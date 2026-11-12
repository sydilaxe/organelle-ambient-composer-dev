"""Offline checks of the patch in Pure Data. Exit code 1 on any failure.  python3 ci_check.py"""
import re
import sys
import numpy as np
from harness import run, errors, rms_db, SR, build_tmp
from data import FLAVOURS

fails = []


def check(cond, msg):
    print(("ok    " if cond else "FAIL  ") + msg, flush=True)
    if not cond:
        fails.append(msg)


def f0(seg, lo=40, hi=2000):
    seg = seg * np.hanning(len(seg))
    N = 1 << 18
    S = np.abs(np.fft.rfft(seg, N))
    hps = S.copy()
    for h in (2, 3):
        dd = S[::h]
        hps[:len(dd)] *= dd
    f = np.fft.rfftfreq(N, 1 / SR)
    m = (f > lo) & (f < hi)
    return f[np.argmax(hps * m)]


# 1. loads and plays with default settings
log, a = run([(50, "ac-setseed 1234")], 60)
check(not errors(log), "loads without Pd errors " + "; ".join(errors(log)[:3]))
check(-30 < rms_db(a) < -12, f"default level {rms_db(a):.1f} dB RMS")
check(np.abs(a).max() < 0.95 and not np.isnan(a).any(), f"no clipping or NaN (peak {np.abs(a).max():.2f})")
lines = [l for l in log.splitlines() if l.startswith("ac-txt")]
check(any(l.startswith("ac-txt1: list COMP 1 of") for l in lines), "screen line 1 shows the form")
check(not any(" symbol" in l for l in lines), "no empty screen fields")

# 2. every start is a different piece; one seed replays the same piece
d = build_tmp()
firsts = []
for i in range(3):
    lg, _ = run([], 2, d=d)
    firsts.append([l for l in lg.splitlines() if l.startswith("ac-setseed")][0])
check(len(set(firsts)) == 3, "three starts give three seeds " + str(firsts))
g = lambda L: [x for x in L.splitlines() if x.startswith(("ac-txt2", "ac-txt3"))][-2:]
l1, _ = run([(50, "ac-setseed 777")], 3)
l2, _ = run([(50, "ac-setseed 777")], 3)
check(g(l1) == g(l2), "a seed replays its piece")
pieces = set()
for s in range(10, 20):
    lg, _ = run([(50, f"ac-setseed {s}")], 1)
    pieces.add(tuple(g(lg)))
check(len(pieces) >= 9, f"10 seeds give {len(pieces)} different pieces")

# 3. each pad synthesis type sounds, at the right pitch where it has one
ev = [(50, "ac-setseed 77"), (300, "ac-chgstop bang"), (300, "ac-secstop bang"), (310, "acmdrone 0"),
      (310, "acmtex 0"), (310, "acmcloud 0"), (310, "acmbell 0"), (310, "acfpad 1"), (310, "acdens 1"), (320, "ac-layers bang"), (330, "ac-rwet 0 10"),
      (330, "ac-motion 0")] + [(340, f"ac-v{k}-flav -1") for k in (1, 2, 3)]
T = 1000
for fl in range(len(FLAVOURS)):
    ev += [(T, f"ac-v0-flav {fl}"), (T, "ac-v0-pitch 57 0 0")]
    T += 6000
log, a = run(ev, T / 1000 + 1)
T = 1000
for fl, name in enumerate(FLAVOURS):
    seg = a[int((T + 3000) * SR / 1000):int((T + 5500) * SR / 1000), 0]
    lvl = rms_db(seg)
    check(-40 < lvl < -18, f"pad type {name}: {lvl:.1f} dB")
    if name in ("vox", "bow"):
        check(abs(f0(seg) / 220 - 1) < 0.01, f"pad type {name} at 220 Hz ({f0(seg):.1f})")
    T += 6000

# 4. a composition runs through its sections and ends in silence
log, a = run([(50, "actime 0.04"), (60, "ac-setseed 2026")], 90)
l1 = [l for l in log.splitlines() if l.startswith("ac-txt1")]
check(any("COMP 1 of" in l for l in l1) and any("FIN" in l for l in l1), "composition reaches FIN")
check(rms_db(a[-10 * SR:]) < -90, "silent after the end")
check(rms_db(a[2 * SR:12 * SR]) > -40, "the composition plays")

