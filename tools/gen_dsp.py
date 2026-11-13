"""Sound: pad voices (5 synthesis types), drone, textures, granular cloud, bells, input processing,
FDN reverb and the master stage.

Buses (throw~/catch~): ac-mixL/R dry mix, ac-padL/R the pad voices, ac-send reverb input (mono),
ac-src what the cloud resamples. Every layer that can be silent sits in a switch~ed subpatch."""
from pdlib import Canvas
from data import CLOUD_LEN, TEXG


def switched(name, gain, block=None, hook=None):
    """Subpatch switched on while [r gain] ('target ms') is above 0, off 100 ms after it fades to 0.
    Returns (canvas, line~) - multiply your output by the line~."""
    s = Canvas(name, w=1600, h=1000)
    s.comment(f"on while {gain} > 0")
    tl = s.to(s.recv(gain), "t l l")
    ln = s.to((tl, 1), "line~")
    up = s.to((tl, 0), "unpack f f")
    d = s.obj("delay")
    s.c(s.to((up, 1), "+ 100"), 0, d, 1)
    sw = s.obj(f"switch~ {block}" if block else "switch~")
    st = s.obj("t f f")
    s.c(st, 0, sw, 0)
    if hook:
        s.c(s.ch((st, 1), "change", "sel 1"), 0, s.obj("s " + hook), 0)
    sel = s.to((up, 0), "sel 0")
    s.c(sel, 0, d, 0)
    s.c(s.m(d, "0"), 0, st, 0)
    on = s.to((sel, 1), "t b b")
    s.c(s.m((on, 1), "stop"), 0, d, 0)
    s.c(s.m((on, 0), "1"), 0, st, 0)
    s.c(s.m(s.obj("loadbang"), "0"), 0, st, 0)
    s.col()
    return s, ln


def mul(c, a, b):
    """signal a * signal b (a, b: obj or (obj, outlet))"""
    m = c.obj("*~")
    c.c(*(a if isinstance(a, tuple) else (a, 0)), m, 0)
    c.c(*(b if isinstance(b, tuple) else (b, 0)), m, 1)
    return m


def add(c, a, b):
    m = c.obj("+~")
    c.c(*(a if isinstance(a, tuple) else (a, 0)), m, 0)
    c.c(*(b if isinstance(b, tuple) else (b, 0)), m, 1)
    return m


def ctl(c, dest, recv, expr=None, inlet=1, first=False):
    """[r recv] (-> first element) (-> expr) -> dest inlet"""
    src = c.recv(recv)
    if first:
        src = c.to(src, "unpack f f")
    if expr:
        src = c.to(src, "expr " + expr)
    c.c(src, 0, dest, inlet)
    return src


def throws(c, L, R, mix=1.0, send=0.0, src=0.0, bus="mix", sbus="ac-send"):
    """to the mix (bus "mix") or the harmony bed (bus "bed": drone and sub, kept apart for SETUP Output split),
    plus the reverb send and the cloud source"""
    for sig, bus in ((L, f"ac-{bus}L"), (R, f"ac-{bus}R")):
        c.c(c.to(sig, f"*~ {mix}"), 0, c.obj("throw~ " + bus), 0)
    if send or src:
        m = add(c, L, R)
        if send:
            c.c(c.to(m, f"*~ {send * 0.5}"), 0, c.obj("throw~ " + sbus), 0)
        if src:
            c.c(c.to(m, f"*~ {src * 0.5}"), 0, c.obj("throw~ ac-src"), 0)


def throws_to(sbus):
    """throws() with the reverb send on a group's bus (SENDS knob pages)"""
    return lambda *a, **k: throws(*a, sbus=sbus, **k)


def span(c, sig, pos):
    """equal-power pan of sig by a signal position (0 left .. 1 right) -> (L, R)"""
    q = c.to(pos, "*~ 0.25")
    gl = c.to(q, "cos~")
    gr = c.ch(q, "-~ 0.25", "cos~")
    return mul(c, sig, gl), mul(c, sig, gr)


def pan(c, sig, l, r):
    return c.to(sig, f"*~ {l}"), c.to(sig, f"*~ {r}")


# ======================================================================================
# Pad voice abstraction (acvoice.pd, argument = voice 0..3)
# ======================================================================================

def _flav_inlets(s, n):
    return [s.obj("inlet~", 20 + i * 140, 5) for i in range(n)]


def _out(s, sig, ln, sigR=None, outlets=False):
    """a pad type's output, left and right, thrown to its voice's body bus ($0-bL / $0-bR, caught in the voice):
    a type that is switched off adds nothing there (12 types wired to outlets cost 20 additions a block per
    voice, sounding or not); mono types send the same to both"""
    # (outlets=True: a type in its own block size, which throw~ can't cross - the bow, in 16s)
    dst = ("outlet~", "outlet~") if outlets else ("throw~ $0-bL", "throw~ $0-bR")
    s.c(mul(s, sig, ln), 0, s.obj(dst[0], 20, 980), 0)
    s.c(mul(s, sig if sigR is None else sigR, ln), 0, s.obj(dst[1], 300, 980), 0)


def flav_fm():
    s, ln = switched("fm", "$0-fw0")
    s.comment("FM: a modulator at a per-piece ratio; index follows brightness and Weird. Right: a slightly "
              "detuned carrier with a softer index")
    f, b = _flav_inlets(s, 2)
    rat = s.to(f, "*~ 1")
    s.c(s.recv("ac-fmr"), 0, rat, 1)
    mo = s.to(rat, "osc~")
    ix = s.ch(b, "*~ 2.2", "+~ 0.15")
    w = s.to(ix, "*~ 1")
    ctl(s, w, "ac-weird", "0.5 + 1.5*$f1")
    dev = mul(s, mul(s, mo, w), f)
    car = s.ch(add(s, f, dev), "osc~", "*~ 0.42")
    carR = s.ch(add(s, s.to(f, "*~ 1.0021"), s.to(dev, "*~ 0.8")), "osc~", "*~ 0.42")
    _out(s, car, ln, add(s, s.to(car, "*~ 0.5"), s.to(carR, "*~ 0.65")))   # mono-safe (no full cancellation)
    return s


def flav_vox():
    s, ln = switched("vox", "$0-fw1")
    s.comment("Vox: a saw through two drifting vowel formants; the right side sings the opposite vowel")
    f, b = _flav_inlets(s, 2)
    saw = s.ch(f, "phasor~", "-~ 0.5")
    l1 = s.ch(s.recv("$0-la"), "osc~", "*~ 0.5")
    l2 = s.ch(s.recv("$0-lb"), "osc~", "*~ 0.5")
    bm = s.ch(b, "*~ 0.8", "+~ 0.35")
    # (shared by both sides: the low body, and the formant centres - the right side's is the mirror image)
    body = s.ch(saw, "lop~ 600", "*~ 0.2")
    c1 = s.ch(l1, "*~ 450", "+~ 505")              # 280 + 450*(0.5 + l1)
    c2 = s.ch(l2, "*~ 1000", "+~ 1400")            # 900 + 1000*(0.5 + l2)
    outs = []
    for sign in (1, -1):
        cf1 = c1 if sign == 1 else s.ch(c1, "*~ -1", "+~ 1010")
        cf2 = c2 if sign == 1 else s.ch(c2, "*~ -1", "+~ 2800")
        v1 = s.obj("vcf~ 7")
        v2 = s.obj("vcf~ 10")
        for v, cf in ((v1, cf1), (v2, cf2)):
            s.c(saw, 0, v, 0)
            s.c(cf, 0, v, 1)
        sm = s.obj("+~")
        s.c(v1, 0, sm, 0)
        s.c(s.to(v2, "*~ 0.7"), 0, sm, 0)
        s.c(body, 0, sm, 0)
        outs.append(s.to(mul(s, sm, bm), "*~ 2.2"))
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.4"), s.to(outs[1], "*~ 0.75")))
    return s


