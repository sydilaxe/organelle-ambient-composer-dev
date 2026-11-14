"""Run the patch offline in Pd (pd -batch) with timed events, a test input, and a recording.

run(events, seconds, inp=None) -> (log, stereo float array)
events: list of (time_ms, "receiver args"). The patch runs in a temporary copy, so seed.txt in the
repository is never touched."""
import os
import shutil
import subprocess
import sys
import tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pdlib import Canvas

PRINTS = ["ac-txt1", "ac-txt2", "ac-txt3", "ac-txt4", "ac-txt5", "led", "ac-toast",
          "ac-setseed", "ac-section", "ac-change", "ac-fin"]
SR = 44100


def build_tmp():
    import gen
    d = tempfile.mkdtemp(prefix="acpd-")
    gen.build(d)
    return d


def run(events, seconds, inp=None, prints=(), d=None, keep=False, extra=None, autostart=True):
    """inp: None (silence), 'tone' (plucked tones), 'noise' (soft noise bursts). autostart: the start-up piece
    plays at once (as if Start were pressed); False = it waits, ready, as on the Organelle"""
    own = d is None
    if own:
        d = build_tmp()
    ev = sorted(([(0, "acready 0")] if autostart else []) + list(events), key=lambda e: e[0])
    lines, prev = [], 0
    for t, s in ev:
        lines.append(f"{t - prev} {s};")
        prev = t
    lines.append(f"{max(0, seconds * 1000 - prev)} h-stop bang;")
    lines.append("0 pd quit;")
    open(os.path.join(d, "h_events.txt"), "w").write("\n".join(lines) + "\n")
    c = Canvas()
    lb = c.obj("loadbang", 20, 20)
    tb = c.obj("t b b b", 20, 45)
    c.c(lb, 0, tb, 0)
    dsp = c.msg("; pd dsp 1", 200, 70)
    c.c(tb, 2, dsp, 0)
    wm = c.msg("open h.wav, start", 300, 70)
    c.c(tb, 1, wm, 0)
    qm = c.msg("read h_events.txt, tempo 1 msec, bang", 20, 70)
    c.c(tb, 0, qm, 0)
    ws = c.obj("writesf~ 2", 300, 150)
    c.c(wm, 0, ws, 0)
    q = c.obj("qlist", 20, 150)
    c.c(qm, 0, q, 0)
    cl, cr = c.obj("catch~ outL", 300, 100), c.obj("catch~ outR", 400, 100)
    c.c(cl, 0, ws, 0)
    c.c(cr, 0, ws, 1)
    sr = c.obj("r h-stop", 500, 100)
    sm = c.msg("stop", 500, 125)
    c.c(sr, 0, sm, 0)
    c.c(sm, 0, ws, 0)
    # test input
    if inp == "tone":     # a decaying 220/330 Hz tone every 1.5 s
        src = c.obj("osc~ 220", 700, 20)
        e = c.obj("vline~", 800, 20)
        met = c.obj("metro 1500", 800, 0)
        c.c(lb, 0, met, 0)
        em = c.msg("0.5, 0 900", 800, 10)
        c.c(met, 0, em, 0)
        c.c(em, 0, e, 0)
        m = c.obj("*~", 700, 60)
        c.c(src, 0, m, 0)
        c.c(e, 0, m, 1)
    elif inp == "sine":   # a steady A3 (220 Hz)
        m = c.obj("*~ 0.25", 700, 60)
        c.c(c.obj("osc~ 220", 700, 20), 0, m, 0)
    elif inp == "saw":    # a steady bright E3 (164.8 Hz)
        m = c.obj("*~ 0.15", 700, 60)
        c.c(c.ch(c.obj("phasor~ 164.81", 700, 20), "-~ 0.5"), 0, m, 0)
    elif inp == "clicks":  # knocks every 250 ms through a resonance
        v = c.obj("vline~", 800, 20)
        met = c.obj("metro 250", 800, 0)
        c.c(lb, 0, met, 0)
        em = c.msg("1, 0 0 2", 800, 10)
        c.c(met, 0, em, 0)
        c.c(em, 0, v, 0)
        f = c.obj("vcf~ 6", 700, 40)
        c.c(v, 0, f, 0)
        c.c(c.obj("sig~ 900", 750, 30), 0, f, 1)
        m = c.obj("*~ 2", 700, 60)
        c.c(f, 0, m, 0)
    elif inp == "voice":   # a crude singer: a buzzy tone with vibrato through two formants, phrases of 4 notes
        q = c.obj("qlist", 1000, 0)
        open(os.path.join(d, "h_voice.txt"), "w").write(
            "".join(f"{0 if i == 0 else 2000} h-vn {n};\n" for i, n in enumerate([57, 60, 64, 62] * 40)))
        qm = c.msg("read h_voice.txt, bang", 1000, 20)
        c.c(lb, 0, qm, 0)
        c.c(qm, 0, q, 0)
        hz = c.obj("line~", 1100, 60)
        c.c(c.m(c.ch(c.obj("r h-vn", 1100, 0), "mtof"), "$1 80"), 0, hz, 0)
        vib = c.ch(c.obj("osc~ 5.2", 1200, 40), "*~ 0.012", "+~ 1")
        f = c.obj("*~", 1100, 90)
        c.c(hz, 0, f, 0)
        c.c(vib, 0, f, 1)
        saw = c.ch(f, "phasor~", "-~ 0.5")
        fm1, fm2 = c.obj("vcf~ 8", 1100, 150), c.obj("vcf~ 10", 1200, 150)
        for v, cf in ((fm1, 700), (fm2, 1150)):
            c.c(saw, 0, v, 0)
            c.c(c.obj(f"sig~ {cf}"), 0, v, 1)
        env = c.obj("vline~", 1300, 150)
        met = c.obj("metro 2000", 1300, 100)
        c.c(lb, 0, met, 0)
        c.c(c.m(met, "0.6 150, 0 300 1600"), 0, env, 0)
        sm = c.obj("+~", 1100, 190)
        c.c(fm1, 0, sm, 0)
        c.c(fm2, 0, sm, 1)
        m = c.obj("*~", 700, 60)
        c.c(sm, 0, m, 0)
        c.c(env, 0, m, 1)
    elif inp == "noise":
        src = c.obj("noise~", 700, 20)
        m = c.obj("*~ 0.1", 700, 60)
        c.c(src, 0, m, 0)
    else:
        m = c.obj("sig~ 0", 700, 60)
    c.c(m, 0, c.obj("s~ inL", 700, 90), 0)
    c.c(m, 0, c.obj("s~ inR", 800, 90), 0)
    c.obj("main", 20, 250)
    if extra:
        extra(c)
    for n in list(PRINTS) + list(prints):
        r = c.obj("r " + n)
        c.c(r, 0, c.obj("print " + n), 0)
    c.save(os.path.join(d, "h_test.pd"))
    res = subprocess.run(["pd", "-nosound", "-nomidi", "-batch", "-stderr", "-open", "h_test.pd"], cwd=d,
                         capture_output=True, text=True, timeout=1800)
    a = audio(os.path.join(d, "h.wav"))
    if own and not keep:
        shutil.rmtree(d, ignore_errors=True)
    return res.stderr, a


def audio(path):
    b = open(path, "rb").read()
    i = b.index(b"data") + 8
    n = (len(b) - i) // 4 * 4
    return np.frombuffer(b[i:i + n], dtype="<i2").reshape(-1, 2).astype(float) / 32768


def errors(log):
    bad = []
    for l in log.splitlines():
        low = l.lower()
        if ("error" in low or "no such" in low or "couldn't create" in low or "bad arguments" in low
                or "no method" in low or "inlet: expected" in low or "dsp loop" in low or "out of range" in low
                or "stack overflow" in low or "can't" in low):
            bad.append(l)
    return bad


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