# 5. controls: knob pickup, pages, keys
ev = [(50, "ac-setseed 11"), (100, "ac-extnote 1"), (200, "knob4 0.5"), (210, "knob1 0.5"), (400, "knob4 0.8"), (500, "aux 1"), (550, "aux 0"),
      (600, "knob1 0.1"), (800, "aux 1"), (850, "aux 0"), (900, "aux 1"), (950, "aux 0")]
T = 1500
for n in (64, 73, 74, 75, 81, 82, 83):
    ev += [(T, f"notesRaw {n} 100"), (T + 50, f"notesRaw {n} 0")]
    T += 2000
log, _ = run(ev, T / 1000 + 2)
check("ac-txt5: list Colr 50 In 60 auto" in log, "knob pickup scales towards the end (In 60)")
check("ac-txt4: list Mix 9 Verb auto" in log, "page 2 knobs (SPACE)")
check("ac-txt4: list Len 12 min Weird 30" in log, "page 3 (PIECE)")
for t in ("next key E", "chord change", "next section", "drone off", "input reso", "hold - reverb and cloud", "new piece"):
    check(f"ac-toast: list {t}" in log, f"key toast: {t}")

# 6. input processing: every mode makes sound from the input, and ghost onsets ring bells
ALL = ["acmdrone", "acmpad", "acmtex", "acmcloud", "acmbell"]
ev = [(50, "ac-setseed 99")] + [(60, f"{m} 0") for m in ALL] + [(61, "ac-layers bang")]
T = 1000
for mode in range(1, 5):
    ev += [(T, f"acinmode {mode}"), (T, "acinput 0.9"), (T + 1, "ac-inputupd bang")]
    T += 12000
ev += [(T - 12000, "acmbell 1"), (T - 11999, "ac-layers bang")]
log, a = run(ev, T / 1000, inp="tone", prints=("ac-bell",))
T = 1000
for mode, name in enumerate(("reso", "cloud", "tape", "ghost")):
    seg = a[int((T + 4000) * SR / 1000):int((T + 11000) * SR / 1000)]
    if name != "ghost":
        check(rms_db(seg) > -40, f"input {name}: {rms_db(seg):.1f} dB")
    T += 12000
check(log.count("ac-bell:") >= 3, f"ghost mode: input onsets ring bells ({log.count('ac-bell:')})")

# 7. Bloom: matches Conduit's C version (tools/ref/bloom.c) in swell, decay and envelope
import os, subprocess, tempfile
ALL = ["acmdrone", "acmpad", "acmtex", "acmcloud", "acmbell", "acmmotion"]


def imp(c):
    v = c.obj("vline~", 900, 300)
    m = c.msg("1, 0 0 0.0227", 900, 270)
    c.c(c.obj("r h-imp", 900, 240), 0, m, 0)
    c.c(m, 0, v, 0)
    c.c(v, 0, c.obj("throw~ ac-send", 900, 330), 0)


def env(x, sr, w=0.02):
    n = int(w * sr)
    k = len(x) // n
    return np.sqrt((x[:k * n] ** 2).reshape(k, n).mean(1))


def shape(e):
    db = 20 * np.log10(e / e.max() + 1e-12)
    pk = np.argmax(e)
    below = np.where(db[pk:] < -30)[0]
    return pk * 0.02, (below[0] * 0.02 * 2 if len(below) else 99)


here = os.path.dirname(os.path.abspath(__file__))
exe = os.path.join(tempfile.mkdtemp(), "bloom_ir")
subprocess.run(["gcc", "-O2", "-o", exe, os.path.join(here, "ref", "bloom_ir.c"), os.path.join(here, "ref", "bloom.c"),
                "-lm"], check=True)
