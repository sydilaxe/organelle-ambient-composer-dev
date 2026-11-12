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
lines = [l for l in log.splitlines() if l.startswith("screenLine")]
check(any(l.startswith("screenLine1: list COMP 1 of") for l in lines), "screen line 1 shows the form")
check(not any(" symbol" in l for l in lines), "no empty screen fields")

# 2. every start is a different piece; one seed replays the same piece
d = build_tmp()
firsts = []
for i in range(3):
    lg, _ = run([], 2, d=d)
    firsts.append([l for l in lg.splitlines() if l.startswith("ac-setseed")][0])
check(len(set(firsts)) == 3, "three starts give three seeds " + str(firsts))
g = lambda L: [x for x in L.splitlines() if x.startswith(("screenLine2", "screenLine3"))][-2:]
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
l1 = [l for l in log.splitlines() if l.startswith("screenLine1")]
check(any("COMP 1 of" in l for l in l1) and any("FIN" in l for l in l1), "composition reaches FIN")
check(rms_db(a[-10 * SR:]) < -90, "silent after the end")
check(rms_db(a[2 * SR:12 * SR]) > -40, "the composition plays")

# 5. controls: knob pickup, pages, keys
ev = [(50, "ac-setseed 11"), (200, "knob4 0.5"), (210, "knob1 0.5"), (400, "knob4 0.8"), (500, "aux 1"), (550, "aux 0"),
      (600, "knob1 0.1"), (800, "aux 1"), (850, "aux 0"), (900, "aux 1"), (950, "aux 0")]
T = 1500
for n in (64, 73, 74, 75, 81, 82, 83):
    ev += [(T, f"notesRaw {n} 100"), (T + 50, f"notesRaw {n} 0")]
    T += 2000
log, _ = run(ev, T / 1000 + 2)
check("screenLine5: list Colr 50 In 60 reso" in log, "knob pickup scales towards the end (In 60)")
check("ac-toast: list page SPACE" in log and "screenLine4: list Mix 9 Verb auto" in log, "page 2 knobs")
check("ac-toast: list page PIECE" in log, "page 3")
for t in ("next key E", "chord change", "next section", "drone off", "input cloud", "hold - reverb and cloud", "new piece"):
    check(f"ac-toast: list {t}" in log, f"key toast: {t}")

# 6. input processing: every mode makes sound from the input, and ghost onsets ring bells
ALL = ["acmdrone", "acmpad", "acmtex", "acmcloud", "acmbell"]
ev = [(50, "ac-setseed 99")] + [(60, f"{m} 0") for m in ALL] + [(61, "ac-layers bang")]
T = 1000
for mode in range(4):
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
    m = re.match(r"screenLine1: list COMP \d+ of \d+ (\w+)", l)
    if m and (not roles or roles[-1] != m.group(1)):
        roles.append(m.group(1))
keys = [l.split()[2] for l in log.splitlines() if l.startswith("screenLine2")]
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

print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
