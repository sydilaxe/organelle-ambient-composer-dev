"""Render demo MP3s into ../demos (needs ffmpeg):  python3 render_demo.py"""
import os, subprocess, tempfile
import numpy as np
from harness import run, SR

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demos")
def breath_phrases():
    """a played part, as a DM48X would send it: notes on their own MPE channels, breath swells, a bend"""
    ev, t = [], 6000
    notes = [64, 67, 71, 69, 64, 62, 67, 64]
    for i, n in enumerate(notes):
        ch = 2 + i % 4
        ev += [(t, f"ac-livebreath {ch} 0"), (t + 5, f"ac-livenote {ch} {n} 90")]
        for k in range(40):                         # 4 s swell up and down
            ev.append((t + 10 + k * 100, f"ac-livebreath {ch} {int(110 * np.sin(np.pi * k / 40) ** 1.5)}"))
        if i % 3 == 2:
            ev += [(t + 2500, f"ac-livebend {ch} 0.5"), (t + 3500, f"ac-livebend {ch} 0")]
        ev += [(t + 4100, f"ac-livenote {ch} {n} 0")]
        t += 5200 if i % 2 else 3800
    return ev


DEMOS = [
    # a whole 5-minute composition (Len at 0), rendered to its end
    ("amble_composition_seed_2718", [(50, "aclen 0"), (60, "ac-setseed 2718")], 345, None),
    # drifting backing track, the input (a plucked test tone) ringing the chord resonators
    ("amble_drift_resonate_input_seed_808", [(40, "acmode 0"), (50, "ac-setseed 808"), (60, "acinput 0.6"), (61, "ac-inputupd bang"),
                                       (60, "acdens 0.7"), (61, "ac-layers bang")], 150, "tone"),
    # an electric piece: digi and saw pads, an analog drone, a sub bass line, chorus, buzz and radio, Hall
    ("amble_electric_composition_seed_3612", [(50, "aclen 0"), (60, "ac-setseed 3612")], 345, None),
    # bell-like and electric: tine, bar partials and FM pads, the "space" atmosphere, an analog drone; stereo scenes
    ("amble_bells_atmosphere_composition_seed_8464", [(50, "aclen 0"), (60, "ac-setseed 8464")], 345, None),
    # the vocoder: a (synthetic) singer speaking through a synth choir on the chords
    ("amble_vocoder_voice_input_seed_4139", [(40, "acmode 0"), (50, "ac-setseed 4139"), (60, "acinmode 6"),
                                             (60, "acinput 0.8"), (61, "ac-inputupd bang")], 75, "voice"),
    # live: a breath-controlled MPE part (notes, swells, bends) and a plucked tone on the audio input (Auto mode)
    ("amble_live_breath_mpe_and_input_seed_77", [(40, "acmode 0"), (50, "ac-setseed 77"), (60, "acinput 0.5"),
                                                  (61, "ac-inputupd bang")] + breath_phrases(), 70, "tone"),
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
        print(p, [l for l in log.splitlines() if l.startswith("ac-txt2")][-1:])