Tset = 1.5 + 28.5 * 0.32 ** 1.5
for name, vt, typ in (("Bloom 1", 0.3, 0), ("Bloom 2", 0.5, 1), ("Hall", 0.7, None), ("Shimmer", 0.9, None)):
    ev = [(50, "ac-setseed 5"), (60, "ac-secstop bang"), (60, "ac-chgstop bang")] + [(70, f"{m} 0") for m in ALL] + \
         [(71, "acfade 10"), (72, "ac-layers bang"), (80, f"acrvtype {vt}"), (80, "acrvmix 1"), (80, "acrvtime 0.32"),
          (80, "acrvtone 0.5"), (80, "acrvsize 1"), (80, "ac-rvsize 1"), (81, "ac-verbsel bang"), (9000, "h-imp bang")]
    log, a = run(ev, 20, extra=imp)
    seg = a[9 * SR:]
    e = env(seg.mean(1), SR)
    pk, t60 = shape(e)
    corr = np.corrcoef(seg[:3 * SR, 0], seg[:3 * SR, 1])[0, 1]
    check(abs(corr) < 0.3, f"{name}: stereo (L/R correlation {corr:.2f})")
    check(2.5 < t60 < 9, f"{name}: decays (T60 about {t60:.1f} s for Time {Tset:.1f} s)")
    if typ is None:
        continue
    raw = subprocess.run([exe, str(typ), "11", "1", "0.5", str(Tset)], capture_output=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
    ec = env(y.mean(1), 48000)
    cpk, ct60 = shape(ec)
    n = min(len(ec), len(e), 400)
    ecorr = np.corrcoef(20 * np.log10(ec[:n] + 1e-9), 20 * np.log10(e[:n] + 1e-9))[0, 1]
    check(abs(pk - cpk) < 0.08, f"{name}: swell peaks at {pk:.2f} s (C version {cpk:.2f} s)")
    check(abs(t60 / ct60 - 1) < 0.15, f"{name}: T60 {t60:.1f} s (C version {ct60:.1f} s)")
    check(ecorr > 0.8, f"{name}: envelope matches the C version (r = {ecorr:.2f})")

# 8. form: a 5-minute piece runs emerge -> ... climax ... -> dissolve, leaves home and returns, changes tempo
log, a = run([(50, "aclen 0"), (60, "ac-setseed 2718"), (40, "actime 0.15")], 110, prints=("ac-bpm", "ac-mnote"))
log = log[log.rindex("ac-setseed:"):]
roles = []
for l in log.splitlines():
    m = re.match(r"ac-txt1: list COMP \d+ of \d+ (\w+)", l)
    if m and (not roles or roles[-1] != m.group(1)):
        roles.append(m.group(1))
keys = [l.split()[2] for l in log.splitlines() if l.startswith("ac-txt2")]
bpms = {l for l in log.splitlines() if l.startswith("ac-bpm")}
check(roles[:1] == ["emerge"] and roles[-1:] == ["dissolve"] and "climax" in roles, "form: " + " ".join(roles))
check(len(set(keys)) > 1 and keys[-1] == keys[0], f"key plan leaves home and returns ({keys[0]} ... {keys[-1]})")
check(len(bpms) >= 3, f"tempo follows the form ({len(bpms)} tempi)")
check(log.count("ac-mnote:") > 10, f"motion layer plays ({log.count('ac-mnote:')} notes)")
check("FIN" in log, "the piece ends")
# a 30-minute piece plans 12 sections at most and ends
log, a = run([(50, "aclen 1"), (60, "ac-setseed 30"), (40, "actime 0.02")], 80)
n = [int(m.group(1)) for m in re.finditer(r"COMP \d+ of (\d+)", log)]
check(n and 10 <= n[-1] <= 12 and "FIN" in log, f"30-minute piece: {n[-1] if n else '?'} sections, ends")

# 9. Euclidean timing: E(5,8) on 16ths, exactly 5 hits in every 8 steps, on the right steps
def stepcount(c):
    f = c.obj("f", 900, 400)
    c.c(c.obj("r ac-step", 900, 380), 0, f, 0)
    c.c(c.obj("+ 1", 960, 400), 0, f, 1)
    c.c(f, 0, c.items.__len__() - 1, 0)
    c.c(f, 0, c.obj("v hstep", 900, 420), 0)
    e = c.obj("expr hstep", 1000, 450)
    c.c(c.to(c.obj("r ac-mnote", 1000, 400), "t b"), 0, e, 0)
    c.c(e, 0, c.obj("print MN", 1000, 480), 0)


ev = [(50, "ac-setseed 3"), (60, "ac-secstop bang"), (60, "ac-chgstop bang"), (70, "acdens 1"), (70, "acrhythm 1"),
      (70, "acfmotion 1"), (70, "acenergy 1"), (70, "acfade 10"), (71, "ac-layers bang"),
      (80, "acmk 5"), (80, "acmn 8"), (80, "acmdiv 1"), (80, "acmrot 0")]
log, _ = run(ev, 25, extra=stepcount)
st = [int(float(l.split()[1])) for l in log.splitlines() if l.startswith("MN:")]
hits = sorted({x for x in st if x > 40})
pat = {x % 8 for x in hits}
rots = [{(x + r) % 8 for x in range(8) if x * 5 % 8 < 5} for r in range(8)]
windows = [sum(1 for h in hits if w <= h < w + 8) for w in range(hits[0], hits[-1] - 8)] if hits else []
check(len(hits) > 20 and pat in rots and set(windows) == {5},
      f"motion follows E(5,8): {len(hits)} hits, steps mod 8 = {sorted(pat)}, 5 in every 8 steps")

# 10. live notes: Organelle keys play, MPE bend retunes its own voice, breath controls the level
mute = [(60, f"{m} 0") for m in ALL] + [(61, "acfade 10"), (62, "ac-layers bang"), (63, "ac-rwet 0 10")]
ev = [(50, "ac-setseed 9"), (55, "ac-chgstop bang"), (55, "ac-secstop bang")] + mute + [
    (1000, "notesRaw 69 100"), (4000, "notesRaw 69 0"),
    (6000, "ac-livenote 2 57 100"), (9000, "ac-livebend 2 2"), (12000, "ac-livenote 2 57 0"),
    (14000, "ac-livebreath 3 0"), (14000, "ac-livenote 3 60 100"), (15000, "ac-livebreath 3 110"),
    (17000, "ac-livebreath 3 0"), (18000, "ac-livenote 3 60 0")]
log, a = run(ev, 20)
lv = lambda t0, t1: a[int(t0 * SR):int(t1 * SR), 0]
check(rms_db(lv(2, 3.8)) > -50, f"an Organelle key plays a note ({rms_db(lv(2, 3.8)):.1f} dB)")
fa, fb = f0(lv(7, 8.8)), f0(lv(10, 11.8))
check(abs(12 * np.log2(fb / fa) - 2) < 0.15, f"MPE bend +2 semitones ({fa:.1f} -> {fb:.1f} Hz)")
check(rms_db(lv(14.2, 14.9)) < -80 and rms_db(lv(15.5, 16.8)) > -45, "breath 0 is silent, breath plays")
check("breath control" in log, "a breath controller is noticed")

# 11. key modes and listening
ev = [(50, "ac-setseed 21"), (60, "acfollow 1"), (1000, "notesRaw 73 100"), (1100, "notesRaw 73 0"),
      (2000, "aux 1"), (2100, "notesRaw 74 100"), (2200, "notesRaw 74 0"), (2300, "aux 0"),
      (3000, "aux 1"), (3100, "aux 0"), (4000, "ac-extnote 1"), (4100, "notesRaw 73 100"), (4200, "notesRaw 73 0"),
      (5000, "ac-livenote 1 64 100"), (13000, "ac-livenote 1 64 0")]
log, _ = run(ev, 15, prints=("ac-lvon", "ac-fkey"))
L_ = log.splitlines()
check("ac-lvon: 0 73 0.787402" in L_, "standalone: keys play notes")
check("ac-fkey: 74" in L_ and "ac-toast: list next section" in L_, "aux + key: a function")
check("ac-txt4: list Mix 45 Verb auto" in L_, "aux tap: next page")
check("ac-fkey: 73" in L_ and "ac-toast: list chord change" in L_, "with external MIDI the keys are functions")
check("ac-toast: list key from you E" in L_, "a note held 6 s becomes the key")

# 12. audio: pitch tracking and the input class
def probe(c):
    m = c.obj("metro 500", 900, 500)
    c.c(c.obj("loadbang", 900, 480), 0, m, 0)
    e = c.obj("expr acinp; acinclass", 900, 520)
    c.c(m, 0, e, 0)
    p = c.obj("pack f f", 900, 560)
    c.c(e, 1, p, 1)
    c.c(e, 0, p, 0)
    c.c(p, 0, c.obj("print AN", 900, 600), 0)


for inp, want, cls in (("sine", 57, "pitched"), ("saw", 52, "pitched"), ("clicks", None, "plucked"),
                       ("noise", None, "texture")):
    log, _ = run([(50, "ac-setseed 4"), (60, "acinput 0.7"), (61, "ac-inputupd bang")], 12, inp=inp, extra=probe)
    rows = [[float(x) for x in l.split()[1:]] for l in log.splitlines() if l.startswith("AN:")]
    ps = [r[0] for r in rows[8:] if r[0] > 0]
    got = ["quiet", "pitched", "plucked", "texture"][int(rows[-1][1])]
    check(got == cls, f"input {inp}: class {got}")
    if want:
        check(ps and abs(np.median(ps) - want) < 0.15, f"input {inp}: pitch {np.median(ps) if ps else -1:.2f} (want {want})")

# 13. tuned bands ring the chord; memories record and come back
log, a = run([(50, "ac-setseed 4"), (55, "ac-chgstop bang")] + mute +
             [(70, "acinmode 5"), (70, "acinput 1"), (71, "ac-inputupd bang")], 10, inp="noise",
             prints=tuple(f"ac-band{k}" for k in range(4)))
seg = a[5 * SR:9 * SR, 0]
S = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
fr = np.fft.rfftfreq(len(seg), 1 / SR)
bands = [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-band")][-4:]
peaks = [20 * np.log10(S[(fr > b * 0.98) & (fr < b * 1.02)].mean() / np.median(S)) for b in bands]
check(rms_db(seg) > -40 and sum(p > 10 for p in peaks) >= 2 and np.mean(peaks) > 12, f"bands: noise rings the chord tones {np.round(peaks, 1)} dB")
log, a = run([(50, "ac-setseed 4"), (55, "ac-chgstop bang"), (55, "ac-secstop bang")] + mute +
             [(70, "acinput 0.01"), (71, "ac-inputupd bang"), (500, "ac-memrec bang"), (9000, "ac-memplay 0 1"),
              (9000, "ac-g-mem 0.9 200")], 20, inp="sine")
check(rms_db(a[12 * SR:18 * SR]) > -45 and rms_db(a[6 * SR:int(8.5 * SR)]) < -55, "a memory records and plays back")

# 14. breath holds a section, then the form goes on
ev = [(40, "actime 0.02"), (50, "ac-setseed 12"), (55, "aclen 0")] + [(t, "ac-livebreath 1 90") for t in range(300, 16000, 200)]
log, _ = run(ev, 30)
check("ac-toast: list holding - you are playing" in log and "FIN" in log, "breath holds sections; the piece still ends")

# 15. MIDI clock out (24 a beat, Start), notes out, following an external clock
log, _ = run([(50, "ac-setseed 7"), (60, "ac-secstop bang")], 10, prints=("ac-midibyte", "ac-bpm"))
by = [l for l in log.splitlines() if l.startswith("ac-midibyte")]
bpm = [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-bpm")][-1]
want = 24 * bpm / 60 * 9.9
check("ac-midibyte: 250" in by and abs(by.count("ac-midibyte: 248") - want) < 4,
      f"clock out: Start and {by.count('ac-midibyte: 248')} ticks (about {want:.0f} at {bpm:.1f} BPM)")
log, _ = run([(40, "acmout 2"), (50, "ac-setseed 7")], 8, prints=("ac-noteout",))
check(log.count("ac-noteout:") >= 5, "clock + notes: the chord and the drone go out as notes")
ev = [(40, "acsync 1"), (50, "ac-setseed 7"), (100, "ac-rtin 250")] + \
     [(int(200 + i * 20.833), "ac-rtin 248") for i in range(24 * 16)]
log, _ = run(ev, 9, prints=("ac-step",))
check(log.count("ac-step: bang") == 64, f"follows an external clock (16 beats -> {log.count('ac-step: bang')} steps)")

# 16. SETUP and settings survive a restart
d = build_tmp()
run([(100, "knob2 0.5"), (200, "knob2 0.9"), (400, "aux 1"), (1600, "aux 0"), (1700, "knob1 0.0"), (1800, "aux 1"),
     (3000, "aux 0")], 8, d=d)
log, _ = run([(500, "aux 1"), (1700, "aux 0")], 3, d=d, prints=("ac-sett1",))
check("ac-sett1: 1 MIDI out off" in log and "ac-txt4: list Dens 50 Tide 89" in log,
      "settings (a knob, MIDI out) are saved and loaded")

# 17. the OLED score draws every region, and SETUP shows its pages
def snap(c):
    c.c(c.obj("r h-snap", 900, 700), 0, c.obj("print SNAP", 900, 730), 0)


log, _ = run([(50, "ac-setseed 2718"), (3000, "knob3 0.4"), (3100, "knob3 0.6"), (8000, "aux 1"), (9300, "aux 0"),
              (9500, "aux 1"), (9600, "aux 0")], 10, prints=("oscOut", "ac-sett0"))
osc = [l for l in log.splitlines() if l.startswith("oscOut")]
check(sum("gFlip" in l for l in osc) >= 50, "the OLED flips about 10 times a second")
for what, pat in (("form strip", "gFillArea 3 0 0 128 8 0"), ("ladder", "gFillArea 3 0 20 60 33 0"),
                  ("meters", "gFillArea 3 62 20 33 33 0"), ("rhythm", "gFillArea 3 96 20 32 33 0"),
                  ("tempo", "bpm"), ("knob page", "page SHAPE")):
    check(any(pat in l for l in osc), f"OLED draws the {what}")
check("ac-sett0: list SETUP 2 of 3 - hold aux" in log, "SETUP opens with aux held, aux tap turns its page")

# 18. the wider sound world: drone designs, the sub, electric textures, character, the vocoder, variety
from data import DRONES, TEXTURES, CHARACTERS, FLAVOURS
for dt, name in enumerate(DRONES):
    ev = [(50, "ac-setseed 77"), (55, "ac-secstop bang")] + [(60, f"{m} 0") for m in ALL] + \
         [(61, "acmdrone 1"), (61, "acfdrone 1"), (61, f"acdcur {dt}"), (61, "acfade 10"), (62, "ac-layers bang"),
          (63, "ac-rwet 0 10"), (64, "ac-g-sub 0 10")]
    log, a = run(ev, 8)
    check(-45 < rms_db(a[4 * SR:8 * SR, 0]) < -20, f"drone {name}: {rms_db(a[4 * SR:8 * SR, 0]):.1f} dB")
ev = [(50, "ac-setseed 77"), (55, "ac-secstop bang"), (56, "ac-chgstop bang")] + [(60, f"{m} 0") for m in ALL] + \
     [(61, "acmdrone 1"), (61, "acfade 10"), (62, "ac-layers bang"), (63, "ac-g-drone 0 10"), (63, "ac-g-drone1 0 10"),
      (63, "ac-g-drone2 0 10"), (63, "ac-g-drone3 0 10"), (63, "ac-rwet 0 10"),
      (64, "acsubm 0"), (65, "ac-subp 41.2 0")]
log, a = run(ev, 8)
check(abs(f0(a[4 * SR:8 * SR, 0], lo=25, hi=200) - 41.2) < 1, f"sub alone at 41.2 Hz ({f0(a[4 * SR:8 * SR, 0], lo=25, hi=200):.1f})")
for tx in range(4, len(TEXTURES)):
    ev = [(50, "ac-setseed 77"), (55, "ac-secstop bang")] + [(60, f"{m} 0") for m in ALL] + \
         [(61, "acmtex 1"), (61, "acftex 1"), (61, "acdens 1"), (61, "acenergy 1"), (61, f"actex1 {tx}"),
          (61, f"actex2 {tx}"), (61, "acfade 10"), (62, "ac-layers bang")]
    log, a = run(ev, 12)
    check(rms_db(a[3 * SR:12 * SR]) > -50, f"texture {TEXTURES[tx]}: {rms_db(a[3 * SR:12 * SR]):.1f} dB")
cents = []
for ch in range(len(CHARACTERS)):
    ev = [(50, "ac-setseed 77"), (300, "ac-chgstop bang"), (300, "ac-secstop bang")] + [(310, f"{m} 0") for m in ALL] + \
         [(310, "acmpad 1"), (310, "acfpad 1"), (310, "acdens 1"), (320, "ac-layers bang"), (330, "ac-rwet 0 10"),
          (330, "ac-motion 0")] + [(340, f"ac-v{k}-flav -1") for k in (1, 2, 3)] + \
         [(400, f"acchar {ch}"), (400, "acchamt 0.8"), (401, "ac-layers bang"), (1000, "ac-v0-flav 0"),
          (1000, "ac-v0-pitch 57 0 0")]
    log, a = run(ev, 6)
    seg = a[3 * SR:6 * SR]
    S = np.abs(np.fft.rfft(seg[:, 0] * np.hanning(len(seg))))
    fr = np.fft.rfftfreq(len(seg), 1 / SR)
    cents.append(((S * fr).sum() / S.sum(), np.corrcoef(seg[:, 0], seg[:, 1])[0, 1], rms_db(seg)))
check(all(c[2] > -45 for c in cents), "every character keeps the pads audible")
check(cents[1][1] < 0.9, f"chorus widens the pads (L/R {cents[1][1]:.2f})")
check(min(abs(c[0] - cents[0][0]) for c in cents[2:]) > 50, "tape, ring and crush change the colour " +
      str([int(c[0]) for c in cents]))


def envl(x, w=0.05):
    n = int(w * SR)
    k = len(x) // n
    return np.sqrt((x[:k * n] ** 2).reshape(k, n).mean(1))


ev = [(50, "ac-setseed 31"), (55, "ac-secstop bang")] + [(60, f"{m} 0") for m in ALL] + \
     [(62, "acfade 10"), (63, "ac-layers bang"), (64, "ac-rwet 0 10"), (70, "acinmode 6"), (70, "acinput 1"),
      (71, "ac-inputupd bang")]
log, a = run(ev, 14, inp="tone", prints=("ac-voccar0", "ac-voccar1", "ac-voccar2", "ac-voccar3"))
out = a[4 * SR:14 * SR, 0]
t = np.arange(len(out)) / SR
r = np.corrcoef(envl(out), envl(np.maximum(0, 1 - ((t + 4) % 1.5) / 0.9)))[0, 1]
S = np.abs(np.fft.rfft(out * np.hanning(len(out))))
fr = np.fft.rfftfreq(len(out), 1 / SR)
car = [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-voccar")][-4:]
on = np.mean([S[(fr > c0 * 0.99) & (fr < c0 * 1.01)].max() for c0 in car]) / np.median(S)
check(r > 0.8 and 20 * np.log10(on) > 30 and rms_db(out) > -40,
      f"vocode: the input's envelope (r = {r:.2f}) on the chord's pitches ({20 * np.log10(on):.0f} dB)")

def probe2(c):
    d = c.obj("delay 50", 900, 520)
    c.c(c.obj("r ac-section", 900, 500), 0, d, 0)
    e = c.obj("expr acpal1; acpal2; acpal3", 900, 540)
    c.c(d, 0, e, 0)
    p = c.obj("pack f f f", 900, 560)
    for i in (2, 1, 0):
        c.c(e, i, p, i)
    c.c(p, 0, c.obj("print PAL", 900, 580), 0)


ev = [(100 + i * 300, f"ac-setseed {s * 101}") for i, s in enumerate(range(1, 11))]
log, _ = run(ev, 4, extra=probe2)
pals = {tuple(sorted(l.split()[1:])) for l in log.splitlines() if l.startswith("PAL")}
check(len(pals) >= 8, f"10 consecutive seeds give {len(pals)} different pad palettes")

# 19. stereo: wide above the bass, moving, mono-safe; SETUP Output mono gives mono
from scipy.signal import butter, sosfilt
hp = butter(4, 200, 'hp', fs=SR, output='sos')
for seed, extra, name in ((2718, [], "wide"), (2718, [(40, "acmono 1")], "mono")):
    log, a = run([(50, "aclen 0"), (60, f"ac-setseed {seed}")] + extra, 160)
    seg = a[110 * SR:160 * SR]
    M, S_ = (seg[:, 0] + seg[:, 1]) / 2, (seg[:, 0] - seg[:, 1]) / 2
    sm = 10 * np.log10((S_ ** 2).mean() / (M ** 2).mean() + 1e-12)
    loss = 10 * np.log10((M ** 2).mean() / (((seg[:, 0] ** 2).mean() + (seg[:, 1] ** 2).mean()) / 2) + 1e-12)
    ah = sosfilt(hp, a, axis=0)
    bal = [10 * np.log10((ah[i:i + SR, 0] ** 2).mean() / (ah[i:i + SR, 1] ** 2).mean() + 1e-12)
           for i in range(20 * SR, len(a) - SR, SR)]
    if name == "wide":
        check(-11 < sm < -3, f"stereo: side/mid {sm:.1f} dB (wide, not phasey)")
        check(np.std(bal) > 1.2, f"stereo: the image moves ({np.std(bal):.1f} dB balance swings)")
        check(loss > -2.5, f"stereo: mono-compatible (mono sum {loss:.1f} dB)")
    else:
        check(np.abs(seg[:, 0] - seg[:, 1]).max() < 1e-4, "SETUP Output mono: both channels the same")

print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
