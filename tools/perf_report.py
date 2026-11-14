"""Read Amble's performance logs and profiles (the patch's logs/ folder) and say where the CPU goes.

    python3 perf_report.py PATH...      files, or folders holding perf-*.txt / profile-*.txt (default: ../patches/Amble/logs)

What it tells you:
  - the load over the session: average, typical (95 %), the worst 100 ms; the time the CPU guard was lightening it
  - the spikes: the worst moments and what had just changed (a page drawn, a section, a load, a morph)
  - what each thing costs while playing: a fit of the load against what was on (layers, pad types, engines, effects),
    so a cost shows even when it never causes a spike
  - the profile: each part alone, above the baseline
  - so: what is cheap enough to make richer, and what is worth optimising

The fit needs variety: a log of one piece left alone can tell the pads' cost only from the moments they were off.
Ten minutes moving through sections, pages and settings fits well. Costs are in % of the CPU (the guard's 100 % is
the Organelle's whole budget; it steps in at 78 %)."""
import glob
import os
import sys

import numpy as np

from data import FLAVOURS, DRONES, STRIKES, VERBS
from gen_log import FIELDS

GUARD = 78
LAYERS = ("drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud")


def read_lines(path):
    """a Pd [text] file: lines ending in ';', words separated by spaces (escaped ones kept)."""
    out = []
    for raw in open(path).read().replace("\\;", "").split(";"):
        w = raw.split()
        if w:
            out.append(w)
    return out


def read_perf(paths):
    rows, names = [], [n for n, _ in FIELDS]
    for p in sorted(paths):
        lines = read_lines(p)
        if not lines:
            continue
        head, body = lines[0], lines[1:]
        if head[:3] != ["t", "load", "peak"]:
            print(f"  (skipped {os.path.basename(p)}: not a perf log)")
            continue
        for w in body:
            r = dict(zip(head, (float(x) for x in w)))
            r["file"] = os.path.basename(p)
            rows.append(r)
        if head != names:
            print(f"  ({os.path.basename(p)}: written by another version; fields matched by name)")
    return rows


def read_profile(paths):
    out = {}
    for p in sorted(paths):
        for w in read_lines(p)[1:]:
            if len(w) >= 3:
                out.setdefault(w[0], []).append((float(w[1]), float(w[2])))
    # several profiles: the average of each part
    return {k: (np.mean([a for a, _ in v]), max(b for _, b in v)) for k, v in out.items()}


def name(table, i):
    i = int(i)
    return table[i] if 0 <= i < len(table) else str(i)


def describe(r):
    """a line's state in words"""
    on = [n for i, n in enumerate(LAYERS) if int(r.get("layers", 0)) >> i & 1]
    pads = sorted({name(FLAVOURS, r.get(f"pad{k}", 0)) for k in range(4)})
    bits = [" ".join(on) or "silent"]
    if "pad" in on:
        bits.append("pads " + "/".join(pads))
    if "drone" in on:
        bits.append("drone " + name(DRONES, r.get("drone", 0)))
    if "bell" in on:
        bits.append("bells " + name(STRIKES, r.get("bells", 0)))
    if "motion" in on:
        bits.append("motion " + name(STRIKES, r.get("motion", 0)))
    bits.append(name(VERBS, r.get("verb", 0)))
    for f in ("journey", "sink", "blur", "swell", "pump", "duck", "spark", "input", "held"):
        if r.get(f, 0):
            bits.append(f"{f} {int(r[f])}")
    if r.get("setup", 0) >= 100:
        bits.append(f"SETUP {int(r['setup']) - 100 + 1} open")
    if r.get("morph", 0):
        bits.append("morphing")
    return ", ".join(bits)


def changes(prev, r):
    if prev is None or prev["file"] != r["file"]:
        return "start of a log"
    skip = {"t", "load", "peak", "file"}
    d = [k for k in r if k not in skip and prev.get(k) != r.get(k)]
    return ", ".join(f"{k} {prev.get(k, 0):g}->{r[k]:g}" for k in d) or "nothing logged changed"


def features(rows):
    """what was on in each line, as columns for the fit"""
    cols = {}

    def col(n, f):
        cols[n] = np.array([f(r) for r in rows], float)
    for i, n in enumerate(LAYERS):
        if n in ("pad", "bell", "motion", "drone"):
            continue            # split by type below
        col(f"layer {n}", lambda r, i=i: int(r["layers"]) >> i & 1)
    padon = lambda r: int(r["layers"]) >> 2 & 1
    for t, n in enumerate(FLAVOURS):     # a pad type's share of the four voices
        col(f"pad {n}", lambda r, t=t: padon(r) * sum(int(r.get(f"pad{k}", -1)) == t for k in range(4)) / 4)
    for t, n in enumerate(DRONES):
        col(f"drone {n}", lambda r, t=t: (int(r["layers"]) & 1) * (int(r["drone"]) == t))
    for t, n in enumerate(STRIKES):
        col(f"bells {n}", lambda r, t=t: (int(r["layers"]) >> 3 & 1) * (int(r["bells"]) == t))
        col(f"motion {n}", lambda r, t=t: (int(r["layers"]) >> 4 & 1) * (int(r["motion"]) == t))
    for t, n in enumerate(VERBS):
        if t:
            col(f"reverb {n}", lambda r, t=t: int(r["verb"]) == t)
    col("journey on", lambda r: int(r["journey"]) >= 1000)
    for f in ("sink", "blur", "swell", "duck", "spark", "input"):
        col(f, lambda r, f=f: r[f] / 100)
    col("pump", lambda r: r["pump"] > 0)
    col("CC out", lambda r: r["ccout"] > 0)
    col("live notes held", lambda r: r["held"])
    col("SETUP open", lambda r: r["setup"] >= 100)
    col("morphing", lambda r: r["morph"] > 0)
    return cols