def flav_bow():
    s, ln = switched("bow", "$0-fw2", block=16)
    s.comment("Bow: a string kept ringing by filtered noise (block 16 for short delays)")
    f, b, dl = _flav_inlets(s, 3)
    exc = mul(s, s.ch(s.obj("noise~"), "lop~ 2500"), s.ch(b, "*~ 0.03", "+~ 0.006"))
    a = s.obj("+~")
    s.c(exc, 0, a, 0)
    s.to(a, "delwrite~ $0-bw 60")
    vd = s.obj("vd~ $0-bw")
    s.c(dl, 0, vd, 0)
    damp = s.to(vd, "lop~ 3000")
    ctl(s, damp, "ac-bright", "1500 + 5500*$f1", first=True)
    s.c(s.to(damp, "*~ 0.993"), 0, a, 1)
    _out(s, s.ch(vd, "hip~ 40", "*~ 9"), ln, outlets=True)
    return s


def flav_part():
    s, ln = switched("part", "$0-fw3")
    s.comment("Partials: 4 sines at per-piece ratios, each swelling on its own, tilted by brightness; "
              "the fundamental in the middle, the upper partials alternating left and right")
    f, b = _flav_inlets(s, 2)
    up = s.to(s.recv("ac-partials"), "unpack f f f")
    lt = s.to(s.recv("$0-lb"), "t f f f f")
    b2 = mul(s, b, b)
    b3 = mul(s, b2, b)
    tilt = [None, b, b2, b3]
    L, R = s.obj("*~ 0.45"), s.obj("*~ 0.45")
    for k in range(4):
        if k == 0:
            o = s.to(f, "osc~")
        else:
            r = s.to(f, f"*~ {k + 1}")
            s.c(up, k - 1, r, 1)
            o = s.to(r, "osc~")
        amp = s.ch((lt, k), f"* {[1, 1.37, 1.71, 2.13][k]}", "osc~", "*~ 0.35", "+~ 0.65")
        p = mul(s, o, amp)
        if tilt[k] is not None:
            p = mul(s, p, tilt[k])
        gl, gr = [(1, 1), (1.45, 0.15), (0.15, 1.45), (1.3, 0.35)][k]
        s.c(s.to(p, f"*~ {gl}"), 0, L, 0)
        s.c(s.to(p, f"*~ {gr}"), 0, R, 0)
    _out(s, L, ln, R)
    return s


def flav_fold():
    s, ln = switched("fold", "$0-fw4")
    s.comment("Fold: a sine wavefolded (sin of a driven sine), ring-modulated by its sub-octave; the right "
              "side folds a little less")
    f, b = _flav_inlets(s, 2)
    dr = s.ch(b, "*~ 4", "+~ 0.5", "*~ 1")
    ctl(s, dr, "ac-weird", "0.3 + 1.2*$f1")
    sub = s.ch(f, "*~ 0.5", "osc~", "*~ 0.22", "+~ 0.78")
    outs = []
    for k, d in ((1, 1.0), (0.7, 1.0017)):
        x = s.ch(s.to(f, f"*~ {d}"), "osc~")
        u = s.ch(mul(s, x, s.to(dr, f"*~ {k}")), "*~ 0.25", "-~ 0.25", "cos~", "hip~ 20")
        outs.append(s.ch(mul(s, u, sub), "lop~ 5000", "*~ 0.32"))
    # mono-safe: the right side keeps part of the left, so a mono sum never cancels
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))
    return s


def flav_pulsar():
    s, ln = switched("pulsar", "$0-fw5")
    s.comment("Pulsar: each period starts a short windowed burst of a few sine cycles; the burst length "
              "follows a drifting formant, so the voice speaks somewhere between insect and choir. The right "
              "side's formant sits higher")
    f, b = _flav_inlets(s, 2)
    form = s.ch(s.recv("$0-la"), "* 0.7", "osc~", "*~ 0.5", "+~ 0.5")
    fsig = s.to(add(s, s.to(form, "*~ 900"), s.to(b, "*~ 1400")), "+~ 450")
    ph = s.to(f, "phasor~")
    outs = []
    for m in (1, 1.18):
        k = s.obj("/~")
        s.c(s.to(fsig, f"*~ {m}"), 0, k, 0)
        s.c(f, 0, k, 1)
        u = s.ch(mul(s, ph, s.to(k, "max~ 1")), "clip~ 0 1")
        win = s.ch(u, "cos~", "*~ -0.5", "+~ 0.5")
        car = s.ch(u, "*~ 3", "cos~")
        outs.append(s.ch(mul(s, win, car), "hip~ 30", "*~ 0.75"))
    _out(s, outs[0], ln, outs[1])
    return s


def voice():
    v = Canvas(w=1800, h=1000)
    v.comment("Pad voice $1: pitch glides (delayed, so chords change one voice at a time), 5 synthesis "
              "types crossfaded by ac-v$1-flav, breathing and drift")
    up = v.to(v.recv("ac-v$1-pitch"), "unpack f f f")
    pk = v.obj("pack f f")
    pp = v.obj("pipe f f 0")
    v.c(up, 2, pp, 2)
    v.c(up, 1, pk, 1)
    v.c(up, 0, pk, 0)
    v.c(pk, 0, pp, 0)
    pk2 = v.obj("pack f f")
    v.c(pp, 1, pk2, 1)
    v.c(pp, 0, pk2, 0)
    tf = v.ch(pk2, "line 0 40", "t f f")
    dsig = v.ch(v.m(v.to((tf, 1), "expr 1000/mtof($f1) - 0.012"), "$1 40"), "line~")
    fsig = v.ch(v.m(v.to((tf, 0), "mtof"), "$1 40"), "line~")
    drift = v.ch(v.recv("$0-ld"), "osc~", "*~ 0")
    ctl(v, drift, "ac-motion", "0.005*$f1")
    f2 = mul(v, v.to(drift, "+~ 1"), fsig)
    v.col()
    br = v.ch(v.recv("ac-bright"), "line~")
    bsig = v.ch(add(v, br, v.obj("r~ ac-envb")), "clip~ 0 1")
    lu = v.to(v.recv("ac-v$1-lfo"), "unpack f f f f")
    breath = v.ch((lu, 0), "osc~", "*~ 0.5", "+~ 0.5", "*~ -0.4")
    ctl(v, breath, "ac-motion", "-0.75*(0.25+0.75*$f1)")
    amp = v.to(breath, "+~ 1")
    for i, n in ((1, "$0-ld"), (2, "$0-la"), (3, "$0-lb")):
        v.c(lu, i, v.obj("s " + n), 0)
    v.col()
    # the whole voice computes only while the pad layer plays: on at once, off 200 ms after it has faded out
    gp = v.ch(v.recv("ac-g-pad"), "unpack f f")
    psw = v.obj("switch~")
    v.c(v.m(v.obj("loadbang"), "0"), 0, psw, 0)
    pd_ = v.obj("delay")
    v.c(v.to((gp, 1), "+ 200"), 0, pd_, 1)
    gsel = v.to(gp, "sel 0")
    v.c(gsel, 0, pd_, 0)
    gon = v.to((gsel, 1), "t b b")
    v.c(v.m((gon, 1), "stop"), 0, pd_, 0)
    v.c(v.m((gon, 0), "1"), 0, psw, 0)
    v.c(v.m(pd_, "0"), 0, psw, 0)
    v.col()
    from gen_sounds import NEW_FLAVS
    nf = 6 + len(NEW_FLAVS)
    ft = v.to(v.recv("ac-v$1-flav"), "t " + " ".join(["f"] * nf))
    for i in range(nf):
        v.c(v.m(v.to((ft, i), f"== {i}"), "$1 4000"), 0, v.obj(f"s $0-fw{i}"), 0)
    v.col()
    bodyL, bodyR = v.obj("*~"), v.obj("*~")
    v.c(amp, 0, bodyL, 1)
    v.c(amp, 0, bodyR, 1)
    v.c(v.obj("catch~ $0-bL"), 0, bodyL, 0)
    v.c(v.obj("catch~ $0-bR"), 0, bodyR, 0)
    for i, fl in enumerate((flav_fm(), flav_vox(), flav_bow(), flav_part(), flav_fold(), flav_pulsar())
                           + tuple(f() for f in NEW_FLAVS)):
        sp = v.sub(fl, 20 + i * 120, 700)
        v.c(f2, 0, sp, 0)
        v.c(bsig, 0, sp, 1)
        if fl.name == "bow":
            v.c(dsig, 0, sp, 2)
            v.c((sp, 0), 0, bodyL, 0)
            v.c((sp, 1), 0, bodyR, 0)
    # stereo: the composition gives each voice a home (ac-v$1-home "pos ms", by section scene); it orbits
    # around it on its own slow cycle, as far as ac-pandepth. The voice's own stereo is kept (balance pan).
    home = v.ch(v.recv("ac-v$1-home"), "line~")
    v.c(v.m(v.ch(v.obj("loadbang"), "f $1", "expr 0.08 + 0.28*$f1"), "$1 10"), 0, home, 0)
    orb = v.to(v.to((lu, 0), "* 0.37"), "osc~")
    dep = v.to(orb, "*~ 0.2")
    v.c(v.recv("ac-pandepth"), 0, dep, 1)
    posn = v.to(add(v, dep, home), "clip~ 0.02 0.98")
    q = v.to(posn, "*~ 0.25")
    gl = v.ch(q, "cos~", "*~ 1.414")
    gr = v.ch(q, "-~ 0.25", "cos~", "*~ 1.414")
    L = mul(v, v.to(bodyL, "*~ 0.2"), v.to(gl, "clip~ 0 1"))
    R = mul(v, v.to(bodyR, "*~ 0.2"), v.to(gr, "clip~ 0 1"))
    for sig, bus in ((L, "ac-padL"), (R, "ac-padR")):
        v.c(sig, 0, v.obj("throw~ " + bus), 0)
    return v


