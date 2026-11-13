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
for t in ("next key E", "chord change", "next section", "drone off", "input reso", "stopped - A# to start", "new piece"):
    check(f"ac-toast: list {t}" in log, f"key toast: {t}")

# 6. input processing: every mode makes sound from the input, and ghost onsets ring bells
ALL = ["acmdrone", "acmpad", "acmtex", "acmcloud", "acmbell"]
ev = [(50, "ac-setseed 99")] + [(310, f"{m} 0") for m in ALL] + [(311, "ac-layers bang")]
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
    ev = [(50, "ac-setseed 5"), (310, "ac-secstop bang"), (310, "ac-chgstop bang")] + [(320, f"{m} 0") for m in ALL] + \
         [(321, "acfade 10"), (322, "ac-layers bang"), (330, f"acrvtype {vt}"), (330, "acrvmix 1"), (330, "acrvtime 0.32"),
          (330, "acrvtone 0.5"), (330, "acrvsize 1"), (330, "ac-rvsize 1"), (331, "ac-verbsel bang"), (9000, "h-imp bang")]
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


ev = [(50, "ac-setseed 3"), (310, "ac-secstop bang"), (310, "ac-chgstop bang"), (320, "acdens 1"), (320, "acrhythm 1"),
      (320, "acfmotion 1"), (320, "acenergy 1"), (320, "acfade 10"), (321, "ac-layers bang"),
      (330, "acmk 5"), (330, "acmn 8"), (330, "acmdiv 1"), (330, "acmrot 0")]
log, _ = run(ev, 25, extra=stepcount)
st = [int(float(l.split()[1])) for l in log.splitlines() if l.startswith("MN:")]
hits = sorted({x for x in st if x > 40})
pat = {x % 8 for x in hits}
rots = [{(x + r) % 8 for x in range(8) if x * 5 % 8 < 5} for r in range(8)]
windows = [sum(1 for h in hits if w <= h < w + 8) for w in range(hits[0], hits[-1] - 8)] if hits else []
check(len(hits) > 20 and pat in rots and set(windows) == {5},
      f"motion follows E(5,8): {len(hits)} hits, steps mod 8 = {sorted(pat)}, 5 in every 8 steps")

# 10. live notes: Organelle keys play, MPE bend retunes its own voice, breath controls the level
mute = [(310, f"{m} 0") for m in ALL] + [(311, "acfade 10"), (312, "ac-layers bang"), (313, "ac-rwet 0 10")]
ev = [(50, "ac-setseed 9"), (305, "ac-chgstop bang"), (305, "ac-secstop bang"), (320, "ac-lvtype 6")] + mute + [
    (1000, "notesRaw 69 100"), (4000, "notesRaw 69 0"),
    (6000, "ac-livenote 2 57 100"), (9000, "ac-livebend 2 2"), (12000, "ac-livenote 2 57 0"),
    (14000, "ac-livebreath 3 0"), (14000, "ac-livenote 3 60 100"), (15000, "ac-livebreath 3 110"),
    (17000, "ac-livebreath 3 0"), (18000, "ac-livenote 3 60 0")]
log, a = run(ev, 20)
lv = lambda t0, t1: a[int(t0 * SR):int(t1 * SR), 0]
check(rms_db(lv(2, 3.8)) > -50, f"an Organelle key plays a note ({rms_db(lv(2, 3.8)):.1f} dB)")
fa, fb = f0(lv(7, 8.8)), f0(lv(10, 11.8))
st_ = 12 * np.log2(fb / fa)
check(abs((st_ - 2 + 6) % 12 - 6) < 0.15, f"MPE bend +2 semitones ({fa:.1f} -> {fb:.1f} Hz, the detector may jump an octave)")
check(rms_db(lv(14.2, 14.9)) < -80 and rms_db(lv(15.5, 16.8)) > -45, "breath 0 is silent, breath plays")
check("breath control" in log, "a breath controller is noticed")

