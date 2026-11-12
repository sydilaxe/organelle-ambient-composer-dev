"""Sound: pad voices (5 synthesis types), drone, textures, granular cloud, bells, input processing,
FDN reverb and the master stage.

Buses (throw~/catch~): ac-mixL/R dry mix, ac-padL/R the pad voices, ac-send reverb input (mono),
ac-src what the cloud resamples. Every layer that can be silent sits in a switch~ed subpatch."""
from pdlib import Canvas
from data import REVERB_MS, CLOUD_LEN


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


def throws(c, L, R, mix=1.0, send=0.0, src=0.0):
    for sig, bus in ((L, "ac-mixL"), (R, "ac-mixR")):
        c.c(c.to(sig, f"*~ {mix}"), 0, c.obj("throw~ " + bus), 0)
    if send or src:
        m = add(c, L, R)
        if send:
            c.c(c.to(m, f"*~ {send * 0.5}"), 0, c.obj("throw~ ac-send"), 0)
        if src:
            c.c(c.to(m, f"*~ {src * 0.5}"), 0, c.obj("throw~ ac-src"), 0)


def pan(c, sig, l, r):
    return c.to(sig, f"*~ {l}"), c.to(sig, f"*~ {r}")


# ======================================================================================
# Pad voice abstraction (acvoice.pd, argument = voice 0..3)
# ======================================================================================

def _flav_inlets(s, n):
    return [s.obj("inlet~", 20 + i * 140, 5) for i in range(n)]


def _out(s, sig, ln):
    s.c(mul(s, sig, ln), 0, s.obj("outlet~", 20, 980), 0)


def flav_fm():
    s, ln = switched("fm", "$0-fw0")
    s.comment("FM: a modulator at a per-piece ratio; index follows brightness and Weird")
    f, b = _flav_inlets(s, 2)
    rat = s.to(f, "*~ 1")
    s.c(s.recv("ac-fmr"), 0, rat, 1)
    mo = s.to(rat, "osc~")
    ix = s.ch(b, "*~ 2.2", "+~ 0.15")
    w = s.to(ix, "*~ 1")
    ctl(s, w, "ac-weird", "0.5 + 1.5*$f1")
    car = s.ch(add(s, f, mul(s, mul(s, mo, w), f)), "osc~", "*~ 0.42")
    _out(s, car, ln)
    return s


def flav_vox():
    s, ln = switched("vox", "$0-fw1")
    s.comment("Vox: a saw through two drifting vowel formants")
    f, b = _flav_inlets(s, 2)
    saw = s.ch(f, "phasor~", "-~ 0.5")
    cf1 = s.ch(s.recv("$0-la"), "osc~", "*~ 0.5", "+~ 0.5", "*~ 450", "+~ 280")
    cf2 = s.ch(s.recv("$0-lb"), "osc~", "*~ 0.5", "+~ 0.5", "*~ 1000", "+~ 900")
    v1 = s.obj("vcf~ 7")
    v2 = s.obj("vcf~ 10")
    for v, cf in ((v1, cf1), (v2, cf2)):
        s.c(saw, 0, v, 0)
        s.c(cf, 0, v, 1)
    sm = s.obj("+~")
    s.c(v1, 0, sm, 0)
    s.c(s.to(v2, "*~ 0.7"), 0, sm, 0)
    s.c(s.ch(saw, "lop~ 600", "*~ 0.2"), 0, sm, 0)
    bm = s.ch(b, "*~ 0.8", "+~ 0.35")
    _out(s, s.to(mul(s, sm, bm), "*~ 2.2"), ln)
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
    _out(s, s.ch(vd, "hip~ 40", "*~ 9"), ln)
    return s


def flav_part():
    s, ln = switched("part", "$0-fw3")
    s.comment("Partials: 4 sines at per-piece ratios, each swelling on its own, tilted by brightness")
    f, b = _flav_inlets(s, 2)
    up = s.to(s.recv("ac-partials"), "unpack f f f")
    lt = s.to(s.recv("$0-lb"), "t f f f f")
    b2 = mul(s, b, b)
    b3 = mul(s, b2, b)
    tilt = [None, b, b2, b3]
    sm = s.obj("*~ 0.3")
    for k in range(4):
        if k == 0:
            o = s.to(f, "osc~")
        else:
            r = s.to(f, f"*~ {k + 1}")
            s.c(up, k - 1, r, 1)
            o = s.to(r, "osc~")
        amp = s.ch((lt, k), f"* {[1, 1.37, 1.71, 2.13][k]}", "osc~", "*~ 0.5", "+~ 0.5")
        p = mul(s, o, amp)
        if tilt[k] is not None:
            p = mul(s, p, tilt[k])
        s.c(p, 0, sm, 0)
    _out(s, sm, ln)
    return s


