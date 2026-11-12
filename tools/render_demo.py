"""Render demo MP3s into ../demos (needs ffmpeg):  python3 render_demo.py"""
import os, subprocess, tempfile
import numpy as np
from harness import run, SR

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demos")
DEMOS = [
    # a whole 5-minute composition (Len at 0), rendered to its end
    ("amble_composition_seed_2718", [(50, "aclen 0"), (60, "ac-setseed 2718")], 345, None),
    # drifting backing track, the input (a plucked test tone) ringing the chord resonators
    ("amble_drift_resonate_input_seed_808", [(40, "acmode 0"), (50, "ac-setseed 808"), (60, "acinput 0.6"), (61, "ac-inputupd bang"),
                                       (60, "acdens 0.7"), (61, "ac-layers bang")], 150, "tone"),
]


def write_mp3(a, path):
    pcm = (np.clip(a, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-b:a", "160k", path], input=pcm, check=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, ev, secs, inp in DEMOS:
        log, a = run(ev, secs, inp=inp)
        p = os.path.join(OUT, name + ".mp3")
        write_mp3(a, p)
        print(p, [l for l in log.splitlines() if l.startswith("screenLine2")][-1:])