# 11. key modes and listening
ev = [(50, "ac-setseed 21"), (310, "acfollow 1"), (1000, "notesRaw 73 100"), (1100, "notesRaw 73 0"),
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
    log, _ = run([(50, "ac-setseed 4"), (310, "acinput 0.7"), (311, "ac-inputupd bang")], 12, inp=inp, extra=probe)
    rows = [[float(x) for x in l.split()[1:]] for l in log.splitlines() if l.startswith("AN:")]
    ps = [r[0] for r in rows[8:] if r[0] > 0]
    got = ["quiet", "pitched", "plucked", "texture"][int(rows[-1][1])]
    check(got == cls, f"input {inp}: class {got}")
    if want:
        check(ps and abs(np.median(ps) - want) < 0.15, f"input {inp}: pitch {np.median(ps) if ps else -1:.2f} (want {want})")

# 13. tuned bands ring the chord; memories record and come back
log, a = run([(50, "ac-setseed 4"), (305, "ac-chgstop bang")] + mute +
             [(320, "acinmode 5"), (320, "acinput 1"), (321, "ac-inputupd bang")], 10, inp="noise",
             prints=tuple(f"ac-band{k}" for k in range(4)))
seg = a[5 * SR:9 * SR, 0]
S = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
fr = np.fft.rfftfreq(len(seg), 1 / SR)
bands = [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-band")][-4:]
peaks = [20 * np.log10(S[(fr > b * 0.98) & (fr < b * 1.02)].mean() / np.median(S)) for b in bands]
check(rms_db(seg) > -40 and sum(p > 10 for p in peaks) >= 2 and np.mean(peaks) > 12, f"bands: noise rings the chord tones {np.round(peaks, 1)} dB")
log, a = run([(50, "ac-setseed 4"), (305, "ac-chgstop bang"), (305, "ac-secstop bang")] + mute +
             [(320, "acinput 0.01"), (321, "ac-inputupd bang"), (500, "ac-memrec bang"), (9000, "ac-memplay 0 1"),
              (9000, "ac-g-mem 0.9 200")], 20, inp="sine")
check(rms_db(a[12 * SR:18 * SR]) > -45 and rms_db(a[6 * SR:int(8.5 * SR)]) < -55, "a memory records and plays back")

# 14. breath holds a section, then the form goes on
ev = [(40, "actime 0.02"), (50, "ac-setseed 12"), (305, "aclen 0")] + [(t, "ac-livebreath 1 90") for t in range(300, 16000, 200)]
log, _ = run(ev, 30)
check("ac-toast: list holding - you are playing" in log and "FIN" in log, "breath holds sections; the piece still ends")

# 15. MIDI clock out (24 a beat, Start), notes out, following an external clock
log, _ = run([(50, "ac-setseed 7"), (310, "ac-secstop bang")], 10, prints=("ac-midibyte", "ac-bpm"))
by = [l for l in log.splitlines() if l.startswith("ac-midibyte")]
bpm = [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-bpm")][-1]
want = 24 * bpm / 60 * 9.9
check("ac-midibyte: 250" in by and abs(by.count("ac-midibyte: 248") - want) < 4,
      f"clock out: Start and {by.count('ac-midibyte: 248')} ticks (about {want:.0f} at {bpm:.1f} BPM)")
log, _ = run([(40, "acmout 2"), (50, "ac-setseed 7")], 8, prints=("ac-noteout",))
check(log.count("ac-noteout:") >= 5, "clock + notes: the chord and the drone go out as notes")
ev = [(40, "acsync 1"), (50, "ac-setseed 7"), (100, "ac-rtin 250")] + \
     [(int(200 + i * 20.833), "ac-rtin 248") for i in range(24 * 16)]
log, _ = run(ev, 9, prints=("ac-step", "ac-toast"))
# (steps counted from the external Start: a new piece starts the internal clock at once, before Sync follows)
st = log.split("clock start")[-1].count("ac-step: bang")
check(st == 64, f"follows an external clock (16 beats -> {st} steps)")

# 16. SETUP and settings survive a restart
d = build_tmp()
run([(100, "knob2 0.5"), (200, "knob2 0.9"), (400, "aux 1"), (1600, "aux 0"), (1700, "knob1 0.0"), (1800, "aux 1"),
     (3000, "aux 0")], 8, d=d)
log, _ = run([(500, "aux 1"), (1700, "aux 0")], 3, d=d, prints=("ac-sett1",))
check("ac-sett1: 1 MIDI out off" in log and "ac-txt4: list Dens 50 Tide 89" in log,
      "settings (a knob, MIDI out) are saved and loaded")
d = build_tmp()
log1, _ = run([(100, "knob4 0.5"), (200, "knob4 0.9")], 6, d=d)
log2, _ = run([(500, "knob1 0.5"), (600, "knob1 0.51")], 3, d=d)
in1 = re.findall(r"ac-txt5: list Colr \d+ In (\d+)", log1)
in2 = re.findall(r"ac-txt5: list Colr \d+ In (\d+)", log2)
check(in1 and int(in1[-1]) > 50 and in2 and int(in2[-1]) == 0,
      f"the In knob always starts at 0 (was {in1[-1] if in1 else '?'} before the restart, {in2[-1] if in2 else '?'} after)")

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
check("ac-sett0: list SETUP 2 of 8 - hold aux" in log, "SETUP opens with aux held, aux tap turns its page")

# 18. the wider sound world: drone designs, the sub, electric textures, character, the vocoder, variety
from data import DRONES, TEXTURES, CHARACTERS, FLAVOURS
for dt, name in enumerate(DRONES):
    ev = [(50, "ac-setseed 77"), (305, "ac-secstop bang")] + [(310, f"{m} 0") for m in ALL] + \
         [(311, "acmdrone 1"), (311, "acfdrone 1"), (311, f"acdcur {dt}"), (311, "acfade 10"), (312, "ac-layers bang"),
          (313, "ac-rwet 0 10"), (314, "ac-g-sub 0 10")]
    log, a = run(ev, 8)
    check(-45 < rms_db(a[4 * SR:8 * SR, 0]) < -20, f"drone {name}: {rms_db(a[4 * SR:8 * SR, 0]):.1f} dB")
ev = [(50, "ac-setseed 77"), (305, "ac-secstop bang"), (306, "ac-chgstop bang")] + [(310, f"{m} 0") for m in ALL] + \
     [(311, "acmdrone 1"), (311, "acfade 10"), (312, "ac-layers bang"), (313, "ac-g-drone 0 10"), (313, "ac-g-drone1 0 10"),
      (313, "ac-g-drone2 0 10"), (313, "ac-g-drone3 0 10"), (313, "ac-rwet 0 10"),
      (314, "acsubm 0"), (315, "ac-subp 41.2 0")]
log, a = run(ev, 8)
check(abs(f0(a[4 * SR:8 * SR, 0], lo=25, hi=200) - 41.2) < 1, f"sub alone at 41.2 Hz ({f0(a[4 * SR:8 * SR, 0], lo=25, hi=200):.1f})")
for tx in range(4, len(TEXTURES)):
    ev = [(50, "ac-setseed 77"), (305, "ac-secstop bang")] + [(310, f"{m} 0") for m in ALL] + \
         [(311, "acmtex 1"), (311, "acftex 1"), (311, "acdens 1"), (311, "acenergy 1"), (311, f"actex1 {tx}"),
          (311, f"actex2 {tx}"), (311, "acfade 10"), (312, "ac-layers bang")]
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


ev = [(50, "ac-setseed 31"), (305, "ac-secstop bang")] + [(310, f"{m} 0") for m in ALL] + \
     [(312, "acfade 10"), (313, "ac-layers bang"), (314, "ac-rwet 0 10"), (320, "acinmode 6"), (320, "acinput 1"),
      (321, "ac-inputupd bang")]
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
        check(-11 < sm < -1.5, f"stereo: side/mid {sm:.1f} dB (wide; hard-panned bells can push it up for a moment)")
        check(loss > -2.5, f"stereo: not phasey - mono-compatible (mono sum {loss:.1f} dB)")
    else:
        check(np.abs(seg[:, 0] - seg[:, 1]).max() < 1e-4, "SETUP Output mono: both channels the same")
# the voices move: measured dry - every reverb send at 0 (a reverb is a constant wide wash that hides it)
log, a = run([(50, "aclen 0"), (60, "ac-setseed 2718")] + [(500, f"ac-param {i} 0") for i in range(12, 20)], 160)
ah = sosfilt(hp, a, axis=0)
bal = [10 * np.log10((ah[i:i + SR, 0] ** 2).mean() / (ah[i:i + SR, 1] ** 2).mean() + 1e-12)
       for i in range(20 * SR, len(a) - SR, SR)]
# (dry, renders vary: 1.2-1.8 dB seen; the old 1.2 limit was set on the wet mix, which read about 2.1. The scenes
# moving the pads between sections are checked on their own in section 20.)
check(np.std(bal) > 1.0, f"stereo: the image moves ({np.std(bal):.1f} dB balance swings, dry)")

# 20. atmospheres; pad types in stereo but mono-safe; scenes place the voices; preferred sounds come up more
from data import ATMOS_NAMES
for at, name in enumerate(ATMOS_NAMES):
    ev = [(50, "ac-setseed 77"), (305, "ac-secstop bang")] + [(310, f"{m} 0") for m in ALL] + \
         [(311, "acmtex 1"), (311, "acftex 0"), (311, "acfatm 1"), (311, f"acatmcur {at}"), (311, "acfade 10"),
          (312, "ac-layers bang"), (313, "ac-rwet 0 10"), (314, "ac-change bang")]
    log, a = run(ev, 12)
    seg = a[3 * SR:12 * SR]
    cr = np.corrcoef(seg[:, 0], seg[:, 1])[0, 1]
    check(-40 < rms_db(seg) < -24 and cr < 0.85, f"atmosphere {name}: {rms_db(seg):.1f} dB, L/R {cr:.2f}")
base = [(50, "ac-setseed 77"), (300, "ac-chgstop bang"), (300, "ac-secstop bang")] + [(310, f"{m} 0") for m in ALL] + \
       [(310, "acmpad 1"), (310, "acfpad 1"), (310, "acdens 1"), (320, "ac-layers bang"), (330, "ac-rwet 0 10"),
        (330, "ac-motion 0"), (330, "acchar 0"), (331, "ac-layers bang"), (332, "ac-pandepth 0"),
        (332, "ac-v0-home 0.5 10")] + [(340, f"ac-v{k}-flav -1") for k in (1, 2, 3)]
ev = list(base)
T = 1000
for fl in range(len(FLAVOURS)):
    ev += [(T, f"ac-v0-flav {fl}"), (T, "ac-v0-pitch 57 0 0")]
    T += 5000
log, a = run(ev, T / 1000 + 1)
T, wide, dips = 1000, 0, []
for fl in range(len(FLAVOURS)):
    seg = a[int((T + 2000) * SR / 1000):int((T + 4900) * SR / 1000)]
    M = (seg[:, 0] + seg[:, 1]) / 2
    w = int(0.05 * SR)
    k = len(M) // w
    me = np.sqrt((M[:k * w] ** 2).reshape(k, w).mean(1))
    st = np.sqrt(((seg[:k * w, 0] ** 2 + seg[:k * w, 1] ** 2) / 2).reshape(k, w).mean(1))
    dips.append(20 * np.log10((me / st).min()))
    wide += np.corrcoef(seg[:, 0], seg[:, 1])[0, 1] < 0.9
    T += 5000
check(wide >= 7, f"{wide} of {len(FLAVOURS)} pad types have their own stereo")
check(min(dips) > -8, f"pad types are mono-safe (worst mono dip {min(dips):.1f} dB)")
log, _ = run([(40, "actime 0.1"), (50, "aclen 0"), (60, "ac-setseed 2718")], 40,
             prints=tuple(f"ac-v{k}-home" for k in range(4)))
homes = {tuple(l.split()[1] for l in log.splitlines() if l.startswith(f"ac-v{k}-home")) for k in range(4)}
check(all(len(set(h)) >= 2 for h in homes), "stereo scenes move the pad voices between sections")
ev = [(100 + i * 300, f"ac-setseed {5000 + i * 37}") for i in range(40)]
log, _ = run(ev, 13, extra=probe2)
rows = [l.split()[1:] for l in log.splitlines() if l.startswith("PAL")][1:]
liked = {"fm", "part", "pulsr", "saws", "pwm", "digi", "sync", "tine"}
share = sum(FLAVOURS[int(float(x))] in liked for r in rows for x in r) / max(1, 3 * len(rows))
check(share > 0.75, f"palettes favour the electronic and bell-like types ({share:.0%})")

# 21. tempo ranges (SETUP page 3): each range keeps its pieces inside it; a change applies at once
from data import TEMPOS, ROLE_TEMPO
for r, (name, lo, hi) in enumerate(TEMPOS):
    ev = [(40, f"actrange {r}")] + [(100 + i * 300, f"ac-setseed {900 + i * 53}") for i in range(10)]
    log, _ = run(ev, 4, prints=("ac-bpm",))
    b = [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-bpm")][1:]
    ok = b and min(b) >= lo * min(ROLE_TEMPO) - 0.01 and max(b) <= hi * max(ROLE_TEMPO) + 0.01
    check(ok and max(b) - min(b) > (hi - lo) * 0.25, f"tempo range {name}: {min(b):.0f}-{max(b):.0f} BPM")
log, _ = run([(40, "ac-setseed 7"), (300, "acsetup 1"), (310, "acsetpg 2"), (400, "ac-setknob 3 0.99")], 2,
             prints=("ac-bpm", "ac-sett4"))
b = [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-bpm")]
check(b and b[-1] >= 90 * min(ROLE_TEMPO) and "4 Tempo fast 90-140" in log,
      f"SETUP Tempo fast applies at once ({b[-1] if b else 0:.0f} BPM)")
log, a = run([(40, "actrange 4"), (45, "actime 1"), (50, "aclen 0.03"), (60, "ac-setseed 3612")], 180)
# renders vary (noise sources, timing): normal pieces peak about 0.4-0.65; the unlimited pings reached 0.96
check(np.abs(a).max() < 0.8, f"a fast piece stays clean: the motion pings never spike (peak {np.abs(a).max():.2f})")

# 22. the OLED shows external audio: an input panel (waveform, mode, what Amble hears), the pitch on the ladder;
#     the rhythm column comes back when the input stops
ev = [(40, "actime 0.08"), (50, "ac-setseed 2718"), (311, "acinput 0.6"), (312, "ac-inputupd bang")]
log, _ = run(ev, 8, inp="voice", prints=("oscOut",))
osc = log.splitlines()
check(any("gPrintln 3 97 35 8 1 auto" in l for l in osc) and any("gPrintln 3 97 43 8 1 pitch" in l for l in osc)
      and any("gFillArea 3 8 " in l and l.split()[-2:] == ["1", "1"] and " 42 " in l for l in osc),
      "OLED: an input panel (auto / pitch) and the sung pitch on the ladder")
log, _ = run(ev + [(4000, "acinput 0"), (4001, "ac-inputupd bang")], 12, inp="voice", prints=("oscOut",))
late = [l for l in log.splitlines()]
check(any("bpm" in l for l in late[len(late) // 2:]), "OLED: the rhythm column returns after the input stops")

# 23. MIDI notes for external synths and arpeggiators: the arp chord (close, from the Arp octave, base + 5),
#     the bass (base + 4); Parts = arp chord only sends nothing else; SETUP page 4 sets parts and octave
def held_notes(log):
    held = {}
    for p, v, ch in (l.split()[1:] for l in log.splitlines() if l.startswith("ac-noteout")):
        h = held.setdefault(int(ch), set())
        (h.add(int(p)) if v != "0" else h.discard(int(p)))
    return held
log, _ = run([(40, "acmout 2"), (45, "actime 0.1"), (50, "ac-setseed 7")], 12, prints=("ac-noteout",))
h = held_notes(log)
arp = sorted(h.get(6, []))
check(len(arp) >= 3 and arp[0] >= 48 and arp[-1] < 60 + 12 and arp[-1] - arp[0] < 12
      and {p % 12 for p in arp} <= {p % 12 for p in h.get(1, [])} and len(h.get(5, [])) == 1,
      f"MIDI: arp chord in close position {arp} (chord {sorted(h.get(1, []))}), a bass {sorted(h.get(5, []))}")
log, _ = run([(40, "acmout 2"), (41, "acmparts 2"), (45, "actime 0.1"), (50, "ac-setseed 7")], 12, prints=("ac-noteout",))
chs = {int(l.split()[3]) for l in log.splitlines() if l.startswith("ac-noteout")}
check(chs == {6}, f"MIDI parts = arp chord: only the arp chord channel ({sorted(chs)})")
log, _ = run([(40, "acmout 2"), (50, "ac-setseed 7"), (300, "acsetup 1"), (310, "acsetpg 3"),
              (400, "ac-setknob 0 0.99"), (500, "ac-setknob 1 0.0"), (3000, "acsetup 0")], 6,
             prints=("ac-noteout", "ac-sett1", "ac-sett2"))
arp = sorted(held_notes(log).get(6, []))
check("1 MIDI notes arp\\ only" in log and "2 Arp octave C1" in log and arp
      and 24 <= arp[0] < 36, f"SETUP page 4: MIDI parts and Arp octave (arp chord now {arp})")

# 24. CPU guard: under (simulated) overload the piece gets lighter step by step and comes back; off = never
#     (the level is read from SETUP page 4: "CPU n% lite k")
def lite_at(ev, secs, at):
    ev = ev + [e for t in at for e in ((t, "acsetup 1"), (t + 10, "acsetpg 3"), (t + 20, "ac-oledsetup bang"),
                                           (t + 30, "acsetup 0"))]
    log, _ = run(ev, secs, prints=("ac-sett3",))
    return [int(l.split("lite")[1]) for l in log.splitlines() if l.startswith("ac-sett3") and "lite" in l], log
lv, log = lite_at([(40, "acdens 1"), (50, "ac-setseed 7"), (5000, "acloadtest 0.9"), (24000, "acloadtest 0")], 92,
                  [22000, 90000])
check(len(lv) >= 2 and lv[0] == 3 and lv[-1] == 0 and log.count("ac-toast: list CPU high - lighter") == 3,
      f"CPU guard: 3 steps lighter under overload, all back after it ({lv})")
lv, log = lite_at([(40, "acguard 0"), (50, "ac-setseed 7"), (5000, "acloadtest 0.9")], 15, [14000])
check(lv and lv[-1] == 0 and "CPU high" not in log, "CPU guard off: never sheds")

# 25. Start / Stop (A#), Freeze (aux + F#; standalone aux + F# twice), MIDI Start / Stop when following
log, a = run([(40, "acforce 1"), (50, "ac-setseed 7"), (8000, "notesRaw 82 100"), (8050, "notesRaw 82 0"),
              (16000, "notesRaw 82 100"), (16050, "notesRaw 82 0")], 24)
t1 = sorted({l for l in log.splitlines() if l.startswith("ac-txt1")})
check(rms_db(a[12 * SR:15 * SR, 0]) < -100 and rms_db(a[19 * SR:23 * SR, 0]) > -40
      and "ac-txt1: list STOPPED - A# start" in t1 and "ac-txt1: list COMP 1 of 6 emerge" in t1,
      f"A# stops (silent, STOPPED) and starts again in the same section ({rms_db(a[12 * SR:15 * SR, 0]):.0f} dB "
      f"stopped, {rms_db(a[19 * SR:23 * SR, 0]):.0f} dB playing)")
def toasts(ev, secs=6):
    log, _ = run([(50, "ac-setseed 7")] + ev, secs)
    return [l.split("list ", 1)[-1] for l in log.splitlines() if l.startswith("ac-toast")]
F = [(2100, "notesRaw 78 100"), (2150, "notesRaw 78 0")]
F2 = [(2300, "notesRaw 78 100"), (2350, "notesRaw 78 0")]
cases = [toasts([(40, "acforce 1")] + F), toasts([(40, "acforce 1"), (2000, "aux 1")] + F + [(2500, "aux 0")]),
         toasts([(2000, "aux 1")] + F + [(2500, "aux 0")]), toasts([(2000, "aux 1")] + F + F2 + [(2500, "aux 0")])]
check(cases[0] == ["cloud off"] and cases[1] == ["freeze - reverb and cloud"] and cases[2] == ["cloud off"]
      and cases[3] == ["freeze - reverb and cloud"],
      f"F# = cloud, aux + F# = Freeze; standalone aux + F# once = cloud, twice = Freeze ({cases})")
mt = toasts([(40, "acsync 1"), (2000, "ac-rtin 252"), (4000, "ac-rtin 250")])
check("stopped - A# to start" in mt and "playing again" in mt, "following a clock: MIDI Stop / Start stop and start")

# 26. SETUP Output split: the drone (harmony bed) on the left only; the reverb on both
ALLM = ["acmdrone", "acmpad", "acmtex", "acmcloud", "acmbell", "acmmotion"]
ev = [(40, "acmono 2"), (50, "ac-setseed 7"), (310, "ac-secstop bang")] + \
     [(320, f"{m} {1 if m == 'acmdrone' else 0}") for m in ALLM] + \
     [(321, "acfade 10"), (322, "ac-layers bang"), (323, "ac-stereo bang")] + [(t, "ac-rwet 0 10") for t in range(400, 14000, 500)]
log, a = run(ev, 14)
L, R = rms_db(a[6 * SR:14 * SR, 0]), rms_db(a[6 * SR:14 * SR, 1])
check(L > -35 and R < L - 40, f"Output split: the drone only on the left (L {L:.0f} dB, R {R:.0f} dB, reverb off)")

# 27. the reverb is clearly audible: at the default Mix it sits about 6 dB under the whole output (Bloom and Hall)
def rvprobe(c):
    m = c.obj("metro 500", 1200, 20)
    c.c(c.obj("loadbang", 1200, 0), 0, m, 0)
    c.c(c.to(m, "expr acrvlvl"), 0, c.obj("print RV", 1200, 80), 0)
for vt, name in ((0.3, "Bloom 1"), (0.7, "Hall")):
    log, a = run([(50, "ac-setseed 7"), (1000, f"ac-param 5 {vt}")], 40, extra=rvprobe)
    rv = np.median([float(l.split()[1]) for l in log.splitlines() if l.startswith("RV:")][40:]) - 100
    out = rms_db(a[20 * SR:40 * SR].mean(1))
    check(-10 < rv - out < -2, f"{name} at the default Mix: {rv - out:+.1f} dB against the whole output")

# 28. SENDS pages: each group has its own reverb send (drone dry, pads wet...); saved after the SETUP values
ALLM = ["acmdrone", "acmpad", "acmtex", "acmcloud", "acmbell", "acmmotion"]
def drone_wet(send):
    ev = [(50, "ac-setseed 7"), (310, "ac-secstop bang")] + [(320, f"{m} {1 if m == 'acmdrone' else 0}") for m in ALLM] + \
         [(321, "acfade 10"), (322, "ac-layers bang"), (1000, f"ac-param 12 {send}")]
    log, _ = run(ev, 20, extra=rvprobe)
    return np.median([float(l.split()[1]) for l in log.splitlines() if l.startswith("RV:")][24:]) - 100
dry, full = drone_wet(0), drone_wet(1)
check(dry < -90 and full > -45, f"SENDS: Drone send 0 = dry drone ({dry:.0f} dB wet), full = {full:.0f} dB wet")
import os
d = build_tmp()
run([(100, "aux 1"), (150, "aux 0"), (300, "aux 1"), (350, "aux 0"), (500, "aux 1"), (550, "aux 0"),
     (700, "knob1 0.5"), (800, "knob1 0.0")], 6, d=d)
vals = open(os.path.join(d, "settings.txt")).read().split()
log, _ = run([(100, "aux 1"), (150, "aux 0"), (300, "aux 1"), (350, "aux 0"), (500, "aux 1"), (550, "aux 0"),
              (700, "knob2 0.5"), (750, "knob2 0.52")], 3, d=d)
check(len(vals) == 54 and float(vals[27]) == 0 and "ac-txt4: list Drone 0 Pads" in log,
      "SENDS: a send is saved after the SETUP values and comes back after a restart")

# 29. the patch asks the Organelle OS for a larger audio buffer (pd-opts.txt is appended to Pd's options)
po = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "patches", "Amble", "pd-opts.txt")).read()
check("-audiobuf 25" in po, "pd-opts.txt asks for a 25 ms audio buffer (the OS default is 6 ms)")

# 30. SETUP page 5, SOUNDS: one pad type for all four voices at once (and in every later section); raw = the
#     first demos' types (vox, partials, fold, pulsar) with no character; drone, texture and character by hand
FL = ["ac-v%d-flav" % k for k in range(4)]
def flav_vals(text):
    return [int(float(l.split()[1])) for l in text.splitlines() if l.split(":")[0] in FL]
def vprobe(c):
    m = c.obj("metro 250", 1400, 20)
    c.c(c.obj("loadbang", 1400, 0), 0, m, 0)
    c.c(c.ch(m, "expr acdcur*1000 + actex1*100 + actex2*10 + accheff"), 0, c.obj("print SV", 1400, 80), 0)
sp = lambda v: [(300, "acsetup 1"), (310, "acsetpg 4"), (390, "h-mark bang"), (400, f"ac-setknob 0 {v}"),
               (500, "acsetup 0")]
log, _ = run([(50, "ac-setseed 7")] + sp(0.99) + [(3000, "ac-section bang")], 5, prints=tuple(FL) + ("ac-sett1", "h-mark"))
after = log.split("h-mark")[-1]
check("ac-sett1: 1 Pads tine" in log and len(flav_vals(after)) >= 8 and set(flav_vals(after)) == {10},
      f"SOUNDS Pads tine: all 4 voices at once and in the next section ({flav_vals(after)})")
log, _ = run([(50, "ac-setseed 7")] + sp(0.1) + [(1000 + 400 * i, "ac-section bang") for i in range(6)], 4,
             prints=tuple(FL) + ("ac-g-ch1", "ac-g-ch2", "ac-g-ch3", "ac-g-ch4", "ac-sett1", "h-mark"))
after = log.split("h-mark")[-1]
vs = flav_vals(after)
chs = [float(l.split()[1]) for l in after.splitlines() if l.startswith("ac-g-ch")]
check(len(vs) >= 20 and set(vs) <= {1, 3, 4, 5} and len(set(vs)) >= 3 and chs and max(chs) == 0,
      f"SOUNDS Pads raw: only vox / partials / fold / pulsar ({sorted(set(vs))}), no character")
log, _ = run([(50, "ac-setseed 7"), (300, "acsetup 1"), (310, "acsetpg 4"), (400, "ac-setknob 1 0.99"),
              (450, "ac-setknob 2 0.3"), (500, "ac-setknob 3 0.6"), (550, "acsetup 0"), (2000, "ac-section bang")], 4,
             prints=("ac-sett2", "ac-sett3", "ac-sett4"), extra=vprobe)
sv = [l.split()[1:] for l in log.splitlines() if l.startswith("SV:")]
check("2 Drone fm" in log and "3 Texture wind" in log and "4 Character tape" in log
      and sv[-1] == ["3112"], f"SOUNDS: Drone fm, Texture wind, Character tape applied and kept ({sv[-1]})")

# 31. SETUP page 6, MUSIC (key, scale, chords stay as chosen; the bar pulse) and page 7, MIDI IN (where notes go,
#     what breath does)
import gen_setup as S
def setk(pg, k, label, opts, t=400):
    return [(t - 100, "acsetup 1"), (t - 90, f"acsetpg {pg}"), (t, f"ac-setknob {k} {(opts.index(label) + 0.5) / len(opts)}"),
            (t + 100, "acsetup 0")]
ev = [(40, "acmode 0"), (45, "actime 0.05"), (46, "acweird 1"), (50, "ac-setseed 7")] + setk(5, 0, "D", S.SKEYS) + \
     setk(5, 1, "minpent", S.SSCALES, 700) + setk(5, 2, "quartal", S.SCHORDS, 1000) + [(1200, "h-mark bang"), (6000, "ac-setseed 99")]
log, _ = run(ev, 14, prints=("ac-dronep", "h-mark", "ac-txt2"))
after = log.split("h-mark")[-1]
tonics = {int(float(l.split()[1])) % 12 for l in after.splitlines() if l.startswith("ac-dronep")}
s2 = [l for l in after.splitlines() if l.startswith("ac-txt2")]
check(tonics == {2} and s2 and all("minpent quartal" in l for l in s2[-3:]),
      f"MUSIC: key D, minpent, quartal stay through changes and a new piece (tonics {sorted(tonics)}, {s2[-1:]})")
def pulses(label):
    log, _ = run([(50, "ac-setseed 7"), (60, "acrhythm 1")] + setk(5, 3, label, S.PULSES) +
                 [(1000, "acrole 4"), (1001, "ac-pulseupd bang")], 2,
                 prints=("ac-pulse",))
    return [float(l.split()[1]) for l in log.splitlines() if l.startswith("ac-pulse")][-1]
p0, p2, p3 = pulses("off"), pulses("normal"), pulses("strong")
check(p0 == 0 and p3 > p2, f"MUSIC Pulse: off {p0}, normal {p2:.2f}, strong {p3:.2f}")
def routed(label, notes, prints):
    ev = [(50, "ac-setseed 7")] + setk(6, 0, label, S.ROUTES) + [(800, "h-mark bang")]
    ev += [(1000 + 10 * i, f"ac-livenote 1 {n} 100") for i, n in enumerate(notes)]
    ev += [(2900, "h-mark2 bang")] + [(3000 + 10 * i, f"ac-livenote 1 {n} 0") for i, n in enumerate(notes)]
    log, _ = run(ev, 5, prints=prints + ("h-mark", "h-mark2", "ac-lvon"))
    return log.split("h-mark: bang")[1].split("h-mark2")[0], log.split("h-mark2")[-1]
held, _ = routed("bells", [72], ("ac-bell",))
check("ac-bell: 72 " in held and "ac-lvon" not in held, "MIDI IN Notes to bells: a note strikes a bell, no live voice")
held, _ = routed("chords", [60, 64, 67], tuple(f"ac-v{k}-pitch" for k in range(4)))
ch = [int(float(l.split()[1])) for l in held.splitlines() if "-pitch:" in l and l.split()[2] == "300"][-4:]
check(set(ch) == {60, 64, 67, 72}, f"MIDI IN Notes to chords: the held notes are the pad chord ({ch})")
held, rel = routed("drone", [43], ("ac-dronep",))
dr = [int(float(l.split()[1])) for l in held.splitlines() if l.startswith("ac-dronep")]
back = [int(float(l.split()[1])) for l in rel.splitlines() if l.startswith("ac-dronep")]
check(dr and dr[-1] == 43 and back and back[0] != 43, f"MIDI IN Notes to drone: the drone on your note, home after ({dr}, {back})")
def swell(v):
    ev = [(50, "ac-setseed 7")] + setk(6, 1, "swell", S.BRTOS) + [(t, f"ac-livebreath 1 {v}") for t in range(800, 6000, 200)]
    _, a = run(ev, 6)
    return rms_db(a[4 * SR:6 * SR, 0])
lo, hi = swell(0), swell(127)
check(lo < hi - 40, f"MIDI IN Breath to swell: breath sets the level (no breath {lo:.0f} dB, full {hi:.0f} dB)")

held, rel = routed("cloud", [69], tuple(f"ac-gr{i}" for i in range(4)))
gr = [l for l in held.splitlines() if l.startswith("ac-gr")]
check(gr and any(abs(float(l.split()[1]) - 2 ** (((69 - 37) % 12) / 12)) < 0.001 for l in gr) and
      any(l.startswith("ac-gr") for l in rel.splitlines()), f"MIDI IN Notes to cloud: a note tunes a grain stream ({gr[-1:]})")

# 32. SETUP CC MAP: each CC to its own target (defaults: 1 vibrato, 2 / 7 / 11 breath, 64 hold, 74 voice tone per
#     channel); pressure to breath; a CC remapped to a knob of the piece or the voice type
pr = ("ac-livebreath", "ac-lvvib", "ac-lvtim", "ac-lvoff", "ac-param", "ac-lvtype", "ac-sett3", "h-mark")
ev = [(50, "ac-setseed 7"), (600, "ac-livenote 3 60 100"), (700, "h-mark bang"), (800, "ac-ccin 7 100 1"),
      (850, "ac-pressin 1 90"), (900, "ac-ccin 1 127 1"), (950, "ac-ccin 74 127 3"), (960, "ac-ccin 74 0 5"),
      (1000, "ac-ccin 64 127 1"), (1100, "ac-livenote 3 60 0"), (1500, "h-mark bang"), (2000, "ac-ccin 64 0 1")]
log, _ = run(ev, 3, prints=pr)
mid = log.split("h-mark: bang")[1]
late = log.split("h-mark: bang")[2]
check("ac-livebreath: 1 100" in mid and "ac-livebreath: 1 90" in mid and "ac-lvvib: 1" in mid,
      "CC MAP defaults: CC 7 is breath, pressure is breath, CC 1 is vibrato")
check([l for l in mid.splitlines() if l.startswith("ac-lvtim")] == ["ac-lvtim: 0 1"],
      "CC MAP: CC 74 sets the tone of the note on its own channel only")
check("ac-lvoff" not in mid and "ac-lvoff: 0" in late, "CC MAP: CC 64 holds a released note until it lets go")
sel = lambda cc: (S.CCS.index(cc) + 0.5) / len(S.CCS)
tgt = lambda t: (S.TARGETS.index(t) + 0.5) / len(S.TARGETS)
ev = [(50, "ac-setseed 7"), (300, "acsetup 1"), (310, "acsetpg 7"), (400, f"ac-setknob 0 {sel(71)}"),
      (450, f"ac-setknob 1 {tgt('density')}"), (500, "ac-ccin 71 64 1"), (550, "ac-oledsetup bang"),
      (600, f"ac-setknob 0 {sel(11)}"), (650, f"ac-setknob 1 {tgt('voice type')}"), (700, "acsetup 0"),
      (800, "ac-ccin 11 127 1")]
log, _ = run(ev, 2, prints=pr)
check("ac-param: 0 0.5039" in log and "3 Last CC 71 = 64" in log and "ac-lvtype: 10" in log,
      "CC MAP: CC 71 remapped to density moves the Dens knob; CC 11 remapped to voice type picks the type")

# 33. a seed replays its piece whatever played before it (the clock and event players restart with the piece):
#     the random generator's state, read every second, is the same
def rngprobe(c):
    d = c.obj("delay 3500", 1400, 0)
    c.c(c.obj("loadbang", 1400, -20), 0, d, 0)
    m = c.obj("metro 1000", 1400, 20)
    c.c(d, 0, m, 0)
    c.c(c.to(m, "expr acr1*1e6"), 0, c.obj("print RS", 1400, 80), 0)
def rng_after(first):
    log, _ = run([(10, f"ac-setseed {first}"), (40, "acdens 1"), (3000, "ac-setseed 2718")], 40, extra=rngprobe)
    return [l.split()[1] for l in log.splitlines() if l.startswith("RS:")]
r1, r2 = rng_after(140919), rng_after(137919)
check(len(r1) > 30 and r1 == r2 and len(set(r1)) > 20,
      f"a seed replays its piece after any other piece (random state equal for {sum(x == y for x, y in zip(r1, r2))} "
      f"of {len(r1)} s)")

print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
