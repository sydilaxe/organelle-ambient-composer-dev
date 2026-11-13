"""Amble's reverbs.

Bloom 1 / Bloom 2: after the Alesis MidiVerb II "Bloom" programs (45: 8 s, 49: 7 s with an 85 ms
pre-delay), ported from Conduit's adjustable Bloom (tools/ref/bloom.c, GPL-3), whose structure and
delay times come from thement's midiverb_emulator analysis. A damped feedback loop through 15
diffusing all-passes (the loop is what makes the sound swell instead of starting dense), then 3 short
all-passes a side. It runs at half the Organelle's rate (22.05 kHz, near the unit's 23.4 kHz) with the
delays kept in milliseconds, in 16-sample blocks: the shortest diffuser (0.55 ms on the unit) and the
loop's own feedback can't be shorter than one block (0.73 ms) - the only departure from the C version.
Vintage: 13-bit input quantisation, as the unit's converter.

Hall: an 8-line FDN (Hadamard feedback), two modulated lines, damping per line. Shimmer = the Hall
with an octave-up pitch shifter in its feedback."""
from pdlib import Canvas
from gen_dsp import switched, mul, add
from data import BLOOM_RATE, BLOOM_CHAIN, BLOOM_LEFT, BLOOM_RIGHT, BLOOM_PRE, HALL_MS


def ap_bloom(c, src, name, ms, g=0.5, size_recv=None):
    """Conduit's all-pass: stores -(in + g*d), passes d - g*(in + g*d)"""
    dr = c.obj(f"delread~ {name} {ms:.4f}")
    if size_recv:
        c.c(c.to(c.recv(size_recv), f"* {ms:.4f}"), 0, dr, 0)
    sm = c.obj("+~")
    c.c(src, 0, sm, 0)
    c.c(c.to(dr, f"*~ {g}"), 0, sm, 1)
    c.c(c.to(sm, "*~ -1"), 0, c.obj(f"delwrite~ {name} {ms * 1.6 + 5:.1f}"), 0)
    return add(c, dr, c.to(sm, f"*~ {-g}"))


def bloom():
    s, ln = switched("bloom", "ac-g-rvb", block="16 1 0.5")
    s.comment("Bloom (MidiVerb II programs 45 / 49, after Conduit's bloom.c), at 22.05 kHz in 16-sample blocks")
    x = s.obj("inlet~", 20, 5)
    # Vintage: 13-bit quantisation of the input
    q = s.ch(x, "*~ 4096", "wrap~", "*~ -0.000244", "*~ 0")
    s.c(s.recv("ac-vintage"), 0, q, 1)
    xi = add(s, x, q)
    s.to(xi, "delwrite~ $0-blpre 700")
    pre = s.obj("delread~ $0-blpre 0")
    s.c(s.to(s.recv("ac-blpre"), "t f"), 0, pre, 0)
    inlp = s.ch(pre, "*~ 0.5", "rpole~ 0.5")
    # the loop: last time round, x0.5 x decay x (1-damp), low-passed (pole = damp), x1.5 back in
    fb = s.obj("delread~ $0-blfb 0")
    k1 = s.to(fb, "*~ 0.3")
    s.c(s.recv("ac-blk1"), 0, k1, 1)
    lp = s.to(k1, "rpole~ 0.5")
    s.c(s.recv("ac-blpole"), 0, lp, 1)
    v = add(s, s.to(lp, "*~ 1.5"), inlp)
    s.col()
    for i, d in enumerate(BLOOM_CHAIN):
        v = ap_bloom(s, v, f"$0-blc{i}", d / BLOOM_RATE * 1000, size_recv="ac-blsize")
        if i % 4 == 3:
            s.col(160)
    s.to(v, "delwrite~ $0-blfb 20")
    neg = s.to(v, "*~ -1")
    outs = []
    s.col()
    for side, ds in (("l", BLOOM_LEFT), ("r", BLOOM_RIGHT)):
        o = neg
        for i, d in enumerate(ds):
            o = ap_bloom(s, o, f"$0-bl{side}{i}", d / BLOOM_RATE * 1000, size_recv="ac-blsize")
        outs.append(o)
        s.col(160)
    for i, o in enumerate(outs):
        s.c(mul(s, o, ln), 0, s.obj("outlet~ lin", 20 + i * 200, 980), 0)
    return s