def flav_fold():
    s, ln = switched("fold", "$0-fw4")
    s.comment("Fold: a sine wavefolded (sin of a driven sine), ring-modulated by its sub-octave")
    f, b = _flav_inlets(s, 2)
    x = s.to(f, "osc~")
    dr = s.ch(b, "*~ 4", "+~ 0.5", "*~ 1")
    ctl(s, dr, "ac-weird", "0.3 + 1.2*$f1")
    u = s.ch(mul(s, x, dr), "*~ 0.25", "-~ 0.25", "cos~", "hip~ 20")
    sub = s.ch(f, "*~ 0.5", "osc~", "*~ 0.22", "+~ 0.78")
    _out(s, s.ch(mul(s, u, sub), "lop~ 5000", "*~ 0.32"), ln)
    return s


def flav_pulsar():
    s, ln = switched("pulsar", "$0-fw5")
    s.comment("Pulsar: each period starts a short windowed burst of a few sine cycles; the burst length "
              "follows a drifting formant, so the voice speaks somewhere between insect and choir")
    f, b = _flav_inlets(s, 2)
    form = s.ch(s.recv("$0-la"), "* 0.7", "osc~", "*~ 0.5", "+~ 0.5")
    fsig = s.to(add(s, s.to(form, "*~ 900"), s.to(b, "*~ 1400")), "+~ 450")
    k = s.obj("/~")
    s.c(fsig, 0, k, 0)
    s.c(f, 0, k, 1)
    u = s.ch(mul(s, s.to(f, "phasor~"), s.to(k, "max~ 1")), "clip~ 0 1")
    win = s.ch(u, "cos~", "*~ -0.5", "+~ 0.5")
    car = s.ch(u, "*~ 3", "cos~")
    _out(s, s.ch(mul(s, win, car), "hip~ 30", "*~ 0.75"), ln)
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
    ft = v.to(v.recv("ac-v$1-flav"), "t f f f f f f")
    for i in range(6):
        v.c(v.m(v.to((ft, i), f"== {i}"), "$1 4000"), 0, v.obj(f"s $0-fw{i}"), 0)
    v.col()
    body = v.obj("*~")
    v.c(amp, 0, body, 1)
    for i, fl in enumerate((flav_fm(), flav_vox(), flav_bow(), flav_part(), flav_fold(), flav_pulsar())):
        sp = v.sub(fl, 20 + i * 120, 700)
        v.c(f2, 0, sp, 0)
        v.c(bsig, 0, sp, 1)
        if fl.name == "bow":
            v.c(dsig, 0, sp, 2)
        v.c(sp, 0, body, 0)
    out = v.to(body, "*~ 0.2")
    pn = v.ch(v.obj("loadbang"), "f $1", "expr cos((0.12+0.25*$f1)*1.5708); sin((0.12+0.25*$f1)*1.5708)")
    for i, bus in ((0, "ac-padL"), (1, "ac-padR")):
        m = v.to(out, "*~ 0.7")
        v.c(pn, i, m, 1)
        v.c(m, 0, v.obj("throw~ " + bus), 0)
    return v


# ======================================================================================
# Main patch layers
# ======================================================================================

def drone():
    s, ln = switched("drone", "ac-g-drone")
    s.comment("Drone on the tonic: root, a beating twin, a per-piece interval, sub, and a breathing tube")
    f = s.ch(s.m(s.ch(s.recv("ac-dronep"), "line 0 40", "mtof"), "$1 40"), "line~")
    sm = s.obj("lop~ 1000")
    ctl(s, sm, "ac-bright", "350 + 3500*$f1", first=True)
    s.c(s.ch(f, "osc~", "*~ 0.26"), 0, sm, 0)
    s.c(s.ch(f, "*~ 1.0035", "osc~", "*~ 0.13"), 0, sm, 0)
    iv = s.to(f, "*~ 1.5")
    s.c(s.recv("ac-dint"), 0, iv, 1)
    s.c(mul(s, s.to(iv, "osc~"), s.ch(s.obj("osc~ 0.031"), "*~ 0.06", "+~ 0.1")), 0, sm, 0)
    s.c(s.ch(f, "*~ 0.5", "osc~", "*~ 0.2"), 0, sm, 0)
    harm = s.ch(s.recv("ac-dharm"), "line~")
    tube = s.obj("vcf~ 40")
    s.c(s.obj("noise~"), 0, tube, 0)
    s.c(mul(s, f, harm), 0, tube, 1)
    s.c(mul(s, s.to(tube, "*~ 5"), s.ch(s.obj("osc~ 0.023"), "*~ 0.5", "+~ 0.5")), 0, sm, 0)
    o = mul(s, s.to(sm, "hip~ 25"), ln)
    throws(s, o, o, mix=0.6, send=0.3, src=1)
    return s