# ======================================================================================
# Main patch layers
# ======================================================================================

def drone():
    s, ln = switched("drone", "ac-g-drone")
    s.comment("Drone on the tonic: root, a beating twin, a per-piece interval, sub, and a breathing tube")
    f = s.ch(s.m(s.ch(s.recv("ac-dronep"), "line 0 40", "mtof"), "$1 40"), "line~")
    # stereo: the root in the middle, the beating twin left, the interval right, a breath tube each side
    sL, sR = s.obj("lop~ 1000"), s.obj("lop~ 1000")
    for sm in (sL, sR):
        ctl(s, sm, "ac-bright", "350 + 3500*$f1", first=True)
    root = s.ch(f, "osc~", "*~ 0.26")
    twin = s.ch(f, "*~ 1.0035", "osc~", "*~ 0.13")
    iv = s.to(f, "*~ 1.5")
    s.c(s.recv("ac-dint"), 0, iv, 1)
    ivs = mul(s, s.to(iv, "osc~"), s.ch(s.obj("osc~ 0.031"), "*~ 0.06", "+~ 0.1"))
    harm = s.ch(s.recv("ac-dharm"), "line~")
    tubes = []
    for k, (hm, rt) in enumerate(((1.0, 0.023), (1.5, 0.017))):
        tube = s.obj("vcf~ 40")
        s.c(s.obj("noise~"), 0, tube, 0)
        s.c(mul(s, f, s.to(harm, f"*~ {hm}")), 0, tube, 1)
        tubes.append(mul(s, s.to(tube, "*~ 5"), s.ch(s.obj(f"osc~ {rt}"), "*~ 0.5", "+~ 0.5")))
    # the twin and the interval orbit in opposite directions; the two tubes drift on their own cycles
    s.c(s.to(root, "*~ 0.7"), 0, sL, 0)
    s.c(s.to(root, "*~ 0.7"), 0, sR, 0)
    orb = s.obj("osc~ 0.013")
    for src, sign, g in ((twin, 1, 1.2), (ivs, -1, 1.2)):
        pl, pr = span(s, s.to(src, f"*~ {g}"), s.ch(orb, f"*~ {0.4 * sign}", "+~ 0.5"))
        s.c(pl, 0, sL, 0)
        s.c(pr, 0, sR, 0)
    for k, (tb, rt) in enumerate(zip(tubes, (0.0091, 0.0067))):
        pl, pr = span(s, s.to(tb, "*~ 0.9"), s.ch(s.obj(f"osc~ {rt}"), f"*~ {0.42 if k == 0 else -0.42}", "+~ 0.5"))
        s.c(pl, 0, sL, 0)
        s.c(pr, 0, sR, 0)
    # the pulse: a swell on every bar, its depth set by the section (0 = steady)
    env = s.ch(s.m(s.to(s.recv("ac-dpulse"), "expr max(100, $f1-450)"), "1 450, 0 $1 450"), "vline~")
    dep = s.to(env, "*~ 0")
    pu = s.to(s.recv("ac-pulse"), "t f f")
    s.c(pu, 1, dep, 1)
    pa = s.to(dep, "+~ 1")
    s.c(s.to((pu, 0), "expr 1-$f1"), 0, pa, 1)
    oL = mul(s, mul(s, s.to(sL, "hip~ 25"), pa), ln)
    oR = mul(s, mul(s, s.to(sR, "hip~ 25"), pa), ln)
    throws_to("ac-sendd")(s, oL, oR, mix=0.6, send=0.3, src=1, bus="bed")
    return s


def tex_rain():
    s, ln = switched("rain", "ac-g-tex0")
    s.comment("Rain: a soft hiss, a dense patter of tiny unpitched ticks (sparse noise impulses ringing bright "
              "bands that wander), and a few heavier plops - each side its own")
    swell = s.ch(s.obj("osc~ 0.031"), "*~ 0.3", "+~ 0.7")
    outs = []
    for side in range(2):
        bed = s.ch(s.obj("noise~"), "hip~ 600", "lop~ 6000", "*~ 0.05")
        pat = s.obj("vcf~ 2.5")
        s.c(s.ch(s.obj("noise~"), "-~ 0.97", "max~ 0", "*~ 30", "lop~ 9000"), 0, pat, 0)   # ~1300 small drops a second
        s.c(s.ch(s.obj("noise~"), "lop~ 50", "*~ 40000", f"+~ {3800 + 600 * side}", "clip~ 1500 7500"), 0, pat, 1)
        plop = s.obj("vcf~ 6")
        s.c(s.ch(s.obj("noise~"), "-~ 0.9997", "max~ 0", "*~ 1500"), 0, plop, 0)
        s.c(s.obj(f"sig~ {850 + 150 * side}"), 0, plop, 1)
        o = add(s, add(s, bed, s.to(pat, f"*~ {TEXG['RAIN_PAT']}")), s.to(plop, f"*~ {TEXG['RAIN_PLOP']}"))
        outs.append(mul(s, mul(s, o, swell), ln))
        s.col(220)
    throws(s, s.to(outs[0], f"*~ {TEXG['RAIN_G']}"), s.to(outs[1], f"*~ {TEXG['RAIN_G']}"), mix=0.5, send=0.35)
    return s