def ap(c, src, name, ms, g):
    """Schroeder all-pass (for the Hall's input diffusion)"""
    w = c.obj("+~")
    c.c(src, 0, w, 0)
    c.to(w, f"delwrite~ {name} {ms + 10}")
    d = c.obj(f"delread~ {name} {ms}")
    c.c(c.to(d, f"*~ {g}"), 0, w, 1)
    return add(c, d, c.to(w, f"*~ {-g}"))


def hall():
    s, ln = switched("hall", "ac-g-rvh", block="64 1 0.5")
    s.comment("Hall: 8-line FDN, Hadamard feedback, 2 modulated lines; Shimmer adds an octave-up shifter "
              "in the loop. At 22.05 kHz (half the CPU); its input is band-limited outside")
    x = s.obj("inlet~", 20, 5)
    shim_in = s.obj("+~")
    s.c(ap(s, ap(s, ap(s, x, "$0-hap1", 4.77, 0.62), "$0-hap2", 3.59, 0.62), "$0-hap3", 12.7, 0.6), 0, shim_in, 0)
    damps = []
    adds = []
    size = s.recv("ac-rvsize")
    damp = s.recv("ac-hdamp")
    s.col()
    for i, ms in enumerate(HALL_MS):
        a = s.obj("+~")
        s.c(s.to(shim_in, f"*~ {[1, -1, 1, -1, -1, 1, -1, 1][i] * 0.5}"), 0, a, 0)
        s.to(a, f"delwrite~ $0-hl{i} 300")
        if i in (1, 5):
            d = s.obj(f"delread4~ $0-hl{i}")
            base = s.obj(f"sig~ {ms}")
            s.c(s.to(size, f"* {ms}"), 0, base, 0)
            s.c(add(s, base, s.ch(s.obj(f"osc~ {0.11 + 0.07 * i / 5}"), f"*~ {0.9 + 0.3 * i / 5}")), 0, d, 0)
        else:
            d = s.obj(f"delread~ $0-hl{i} {ms}")
            s.c(s.to(size, f"* {ms}"), 0, d, 0)
        dm = s.to(d, "lop~ 6000")
        s.c(damp, 0, dm, 1)
        damps.append(dm)
        adds.append(a)
        s.col(130)
    # Hadamard 8 (fast transform), then x g_i / sqrt(8) back into each line
    v = list(damps)
    for h in (1, 2, 4):
        nv = list(v)
        for i in range(8):
            if i & h == 0:
                nv[i] = add(s, v[i], v[i + h])
                nv[i + h] = s.obj("-~")
                s.c(v[i], 0, nv[i + h], 0)
                s.c(v[i + h], 0, nv[i + h], 1)
        v = nv
    for i in range(8):
        g = s.to(v[i], "*~ 0.3")
        s.c(s.to(s.recv(f"ac-rg{i}"), "* 0.353553"), 0, g, 1)
        s.c(g, 0, adds[i], 1)
    # output level matched to Bloom's on program material (the Hall measured about 9 dB quieter)
    L = s.obj("*~ 0.9")
    R = s.obj("*~ 0.9")
    for i, dm in enumerate(damps):
        s.c(dm, 0, L if i % 2 == 0 else R, 0)
    # shimmer: two crossfaded taps sweeping a 125 ms window -> an octave up, back into the loop
    s.col()
    mono = s.obj("*~ 0.25")
    for dm in damps:
        s.c(dm, 0, mono, 0)
    s.to(mono, "delwrite~ $0-shd 300")
    ph = s.obj("phasor~ 8")
    shout = s.obj("hip~ 200")
    for off in (0, 0.5):
        p = s.ch(ph, f"+~ {off}", "wrap~") if off else ph
        vd = s.obj("vd~ $0-shd")
        s.c(s.ch(p, "*~ -125", "+~ 126.5"), 0, vd, 0)
        win = s.ch(p, "*~ 0.5", "-~ 0.25", "cos~")
        s.c(mul(s, vd, win), 0, shout, 0)
    sh = s.ch(s.recv("ac-shim"), "line~")
    s.c(mul(s, s.to(shout, "lop~ 7000"), sh), 0, shim_in, 1)
    for i, o in enumerate((L, R)):
        s.c(mul(s, o, ln), 0, s.obj("outlet~ lin", 20 + i * 200, 980), 0)
    return s