def fit(rows):
    """least squares of the load on what was on (a little ridge, so rare columns stay small); the columns that never
    varied are left out (their cost is in the constant)"""
    cols = features(rows)
    y = np.array([r["load"] for r in rows], float)
    keep = [n for n, v in cols.items() if v.std() > 1e-6]
    if len(rows) < 12 or not keep:
        return None, {}
    X = np.column_stack([np.ones(len(rows))] + [cols[n] for n in keep])
    lam = np.eye(X.shape[1]) * 0.5
    lam[0, 0] = 0
    beta = np.linalg.solve(X.T @ X + lam, X.T @ y)
    resid = y - X @ beta
    sd = np.sqrt(max(1e-9, resid.var()) * np.diag(np.linalg.pinv(X.T @ X + lam)))
    seen = {n: int((cols[n] > 0).sum()) for n in keep}
    return (beta[0], resid.std()), {n: (beta[i + 1], sd[i + 1], seen[n]) for i, n in enumerate(keep)}


def main(args):
    paths = []
    for a in args or [os.path.join(os.path.dirname(__file__), "..", "patches", "Amble", "logs")]:
        paths += sorted(glob.glob(os.path.join(a, "*.txt"))) if os.path.isdir(a) else [a]
    perf = [p for p in paths if os.path.basename(p).startswith("perf-")]
    prof = [p for p in paths if os.path.basename(p).startswith("profile-")]
    if not perf and not prof:
        print("no perf-*.txt or profile-*.txt found in", " ".join(args) or "the patch's logs/")
        return 1
    rows = read_perf(perf)
    playing = [r for r in rows if r.get("run") == 1]
    print(f"Amble performance report: {len(perf)} log file(s), {len(prof)} profile(s)\n")

    if rows:
        load = np.array([r["load"] for r in rows])
        peak = np.array([r["peak"] for r in rows])
        print("== The session")
        print(f"  {len(rows) * 5 / 60:.1f} min logged ({len(playing) * 5 / 60:.1f} playing)")
        print(f"  load: average {load.mean():.0f} %, typical high (95 %) {np.percentile(load, 95):.0f} %, "
              f"worst 5 s {load.max():.0f} %")
        print(f"  worst 100 ms: {peak.max():.0f} %; 100 ms windows over {GUARD} %: in "
              f"{int((peak > GUARD).sum())} of {len(rows)} lines")
        g = sum(1 for r in rows if r.get("guard", 0) > 0)
        print(f"  CPU guard lightening the piece: {g * 5 / 60:.1f} min" + (" (never)" if not g else ""))
        print(f"  headroom (the guard's {GUARD} % less the typical high): {GUARD - np.percentile(load, 95):.0f} points\n")

        print("== The spikes (the worst 100 ms windows) and what had just changed")
        order = sorted(range(len(rows)), key=lambda i: -rows[i]["peak"])[:8]
        for i in order:
            r = rows[i]
            print(f"  {r['file']} t={r['t']:.0f}s  peak {r['peak']:.0f} % (average {r['load']:.0f} %)")
            print(f"      changed: {changes(rows[i - 1] if i else None, r)}")
            print(f"      state:   {describe(r)}")
        bursty = [r for r in rows if r["peak"] - r["load"] > 25]
        if bursty:
            print(f"  {len(bursty)} line(s) peak more than 25 points over their average: a short burst of control "
                  "work (a chord change, a page drawn, a save) rather than sound; spreading it over more ticks helps")
        print()

        base, cost = fit(playing)
        print("== What each thing costs while playing (fit of the load on what was on)")
        if base is None:
            print("  not enough lines yet (a minute or more of playing, with things changing)\n")
        else:
            print(f"  everything always on: {base[0]:.1f} %; the fit misses by {base[1]:.1f} points on a typical line")
            print(f"  {'':24s} {'cost':>6s} {'+-':>5s}  lines on")
            for n, (b, s, k) in sorted(cost.items(), key=lambda kv: -kv[1][0]):
                flag = "" if abs(b) > 2 * s else "  (unsure)"
                print(f"  {n:24s} {b:6.1f} {s:5.1f}  {k:5d}{flag}")
            print("  (a level, 0-1, like sink or input: the cost at full; a pad type: with all four voices on it)\n")

    pr = read_profile(prof)
    if pr:
        b0 = pr.get("baseline", (0, 0))[0]
        print(f"== The profile: each part alone, above the baseline ({b0:.1f} %)")
        ranked = sorted(((k, v[0] - b0, v[1]) for k, v in pr.items() if k != "baseline"), key=lambda x: -x[1])
        for k, c, p in ranked:
            print(f"  {k:20s} {c:6.1f} %   worst 100 ms {p:.0f} %")
        groups = {}
        for k, c, _ in ranked:
            groups.setdefault(k.split("-")[0], []).append(c)
        print("  by kind (dearest member):", ", ".join(f"{g} {max(v):.1f}" for g, v in
                                                     sorted(groups.items(), key=lambda kv: -max(kv[1]))))
        print()

        print("== So")
        cheap = [k for k, c, _ in ranked if c < 1.5]
        dear = [k for k, c, _ in ranked[:6]]
        print("  worth optimising first (dearest alone):", ", ".join(dear))
        print("  cheap enough to make richer (under 1.5 %):", ", ".join(cheap) or "none")
    if rows and not pr:
        print("== So\n  (run a profile too, SETUP 4 knob 3 fully up, for each part's cost alone)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