def tex_rain():
    s, ln = switched("rain", "ac-g-tex0")
    s.comment("Rain: water-drop bubbles (a sine whose pitch rises as it dies) on chord tones")
    rt = s.to(s.recv("ac-drop"), "route 0 1 2")
    L, R = s.obj("*~"), s.obj("*~")
    s.c(ln, 0, L, 1)
    s.c(ln, 0, R, 1)
    for i in range(3):
        up = s.to((rt, i), "unpack f f")
        pn = s.to((up, 1), "expr cos($f1*1.5708); sin($f1*1.5708)")
        tf = s.ch((up, 0), "mtof", "t f f")
        env = s.ch(s.m(s.to((tf, 1), "expr 90 + 30000/$f1"), "0.9, 0 $1"), "vline~")
        ex = s.to((tf, 0), "expr $f1*0.7; $f1")
        pk = s.obj("pack f f")
        s.c(ex, 1, pk, 1)
        s.c(ex, 0, pk, 0)
        fr = s.ch(s.m(pk, "$1, $2 40"), "vline~")
        sig = mul(s, s.to(fr, "osc~"), mul(s, env, env))
        for k, dst in ((0, L), (1, R)):
            m = s.to(sig, "*~ 0.5")
            s.c(pn, k, m, 1)
            s.c(m, 0, dst, 0)
        s.col(160)
    throws(s, L, R, mix=0.13, send=0.3)
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
    L, R = s.obj("*~ 0.5"), s.obj("*~ 0.5")
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
        s.c(g, 0, L if i % 2 == 0 else R, 0)
        s.col(160)
    throws(s, mul(s, L, ln), mul(s, R, ln), mix=0.85, send=1.2)
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
        up = s.to((rt, j), "unpack f f")
        mf = s.to((up, 0), "mtof")
        sm = s.obj("*~ 1")
        for k, (amp, dec) in enumerate(((0.32, 5200), (0.15, 2600), (0.08, 1100))):
            fr = s.to(mf, "* 1")
            s.c(bs, k, fr, 1)
            env = s.ch(s.m(s.to((up, 1), f"* {amp}"), f"$1, 0 {dec}"), "vline~")
            s.c(mul(s, s.to(fr, "osc~"), mul(s, env, env)), 0, sm, 0)
        s.c(s.to(sm, f"*~ {0.85 if j == 0 else 0.45}"), 0, L, 0)
        s.c(s.to(sm, f"*~ {0.45 if j == 0 else 0.85}"), 0, R, 0)
        s.col(160)
    throws(s, L, R, mix=1.1, send=1.0)
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
    throws(s, mul(s, s.to(L, "*~ 0.12"), ln), mul(s, s.to(R, "*~ 0.12"), ln), mix=1, send=0.6)
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
    throws(s, mul(s, s.to(taps[0], "lop~ 3500"), ln), mul(s, s.to(taps[1], "lop~ 3000"), ln), mix=0.5, send=0.4)
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
    pm = add(s, pL, pR)
    rin = s.obj("*~ 0.35")
    s.c(s.obj("catch~ ac-send"), 0, rin, 0)
    s.c(s.to(pm, "*~ 0.3"), 0, rin, 0)
    rs = s.obj("s~ ac-resamp")
    s.c(s.obj("catch~ ac-src"), 0, rs, 0)
    s.c(s.to(pm, "*~ 0.5"), 0, rs, 0)
    s.col()
    x = allpass(s, allpass(s, rin, "ac-ap1", 11.3, 0.6), "ac-ap2", 4.7, 0.6)
    S = s.obj("*~ -0.5")
    damps, ys = [], []
    for i, ms in enumerate(REVERB_MS):
        a = s.obj("+~")
        s.c(s.to(x, f"*~ {[1, -1, 1, -1][i]}"), 0, a, 0)
        s.to(a, f"delwrite~ ac-fdn{i} 300")
        if i in (0, 2):
            d = s.obj(f"delread4~ ac-fdn{i}")
            s.c(s.ch(s.obj(f"osc~ {0.13 + 0.07 * i}"), "*~ 1.3", f"+~ {ms}"), 0, d, 0)
        else:
            d = s.obj(f"delread~ ac-fdn{i} {ms}")
        dm = s.to(d, "lop~ 4200")
        s.c(dm, 0, S, 0)
        y = s.obj("+~")
        s.c(dm, 0, y, 0)
        s.c(S, 0, y, 1)
        g = s.to(y, "*~ 0.9")
        s.c(s.recv(f"ac-rg{i}"), 0, g, 1)
        s.c(g, 0, a, 1)
        ys.append(y)
        s.col(150)
    wet = s.ch(s.recv("ac-rwet"), "line~")
    wL = mul(s, add(s, ys[0], ys[2]), wet)
    wR = mul(s, add(s, ys[1], ys[3]), wet)
    s.col()
    mg = s.ch(s.recv("ac-master"), "line~")
    outs = []
    for bus, p, w in (("ac-mixL", pL, wL), ("ac-mixR", pR, wR)):
        sm = s.obj("hip~ 8")
        s.c(s.obj("catch~ " + bus), 0, sm, 0)
        s.c(p, 0, sm, 0)
        s.c(w, 0, sm, 0)
        outs.append(mul(s, sm, mg))
    comp = s.ch(s.m(s.ch(add(s, outs[0], outs[1]), "env~ 1024 512", "expr pow(10, -max(0, ($f1-82)*0.75)/20)"),
                    "$1 25"), "line~")
    for o, bus in zip(outs, ("outL", "outR")):
        s.c(s.ch(mul(s, o, comp), "clip~ -0.98 0.98"), 0, s.obj("throw~ " + bus), 0)
    return s
