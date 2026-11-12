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
check(any(l.startswith("screenLine1: list DRIFT") for l in lines), "screen line 1 shows the state")
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
      (310, "acmtex 0"), (310, "acmcloud 0"), (310, "acmbell 0"), (320, "ac-layers bang"), (330, "ac-rwet 0 10"),
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
log, a = run([(50, "actime 0.04"), (60, "ac-setseed 2026"), (100, "notesRaw 72 100"), (150, "notesRaw 72 0")], 90)
l1 = [l for l in log.splitlines() if l.startswith("screenLine1")]
check(any("COMP 1 of" in l for l in l1) and any("FIN" in l for l in l1), "composition reaches FIN")
check(rms_db(a[-10 * SR:]) < -90, "silent after the end")
check(rms_db(a[2 * SR:12 * SR]) > -40, "the composition plays")

# 5. controls: knob pickup, pages, keys
ev = [(50, "ac-setseed 11"), (200, "knob4 0.5"), (210, "knob2 0.5"), (400, "knob4 0.8"), (500, "aux 1"), (550, "aux 0"),
      (600, "knob2 0.1"), (800, "aux 1"), (850, "aux 0")]
T = 1500
for n in (64, 73, 74, 75, 81, 82, 83):
    ev += [(T, f"notesRaw {n} 100"), (T + 50, f"notesRaw {n} 0")]
    T += 2000
log, _ = run(ev, T / 1000 + 2)
check("screenLine5: list Colr 50 In 60 reso" in log, "knob pickup scales towards the end (In 60)")
check("ac-toast: list page SPACE" in log and "screenLine4: list Space 60 Weird 6" in log, "page 2 knobs")
for t in ("next key E", "chord change", "next section", "drone off", "input cloud", "cloud frozen", "new piece"):
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

print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
