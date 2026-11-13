"""Render OLED screenshots of Amble's screens (offline Pd run + oledemu):  python3 shots.py [outdir]"""
import os, sys
from harness import run
import oledemu

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "shots")


def snap(c):
    c.c(c.obj("r h-snap", 900, 700), 0, c.obj("print SNAP", 900, 730), 0)


def main():
    os.makedirs(OUT, exist_ok=True)
    ev = [(40, "actime 0.08"), (50, "ac-setseed 2718"), (60, "acrhythm 0.9"), (60, "acdens 0.8")]
    ev += [(30000, "ac-livenote 2 64 100"), (30000, "ac-livebreath 2 80"), (30500, "ac-livenote 3 71 100")]
    ev += [(t, "ac-livebreath 2 90") for t in range(30100, 34000, 200)]
    ev += [(33500, "h-snap score_playing"), (36000, "ac-livenote 2 64 0"), (36000, "ac-livenote 3 71 0")]
    ev += [(20000, "h-snap score")]
    ev += [(40000, "knob3 0.5"), (40100, "knob3 0.8"), (40500, "h-snap knob_popup")]
    ev += [(44000, "aux 1"), (45300, "h-snap setup"), (45400, "aux 0"), (46000, "aux 1"), (46100, "aux 0"),
           (46500, "h-snap setup_page2"), (46700, "aux 1"), (46800, "aux 0"), (47200, "h-snap setup_page3"),
           (47400, "aux 1"), (47500, "aux 0"), (47900, "h-snap setup_page4"), (48100, "aux 1"), (48200, "aux 0"),
           (48600, "h-snap setup_page5"), (48800, "aux 1"), (48900, "aux 0"),
           (49300, "h-snap setup_page6"), (49500, "aux 1"), (49600, "aux 0"), (50000, "h-snap setup_page7"),
           (50200, "aux 1"), (51500, "aux 0")]
    ev += [(52000, "notesRaw 81 100"), (52050, "notesRaw 81 0"), (52300, "h-snap toast")] if False else []
    ev += [(52000, "ac-toast list input reso"), (52300, "h-snap toast")]
    log, _ = run(ev, 60, prints=("oscOut",), extra=snap)
    saved = oledemu.render(log, OUT)
    # DRIFT, and the end of a piece
    log, _ = run([(40, "actime 0.03"), (45, "acmode 0"), (50, "ac-setseed 808"), (12000, "h-snap drift")], 13,
                 prints=("oscOut",), extra=snap)
    saved += oledemu.render(log, OUT)
    log, _ = run([(40, "actime 0.02"), (50, "aclen 0"), (55, "ac-setseed 5"), (70000, "h-snap fin")], 71,
                 prints=("oscOut",), extra=snap)
    saved += oledemu.render(log, OUT)
    # external audio: the input panel and the sung pitch on the ladder
    log, _ = run([(40, "actime 0.08"), (50, "ac-setseed 2718"), (61, "acinput 0.6"), (62, "ac-inputupd bang"),
                  (9000, "h-snap input")], 10, inp="voice", prints=("oscOut",), extra=snap)
    saved += oledemu.render(log, OUT)
    print("\n".join(saved))


if __name__ == "__main__":
    main()