def tex_wind():
    s, ln = switched("wind", "ac-g-tex1")
    s.comment("Wind: noise whistling through two slow resonant bands tuned to the chord")
    up = s.to(s.recv("ac-wind"), "unpack f f f")
    p1, p2 = s.obj("pack f f"), s.obj("pack f f")
    s.c(up, 2, p1, 1)
    s.c(up, 2, p2, 1)
    s.c(up, 1, p2, 0)
    s.c(up, 0, p1, 0)
    gust = s.ch(add(s, s.obj("osc~ 0.043"), s.ch(s.obj("osc~ 0.071"), "*~ 0.6")), "*~ 0.4", "+~ 0.55", "max~ 0.05")
    outs = []
    for p, rate in ((p1, 0.05), (p2, 0.037)):
        cf = mul(s, s.ch(p, "line~"), s.ch(s.obj(f"osc~ {rate}"), "*~ 0.12", "+~ 1"))
        v = s.obj("vcf~ 25")
        s.c(s.obj("noise~"), 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(mul(s, mul(s, s.to(v, "*~ 4"), gust), ln))
    throws(s, outs[0], outs[1], mix=0.5, send=0.5)
    return s


def tex_ember():
    s, ln = switched("ember", "ac-g-tex2")
    s.comment("Embers: sparse crackles and soft wood knocks (thresholded noise into resonant filters)")
    swell = s.ch(s.obj("osc~ 0.02"), "*~ 0.4", "+~ 0.6")
    outs = []
    for cf, th in ((2600, 0.9993), (1700, 0.9993)):
        v = s.obj("vcf~ 4")
        s.c(s.ch(s.obj("noise~"), f"-~ {th}", "max~ 0", "*~ 700"), 0, v, 0)
        s.c(s.obj(f"sig~ {cf}"), 0, v, 1)
        outs.append(v)
    k = s.obj("vcf~ 9")
    s.c(s.ch(s.obj("noise~"), "-~ 0.9997", "max~ 0", "*~ 1500"), 0, k, 0)
    s.c(s.obj("sig~ 380"), 0, k, 1)
    g = mul(s, s.to(swell, "*~ 15"), ln)
    L = mul(s, add(s, outs[0], s.to(k, "*~ 0.7")), g)
    R = mul(s, add(s, outs[1], s.to(k, "*~ 0.7")), g)
    throws(s, L, R, mix=0.5, send=0.5)
    return s


def tex_chirp():
    s, ln = switched("chirp", "ac-g-tex3")
    s.comment("Chirps: creature calls - a fast pitch sweep with a buzz, in bursts")
    tl = s.to(s.recv("ac-chirp"), "t l l")
    ex = s.to((tl, 0), "expr $f1; $f1*$f2; $f3")
    pk = s.obj("pack f f f")
    for i in (2, 1, 0):
        s.c(ex, i, pk, i)
    fr = s.ch(s.m(pk, "$1, $2 $3"), "vline~")
    env = s.ch(s.m(s.to((tl, 1), "expr $f3*1.3"), "1, 0 $1"), "vline~")
    pn = s.to((tl, 1), "expr cos($f4*1.5708); sin($f4*1.5708)")
    buzz = s.ch(s.obj("osc~ 33"), "*~ 0.05", "+~ 1")
    sig = mul(s, s.to(mul(s, buzz, fr), "osc~"), mul(s, env, env))
    sig = mul(s, s.to(sig, "*~ 0.5"), ln)
    L, R = s.to(sig, "*~ 1"), s.to(sig, "*~ 1")
    s.c(pn, 0, L, 1)
    s.c(pn, 1, R, 1)
    throws(s, L, R, mix=0.5, send=0.7)
    return s


def cloud():
    s, ln = switched("cloud", "ac-g-cloud", hook="ac-cloud-on")
    s.comment("Cloud: 4 overlapping grain streams from the 8 s buffer, each transposed by a chord-friendly ratio "
              "(sometimes reversed)")
    rate = s.to(s.recv("ac-gdur"), "expr 1000/$f1")
    on = s.recv("ac-cloud-on")
    L, R = s.obj("*~ 0.7"), s.obj("*~ 0.7")
    for i in range(4):
        ph = s.obj("phasor~")
        s.c(rate, 0, ph, 0)
        s.c(s.m(on, f"{i * 0.25}"), 0, ph, 1)
        win = s.ch(ph, "cos~", "*~ -0.5", "+~ 0.5")
        pos = s.ch(s.obj("noise~"), "abs~", f"*~ {CLOUD_LEN - 2 * 81000 - 1000}", "+~ 81000", "samphold~")
        s.c(ph, 0, pos, 1)
        ksh = s.obj("samphold~")
        s.c(s.to(s.recv(f"ac-gr{i}"), "expr $f1*acgdurv*44.1"), 0, ksh, 0)
        s.c(ph, 0, ksh, 1)
        idx = add(s, mul(s, ph, ksh), pos)
        g = mul(s, s.to(idx, "tabread4~ acbuf"), win)
        gsp = s.obj("*~ 0.48")
        s.c(s.obj("noise~"), 0, gsp, 0)
        s.c(s.recv("ac-cloudspread"), 0, gsp, 1)
        gp = s.ch(gsp, "+~ 0.5", "samphold~")
        s.c(ph, 0, gp, 1)
        gl, gr = span(s, g, gp)
        s.c(gl, 0, L, 0)
        s.c(gr, 0, R, 0)
        s.col(160)
    throws_to("ac-sendc")(s, mul(s, L, ln), mul(s, R, ln), mix=0.85, send=1.2)
    return s


def cloud_write():
    s = Canvas("cloud-write", w=1200)
    s.comment("Fills the cloud buffer: the composer's own sound, or the input (cloud mode, capture). Freeze stops it.")
    tw = s.obj("tabwrite~ acbuf")
    s.c(mul(s, s.obj("r~ ac-in"), s.ch(s.recv("ac-incl"), "line~")), 0, tw, 0)
    s.c(mul(s, s.obj("r~ ac-resamp"), s.ch(s.recv("ac-inclr"), "line~")), 0, tw, 0)
    met = s.obj("metro 8000")
    s.c(s.recv("ac-init"), 0, met, 0)
    sp = s.to(met, "spigot 1")
    s.c(s.ch(s.recv("ac-freezeupd"), "expr acfreeze==0"), 0, sp, 1)
    s.c(sp, 0, tw, 0)
    s.c(s.recv("ac-cwstart"), 0, tw, 0)
    return s


def bells():
    s, ln = switched("bells", "ac-g-bell")
    s.comment("Bells: the motif, played on 3-partial struck bars (per-piece partial ratios)")
    tl = s.to(s.recv("ac-bell"), "t l b")
    cnt = s.obj("f")
    s.c(tl, 1, cnt, 0)
    s.c(s.ch(cnt, "+ 1", "% 2"), 0, cnt, 1)
    lp = s.obj("list prepend")
    s.c(cnt, 0, lp, 1)
    s.c(tl, 0, lp, 0)
    rt = s.ch(lp, "route 0 1")
    bs = s.to(s.recv("ac-bellset"), "unpack f f f")
    L, R = s.obj("*~"), s.obj("*~")
    s.c(ln, 0, L, 1)
    s.c(ln, 0, R, 1)
    for j in range(2):
        up = s.to((rt, j), "unpack f f f")
        mf = s.to((up, 0), "mtof")
        # the note's place; its upper partials fan out a little to either side
        bpn = s.to((up, 2), "expr cos($f1*1.5708); sin($f1*1.5708); cos(max(0, $f1-0.22)*1.5708); "
                            "sin(max(0, $f1-0.22)*1.5708); cos(min(1, $f1+0.22)*1.5708); sin(min(1, $f1+0.22)*1.5708)")
        for k, (amp, dec) in enumerate(((0.32, 5200), (0.15, 2600), (0.08, 1100))):
            fr = s.to(mf, "* 1")
            s.c(bs, k, fr, 1)
            env = s.ch(s.m(s.to((up, 1), f"* {amp}"), f"$1, 0 {dec}"), "vline~")
            part = mul(s, s.to(fr, "osc~"), mul(s, env, env))
            for side, dst in ((0, L), (1, R)):
                m = s.to(part, "*~ 0.7")
                s.c(bpn, 2 * k + side, m, 1)
                s.c(m, 0, dst, 0)
        s.col(160)
    throws_to("ac-sendb")(s, L, R, mix=1.1, send=1.0)
    return s


def inp():
    s = Canvas("input", w=1600)
    s.comment("External audio: dry blend, mono feed for resonators / tape / cloud, envelope (ghost mode, onsets)")
    iL, iR = s.obj("r~ inL"), s.obj("r~ inR")
    s.c(s.ch(add(s, iL, iR), "*~ 0.5", "hip~ 50"), 0, s.obj("s~ ac-in"), 0)
    dry = s.ch(s.recv("ac-g-dry"), "line~")
    for sig, bus in ((iL, "ac-mixL"), (iR, "ac-mixR")):
        s.c(mul(s, sig, dry), 0, s.obj("throw~ " + bus), 0)
    s.col()
    s.c(s.recv("ac-ghost"), 0, s.obj("v acghost"), 0)
    env = s.ch(add(s, iL, iR), "env~ 2048 1024", "expr max(0, min(1, ($f1-45)/40))")
    te = s.to(env, "t f f f")
    s.c(s.ch(s.m(s.to((te, 2), "expr $f1*acghost"), "$1 50"), "line~"), 0, s.obj("s~ ac-envb"), 0)
    ons = s.ch((te, 1), "expr $f1 - acinprev > 0.12 && $f1 > 0.25", "sel 1")
    s.c(te, 0, s.obj("v acinprev"), 0)
    sp = s.obj("spigot 1")
    s.c(ons, 0, sp, 0)
    tb = s.to(sp, "t b b")
    s.c(tb, 0, s.obj("s ac-inonset"), 0)
    s.c(s.m((tb, 1), "0"), 0, sp, 1)
    s.c(s.m(s.to((tb, 1), "delay 300"), "1"), 0, sp, 1)
    return s


def reso():
    s, ln = switched("resonate", "ac-g-res")
    s.comment("Resonate: the input rings 4 comb strings tuned to the current chord (they glide on changes)")
    src = s.to(s.obj("r~ ac-in"), "*~ 0.3")
    L, R = s.obj("hip~ 60"), s.obj("hip~ 60")
    damps, fbs = [], []
    for k in range(4):
        a = s.obj("+~")
        s.c(src, 0, a, 0)
        s.to(a, f"delwrite~ ac-rs{k} 40")
        vd = s.obj(f"vd~ ac-rs{k}")
        s.c(s.ch(s.recv(f"ac-res{k}"), "line~"), 0, vd, 0)
        dm = s.to(vd, "lop~ 3000")
        fb = s.to(dm, "*~ 0.95")
        s.c(fb, 0, a, 1)
        damps.append(dm)
        fbs.append(fb)
        s.c(vd, 0, L if k % 2 == 0 else R, 0)
        s.col(150)
    for lst, rcv in ((damps, "ac-resdamp"), (fbs, "ac-resfb")):
        r = s.recv(rcv)
        for o in lst:
            s.c(r, 0, o, 1)
    throws_to("ac-sendi")(s, mul(s, s.to(L, "*~ 0.12"), ln), mul(s, s.to(R, "*~ 0.12"), ln), mix=1, send=0.6)
    return s


def tape():
    s, ln = switched("tape", "ac-g-tape")
    s.comment("Tape: long wobbling echoes that darken and saturate as they repeat")
    a = s.obj("+~")
    s.c(s.obj("r~ ac-in"), 0, a, 0)
    s.to(a, "delwrite~ ac-tape 6000")
    taps = []
    for r1, d1, r2, d2, base in ((0.27, 7, 1.9, 0.7, 3100), (0.21, 9, 1.3, 0.9, 4300)):
        m = add(s, s.ch(s.obj(f"osc~ {r1}"), f"*~ {d1}"), s.ch(s.obj(f"osc~ {r2}"), f"*~ {d2}"))
        vd = s.obj("vd~ ac-tape")
        s.c(s.to(m, f"+~ {base}"), 0, vd, 0)
        taps.append(vd)
    s.c(s.ch(taps[0], "lop~ 2400", "hip~ 90", "*~ 0.58", "clip~ -0.8 0.8"), 0, a, 1)
    throws_to("ac-sendi")(s, mul(s, s.to(taps[0], "lop~ 3500"), ln), mul(s, s.to(taps[1], "lop~ 3000"), ln), mix=0.5, send=0.4)
    return s


def allpass(c, src, name, ms, g):
    w = c.obj("+~")
    c.c(src, 0, w, 0)
    c.to(w, f"delwrite~ {name} {ms + 10}")
    d = c.obj(f"delread~ {name} {ms}")
    c.c(c.to(d, f"*~ {g}"), 0, w, 1)
    y = add(c, d, c.to(w, f"*~ {-g}"))
    return y


def master():
    s = Canvas("master", w=2400, h=1200)
    s.comment("Pad bus, 4-line FDN reverb (Householder feedback, two modulated lines), master fade, "
              "compressor, clip")
    pg = s.ch(s.recv("ac-g-pad"), "line~")
    pL = mul(s, s.obj("catch~ ac-padL"), pg)
    pR = mul(s, s.obj("catch~ ac-padR"), pg)
    # the piece's character on the pads (chorus, tape, ring, crush) - dry scaled by ac-chdry
    from gen_sounds import CHARS
    cd = s.ch(s.recv("ac-chdry"), "line~")
    pdL, pdR = mul(s, pL, cd), mul(s, pR, cd)
    for fn in CHARS:
        sp = s.sub(fn())
        s.c(pL, 0, sp, 0)
        s.c(pR, 0, sp, 1)
        s.c((sp, 0), 0, s.obj("throw~ ac-bedL"), 0)
        s.c((sp, 1), 0, s.obj("throw~ ac-bedR"), 0)
    pm = add(s, pL, pR)
    s.c(s.to(pm, "*~ 0.5"), 0, s.obj("s~ ac-padsig"), 0)
    # reverb send level: with the Mix knob at its default (45 %) the reverb sits about 6 dB under the dry sound,
    # at 100 % about level with it (measured in a playing piece; it was 17-27 dB under before)
    rin = s.obj("*~ 1.23")
    # the send buses, each scaled by its SENDS knob (0..2: 50 % on the knob = the designed balance)
    from data import SEND_BUS
    for name, bus in SEND_BUS.items():
        src = s.to(pm, "*~ 0.3") if name == "acsndp" else s.obj("catch~ " + bus)
        if name == "acsndp":       # the pads are sent from their bus here, the notes you play throw to ac-sendp
            s.c(s.obj("catch~ ac-sendp"), 0, src, 0)
        s.c(mul(s, src, s.ch(s.recv("ac-sg-" + name), "line~")), 0, rin, 0)
    rs = s.obj("s~ ac-resamp")
    s.c(s.obj("catch~ ac-src"), 0, rs, 0)
    s.c(s.to(pm, "*~ 0.5"), 0, rs, 0)
    s.col()
    # reverb input: the section swell (ac-rvin) and the hold gate (ac-rvfz)
    rv = mul(s, mul(s, rin, s.ch(s.recv("ac-rvin"), "line~")), s.ch(s.recv("ac-rvfz"), "line~"))
    import gen_verb
    bl = s.sub(gen_verb.bloom())
    rvlp = s.ch(rv, "lop~ 8000", "lop~ 9000")          # both reverbs run at 22.05 kHz
    s.c(rvlp, 0, bl, 0)
    hl = s.sub(gen_verb.hall())
    s.c(rvlp, 0, hl, 0)
    wet = s.ch(s.recv("ac-rwet"), "line~")
    rL = add(s, s.ch((bl, 0), "lop~ 9000"), (hl, 0))
    rR = add(s, s.ch((bl, 1), "lop~ 9000"), (hl, 1))
    # the reverb's low end in mono (below about 250 Hz, where the drone and sub put most of their energy): the
    # prominent reverb then sums to mono without losing much, and stays fully decorrelated above. The left
    # side's lows serve both sides (averaging the two would cancel on held tones, where the sides can sit in
    # opposite phase)
    lowL, lowR = s.to(rL, "lop~ 250"), s.to(rR, "lop~ 250")
    low = lowL
    wides = []
    for r, lo in ((rL, lowL), (rR, lowR)):
        hi = s.obj("-~")
        s.c(r, 0, hi, 0)
        s.c(lo, 0, hi, 1)
        wides.append(add(s, hi, low))
    wL, wR = mul(s, wides[0], wet), mul(s, wides[1], wet)
    s.c(s.ch(wL, "env~ 4096 2048"), 0, s.obj("v acrvlvl"), 0)
    s.col()
    # the master level x the breath swell (SETUP Breath to swell; 1 otherwise)
    sw = s.obj("line~")
    s.c(s.recv("ac-brsw"), 0, sw, 0)
    s.c(s.m(s.obj("loadbang"), "1"), 0, sw, 0)
    mg = mul(s, s.ch(s.recv("ac-master"), "line~"), sw)
    # the buses: mix (everything else) and bed (drone, sub; the pads and their character join it below)
    cmL, cmR = s.obj("catch~ ac-mixL"), s.obj("catch~ ac-mixR")
    cbL, cbR = s.obj("catch~ ac-bedL"), s.obj("catch~ ac-bedR")
    outs = []
    for cm, cb, p, w in ((cmL, cbL, pdL, wL), (cmR, cbR, pdR, wR)):
        sm = s.obj("hip~ 8")
        for x in (cm, cb, p, w):
            s.c(x, 0, sm, 0)
        outs.append(mul(s, sm, mg))
    comp = s.ch(s.m(s.ch(add(s, outs[0], outs[1]), "env~ 1024 512", "expr pow(10, -max(0, ($f1-82)*0.75)/20)"),
                    "$1 25"), "line~")
    # width: side x ac-width (the section's role x SETUP Width; 0 = SETUP Output mono)
    cL, cR = mul(s, outs[0], comp), mul(s, outs[1], comp)
    mid = s.to(add(s, cL, cR), "*~ 0.5")
    side = s.obj("-~")
    s.c(cL, 0, side, 0)
    s.c(cR, 0, side, 1)
    sw = mul(s, s.to(side, "*~ 0.5"), s.ch(s.recv("ac-width"), "line~"))
    oR = s.obj("-~")
    s.c(mid, 0, oR, 0)
    s.c(sw, 0, oR, 1)
    s.col()
    # SETUP Output split: two mono stems - left the harmony bed (pads with their character, drone, sub), right
    # everything else (bells, motion, textures, cloud, atmosphere, live voices, input). One reverb serves both:
    # each stem takes one side of it (summing its two sides to mono would partly cancel).
    bed = s.obj("*~ 0.5")
    for x in (cbL, cbR, pdL, pdR):
        s.c(x, 0, bed, 0)
    rest = s.obj("*~ 0.5")
    for x in (cmL, cmR):
        s.c(x, 0, rest, 0)
    gain = mul(s, mg, comp)
    stems = [mul(s, s.ch(add(s, st, s.to(w, "*~ 0.7")), "hip~ 8"), gain) for st, w in ((bed, wL), (rest, wR))]
    spl = s.ch(s.recv("ac-split"), "line~")
    nrm = s.ch(spl, "*~ -1", "+~ 1")
    for o, stem, bus in ((add(s, mid, sw), stems[0], "outL"), (oR, stems[1], "outR")):
        fin = add(s, mul(s, o, nrm), mul(s, stem, spl))
        s.c(s.ch(fin, "clip~ -0.98 0.98"), 0, s.obj("throw~ " + bus), 0)
    return s

def motion():
    s, ln = switched("motion", "ac-g-motion")
    s.comment("Motion: Euclidean pulses on chord tones - FM pings with a click, a tempo echo")
    tl = s.to(s.recv("ac-mnote"), "t l b")
    cnt = s.obj("f")
    s.c(tl, 1, cnt, 0)
    s.c(s.ch(cnt, "+ 1", "% 3"), 0, cnt, 1)
    lp = s.obj("list prepend")
    s.c(cnt, 0, lp, 1)
    s.c(tl, 0, lp, 0)
    rt = s.to(lp, "route 0 1 2")
    rat = s.recv("ac-mtimbre")
    t2 = s.to(s.recv("ac-mtimbre2"), "unpack f f")
    L, R = s.obj("*~"), s.obj("*~")
    for j in range(3):
        up = s.to((rt, j), "unpack f f f f")
        pk = s.obj("pack f f f")
        pp = s.obj("pipe f f f 0")
        s.c(up, 2, pp, 3)
        s.c(up, 3, pk, 2)
        s.c(up, 1, pk, 1)
        s.c(up, 0, pk, 0)
        s.c(pk, 0, pp, 0)
        mpn = s.to((pp, 2), "expr cos($f1*1.5708); sin($f1*1.5708)")
        # velocity (the pipe's right outlet fires first): amplitude and FM-index envelopes
        vel = s.to((pp, 1), "t f f")
        ap = s.obj("pack f 500")
        s.c(vel, 1, ap, 0)
        s.c(t2, 1, ap, 1)
        aenv = s.ch(s.m(ap, "$1 4, 0 $2 4"), "vline~")
        iv = s.to((vel, 0), "* 2")
        s.c(t2, 0, iv, 1)
        ienv = s.ch(s.m(iv, "$1, 0 140"), "vline~")
        # pitch: carrier, and a modulator at the piece's ratio
        hz = s.ch((pp, 0), "mtof", "t f f")
        fsig = s.to((hz, 1), "sig~")
        modf = s.to((hz, 0), "* 1")
        s.c(rat, 0, modf, 1)
        dev = mul(s, mul(s, s.to(modf, "osc~"), ienv), fsig)
        car = s.to(add(s, fsig, dev), "osc~")
        sig = mul(s, car, mul(s, aenv, aenv))
        for k, dst in ((0, L), (1, R)):
            m = s.to(sig, "*~ 0.35")
            s.c(mpn, k, m, 1)
            s.c(m, 0, dst, 0)
        s.col(170)
    s.c(ln, 0, L, 1)
    s.c(ln, 0, R, 1)
    # echoes: 3/4 beat left, 1/2 beat right, darkening
    beat = s.to(s.recv("ac-bpm"), "t f f")
    outs = []
    for src, frac, nm in ((L, 0.75, "ac-mdl"), (R, 0.5, "ac-mdr")):
        a = s.obj("+~")
        s.c(src, 0, a, 0)
        s.to(a, f"delwrite~ {nm} 3000")
        rd = s.obj(f"delread~ {nm} 500")
        s.c(s.m(s.to(beat, f"expr 60000/$f1*{frac}"), "$1"), 0, rd, 0)
        s.c(s.ch(rd, "lop~ 2500", "*~ 0.38"), 0, a, 1)
        o = s.obj("+~")
        s.c(src, 0, o, 0)
        s.c(s.to(rd, "*~ 0.6"), 0, o, 1)
        # soft limit: pings stacking with their echoes (fast tempi, dense patterns) stay round, never spike
        outs.append(s.to(o, "expr~ tanh($v1*2.5)/2.5"))
    throws_to("ac-sendm")(s, outs[0], outs[1], mix=1.0, send=0.9)
    return s


# ======================================================================================
# Stage 2: live voices, input chain and analysis, tuned bands, memories
# ======================================================================================

def live_voice():
    """Abstraction amlive.pd (argument = voice 0..3): a played note. With a breath controller, breath is the
    level (and adds brightness); otherwise a velocity envelope. Timbre = one of the 6 pad types."""
    v = Canvas(w=1800, h=1000)
    v.comment("Live voice $1: note, MPE bend, breath; the pad synthesis types; on only while it sounds")
    on = v.to(v.recv("ac-lvon"), "route $1")
    up = v.to(on, "unpack f f")
    c_vel = v.to((up, 1), "t f f")
    # pitch = note + bend: a new note jumps there, a bend glides 20 ms
    ln = v.obj("line 0 20")
    e1, e2 = v.obj("expr $f1 + $f2"), v.obj("expr $f1 + $f2")
    nt = v.to((up, 0), "t f f")
    v.c(nt, 1, e2, 1)
    v.c(nt, 0, e1, 0)
    bt = v.ch(v.recv("ac-lvbend"), "route $1", "t f f")
    v.c(bt, 1, e1, 1)
    v.c(bt, 0, e2, 0)
    v.c(v.m(e1, "$1"), 0, ln, 0)
    v.c(v.m(e2, "$1 20"), 0, ln, 0)
    tf = v.to(ln, "t f f")
    dsig = v.ch(v.m(v.to((tf, 1), "expr 1000/mtof($f1) - 0.012"), "$1 20"), "line~")
    fsig0 = v.ch(v.m(v.to((tf, 0), "mtof"), "$1 20"), "line~")
    # vibrato (SETUP CC MAP: a CC to vibrato sets the depth, up to about half a semitone; Vib rate the speed)
    vr = v.obj("osc~ 5.5")
    v.c(v.recv("ac-lvvibr"), 0, vr, 0)
    vd = v.ch(v.m(v.recv("ac-lvvib"), "$1 50"), "line~")
    fsig = mul(v, fsig0, v.to(mul(v, v.to(vr, "*~ 0.03"), vd), "+~ 1"))
    v.col()
    # envelope: velocity level (or 1 with a breath controller), attack 60 ms, decay to 85 %, release 1.4 s
    brm = v.recv("ac-brmode")
    lev = v.obj("expr if($f2, 1, $f1); if($f2, 1, $f1)*0.85")
    v.c(brm, 0, lev, 1)
    v.c(c_vel, 1, lev, 0)
    lp = v.obj("pack f f")
    v.c(lev, 1, lp, 1)
    v.c(lev, 0, lp, 0)
    gate = v.ch(v.m(lp, "$1 60, $2 400 60"), "vline~")
    off = v.to(v.recv("ac-lvoff"), "route $1")
    v.c(v.m(off, "0 1400"), 0, gate, 0)
    # breath (1 when there is no breath controller)
    br = v.obj("line~")
    brlast = v.obj("f 1")              # the latest breath, so the voice wakes at it (no ramp from an old value)
    brin = v.ch(v.recv("ac-lvbr"), "route $1", "t f f")
    v.c(brin, 1, brlast, 1)
    v.c(v.m(brin, "$1 15"), 0, br, 0)
    brm0 = v.ch(brm, "sel 0", "t b b")
    v.c(v.m((brm0, 1), "1"), 0, brlast, 1)
    v.c(v.m(brm0, "1 50"), 0, br, 0)
    v.c(v.m(v.obj("loadbang"), "1"), 0, br, 0)
    v.c(v.m(brlast, "$1"), 0, br, 0)
    # per-note tone and level (SETUP CC MAP: voice tone, voice level; MPE per channel)
    tim = v.obj("line~")
    v.c(v.m(v.ch(v.recv("ac-lvtim"), "route $1"), "$1 20"), 0, tim, 0)
    lv = v.obj("line~")
    v.c(v.m(v.ch(v.recv("ac-lvlev"), "route $1"), "$1 20"), 0, lv, 0)
    v.c(v.m(v.obj("loadbang"), "1"), 0, lv, 0)
    v.c(v.m(v.obj("loadbang"), "0.5"), 0, tim, 0)
    amp = mul(v, mul(v, gate, br), lv)
    bright = v.ch(add(v, add(v, v.ch(v.recv("ac-bright"), "line~"), v.to(br, "*~ 0.3")), v.ch(tim, "-~ 0.5", "*~ 1.2")),
                  "clip~ 0 1")
    v.col()
    # the synthesis type: on (10 ms) at a note-on, all off 1.6 s after the release
    ty = v.obj("f")
    v.c(v.recv("ac-lvtype"), 0, ty, 1)
    from gen_sounds import NEW_FLAVS
    nf = 6 + len(NEW_FLAVS)
    st = v.to(ty, "t " + " ".join(["f"] * nf))
    for i in range(nf):
        v.c(v.m(v.to((st, i), f"== {i}"), "$1 10"), 0, v.obj(f"s $0-fw{i}"), 0)
    d = v.obj("delay 1600")
    v.c(off, 0, d, 0)
    v.c(v.m(c_vel, "stop"), 0, d, 0)
    tb = v.to((c_vel, 0), "t b b")
    v.c(tb, 0, ty, 0)
    for i in range(nf):
        v.c(v.m(d, "0 50"), 0, v.obj(f"s $0-fw{i}"), 0)
    # the whole voice computes only while it sounds: on at a note-on, off 1.75 s after the release
    vsw = v.obj("switch~")
    v.c(v.m(v.obj("loadbang"), "0"), 0, vsw, 0)
    v.c(v.m((tb, 1), "1"), 0, vsw, 0)
    v.c((tb, 1), 0, brlast, 0)
    d2 = v.obj("delay 150")
    v.c(d, 0, d2, 0)
    v.c(v.m((tb, 1), "stop"), 0, d2, 0)
    v.c(v.m(d2, "0"), 0, vsw, 0)
    lb = v.ch(v.obj("loadbang"), "f $1")
    v.c(v.to(lb, "expr 0.11 + 0.03*$f1"), 0, v.obj("s $0-la"), 0)
    v.c(v.to(lb, "expr 0.07 + 0.02*$f1"), 0, v.obj("s $0-lb"), 0)
    v.col()
    bodyL, bodyR = v.obj("*~"), v.obj("*~")
    v.c(amp, 0, bodyL, 1)
    v.c(amp, 0, bodyR, 1)
    v.c(v.obj("catch~ $0-bL"), 0, bodyL, 0)
    v.c(v.obj("catch~ $0-bR"), 0, bodyR, 0)
    for i, fl in enumerate((flav_fm(), flav_vox(), flav_bow(), flav_part(), flav_fold(), flav_pulsar())
                           + tuple(f() for f in NEW_FLAVS)):
        sp = v.sub(fl, 20 + i * 120, 760)
        v.c(fsig, 0, sp, 0)
        v.c(bright, 0, sp, 1)
        if fl.name == "bow":
            v.c(dsig, 0, sp, 2)
            v.c((sp, 0), 0, bodyL, 0)
            v.c((sp, 1), 0, bodyR, 0)
    home = v.ch(v.obj("loadbang"), "f $1", "expr 0.2 + 0.2*$f1")
    orb = v.to(v.ch(v.obj("loadbang"), "f $1", "expr 0.05 + 0.017*$f1"), "osc~")
    dep = v.to(orb, "*~ 0.06")
    v.c(v.to(v.recv("ac-pandepth"), "* 0.4"), 0, dep, 1)
    posn = v.to(dep, "+~ 0.5")
    v.c(home, 0, posn, 1)
    q = v.ch(posn, "clip~ 0.02 0.98", "*~ 0.25")
    gl = v.ch(q, "cos~", "*~ 1.414", "clip~ 0 1")
    gr = v.ch(q, "-~ 0.25", "cos~", "*~ 1.414", "clip~ 0 1")
    L = mul(v, v.to(bodyL, "*~ 0.42"), gl)
    R = mul(v, v.to(bodyR, "*~ 0.42"), gr)
    throws_to("ac-sendp")(v, L, R, mix=1.0, send=0.6, src=0.5)
    return v


def pitch_tracker(src_canvas, src):
    """FFT autocorrelation pitch tracker (vanilla), at half rate (22.05 kHz): 2048-point blocks, 1024 windowed
    samples (zero padded), hop 1024 (46 ms). Lag 20..300 (73 Hz - 1.1 kHz), parabolic interpolation.
    -> acinp (MIDI, -1 = none), acinclr. Switched off (ac-trk 0) while the In knob is at 0."""
    p = Canvas("pitch", w=1400)
    p.comment("autocorrelation by FFT: |X|^2 -> inverse FFT; the strongest lag in 20..300 is the period")
    tsw = p.obj("switch~ 2048 2 0.5")
    p.c(p.ch(p.obj("loadbang"), "f 0"), 0, tsw, 0)
    p.c(p.recv("ac-trk"), 0, tsw, 0)
    x = p.obj("inlet~", 20, 5)
    w = mul(p, x, p.obj("tabreceive~ achann"))
    ff = p.to(w, "rfft~")
    pw = add(p, mul(p, (ff, 0), (ff, 0)), mul(p, (ff, 1), (ff, 1)))
    p.c(p.to(pw, "rifft~"), 0, p.obj("tabsend~ acacf"), 0)
    p.col()
    bg = p.obj("bang~")
    from pdlib import run_steps, X
    mx = p.obj("array max acacf 20 280")
    p.c(bg, 0, mx, 0)
    pk = p.obj("pack f f")
    p.c(mx, 1, pk, 1)
    p.c(mx, 0, pk, 0)
    e = p.to(pk, "expr $f2; $f1/max(1e-09, acacf[0])")
    p.c(e, 1, p.obj("v acinclr"), 0)
    tb = p.to(e, "t b f")
    p.c(tb, 1, p.obj("v aci2"), 0)
    y0, y1, y2 = "acacf[int(aci2)-1]", "acacf[int(aci2)]", "acacf[int(aci2)+1]"
    den = f"({y0} - 2*{y1} + {y2})"
    run_steps(p, (tb, 0), [X(f"if(acinclr > 0.35 && acinlvl > 48, ftom(22050/(aci2 + max(-1, min(1, if({den} < -1e-09, "
                             f"0.5*({y0} - {y2})/{den}, 0))))), -1)", "v acinp")])
    sp = src_canvas.sub(p)
    src_canvas.c(src, 0, sp, 0)
    return sp


def inp():
    s = Canvas("input", w=2000)
    s.comment("External audio: dry blend; gate + automatic gain -> ac-in (resonators, bands, tape, cloud, memories); "
              "level, brightness, pitch and onsets for the listener")
    iL, iR = s.obj("r~ inL"), s.obj("r~ inR")
    mono = s.ch(add(s, iL, iR), "*~ 0.5", "hip~ 50")
    dry = s.ch(s.recv("ac-g-dry"), "line~")
    for sig, bus in ((iL, "ac-mixL"), (iR, "ac-mixR")):
        s.c(mul(s, sig, dry), 0, s.obj("throw~ " + bus), 0)
    # the dry input into the reverb too (SENDS 2, Inp)
    s.c(s.to(mul(s, mono, dry), "*~ 0.3"), 0, s.obj("throw~ ac-sendi"), 0)
    s.col()
    lvl = s.ch(mono, "env~ 2048 1024", "t f f f")
    s.c(lvl, 2, s.obj("v acinlvl"), 0)
    # automatic gain towards -22 dBFS (+24 / -12 dB), gate below -55 dBFS
    agc = s.ch((lvl, 1), "expr if($f1 > 45, pow(10, min(24, max(-12, 78 - $f1))/20), 0)")
    agcs = s.obj("expr $f1*0.25 + $f2*0.75")
    s.c(agc, 0, agcs, 0)
    sm = s.obj("f")
    s.c(agcs, 0, sm, 0)
    s.c(sm, 0, agcs, 1)
    g = s.ch(s.m(agcs, "$1 300"), "line~")
    ain = mul(s, mono, g)
    s.c(ain, 0, s.obj("s~ ac-in"), 0)
    hf = s.ch(mono, "hip~ 3000", "env~ 2048 1024")
    hd = s.obj("expr $f1 - acinlvl")
    s.c(hf, 0, hd, 0)
    s.c(hd, 0, s.obj("v acinhf"), 0)
    pitch_tracker(s, s.ch(ain, "lop~ 5000", "lop~ 6000"))     # band-limit before the half-rate tracker
    s.col()
    s.c(s.recv("ac-ghost"), 0, s.obj("v acghost"), 0)
    env = s.to((lvl, 0), "expr max(0, min(1, ($f1-45)/40))")
    te = s.to(env, "t f f f")
    s.c(s.ch(s.m(s.to((te, 2), "expr $f1*acghost"), "$1 50"), "line~"), 0, s.obj("s~ ac-envb"), 0)
    ons = s.ch((te, 1), "expr $f1 - acinprev > 0.12 && $f1 > 0.25", "sel 1")
    s.c(te, 0, s.obj("v acinprev"), 0)
    sp = s.obj("spigot 1")
    s.c(ons, 0, sp, 0)
    tb = s.to(sp, "t b b")
    s.c(tb, 0, s.obj("s ac-inonset"), 0)
    s.c(s.m((tb, 1), "0"), 0, sp, 1)
    s.c(s.m(s.to((tb, 1), "delay 150"), "1"), 0, sp, 1)
    return s


def bands():
    s, ln = switched("bands", "ac-g-bands")
    s.comment("Tuned bands: the input through 8 narrow resonant bands on the chord (field recordings play it)")
    src = s.obj("r~ ac-in")
    L, R = s.obj("*~ 8"), s.obj("*~ 8")
    for k in range(8):
        v = s.obj("vcf~ 28")
        s.c(src, 0, v, 0)
        s.c(s.ch(s.recv(f"ac-band{k}"), "line~"), 0, v, 1)
        s.c(v, 0, L if k % 2 == 0 else R, 0)
    throws_to("ac-sendi")(s, mul(s, L, ln), mul(s, R, ln), mix=1.0, send=0.7, src=0.3)
    return s


def mem_rec():
    s = Canvas("memory-rec", w=1000)
    s.comment("Records 8 s of ac-in into memory slot N")
    tw = s.obj("tabwrite~ acmem0")
    s.c(s.obj("r~ ac-in"), 0, tw, 0)
    sel = s.to(s.recv("ac-memrecslot"), "sel 0 1 2 3")
    for i in range(4):
        s.c(s.m((sel, i), f"set acmem{i}, bang"), 0, tw, 0)
    return s


def mem_play():
    s, ln = switched("memory-play", "ac-g-mem")
    s.comment("Plays a memory back, transformed: two heads at a rate and half of it (an octave below), each "
              "8 s cycle faded in and out")
    up = s.to(s.recv("ac-memplay"), "unpack f f")
    sel = s.to(up, "sel 0 1 2 3")
    L, R = s.obj("*~ 0.8"), s.obj("*~ 0.8")
    for h, (mult, dst) in enumerate(((1, L), (0.5, R))):
        ph = s.obj("phasor~")
        s.c(s.to((up, 1), f"expr $f1*{mult}/8"), 0, ph, 0)
        rd = s.obj("tabread4~ acmem0")
        for i in range(4):
            s.c(s.m((sel, i), f"set acmem{i}"), 0, rd, 0)
        s.c(s.to(ph, f"*~ {CLOUD_LEN - 4}"), 0, rd, 0)
        win = s.ch(ph, "cos~", "*~ -0.5", "+~ 0.5")
        s.c(mul(s, rd, win), 0, dst, 0)
    throws_to("ac-sendi")(s, mul(s, L, ln), mul(s, R, ln), mix=0.7, send=1.0)
    return s
