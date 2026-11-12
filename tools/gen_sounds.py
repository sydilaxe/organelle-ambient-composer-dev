"""More sounds: electric / synthetic pad types, drone designs, the sub, electric textures, per-piece character
(chorus, tape, ring, crush) on the pads, and the vocoder (input speaks through a synth choir or the pads)."""
from pdlib import Canvas
from gen_dsp import switched, mul, add, ctl, throws, _flav_inlets, _out


# ---------------------------------------------------------------- pad types 6..9 (inlets: freq~, bright~)
def flav_saws():
    s, ln = switched("saws", "$0-fw6")
    s.comment("Saws: three detuned saws (an analog ensemble) through a resonant low-pass that tracks the note")
    f, b = _flav_inlets(s, 2)
    sm = s.obj("*~ 0.33")
    for d in (0.994, 1.0, 1.0065):
        s.c(s.ch(s.to(f, f"*~ {d}"), "phasor~", "-~ 0.5"), 0, sm, 0)
    cf = s.to(mul(s, f, s.ch(b, "*~ 9", "+~ 1.5")), "clip~ 40 5500")
    v = s.obj("vcf~ 1.6")
    s.c(sm, 0, v, 0)
    s.c(cf, 0, v, 1)
    _out(s, s.ch((v, 1), "hip~ 30", "*~ 2.8"), ln)
    return s


def flav_pwm():
    s, ln = switched("pwm", "$0-fw7")
    s.comment("PWM: a pulse whose width breathes, through a slowly sweeping resonant filter (a Juno-like string)")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    w = s.ch(s.recv("$0-la"), "* 1.7", "osc~", "*~ 0.35", "+~ 0.5")
    p2 = s.to(add(s, ph, w), "wrap~")
    pulse = s.obj("-~")
    s.c(ph, 0, pulse, 0)
    s.c(p2, 0, pulse, 1)
    sweep = s.ch(s.recv("$0-lb"), "osc~", "*~ 0.5", "+~ 0.5")
    cf = s.to(mul(s, f, add(s, s.to(sweep, "*~ 4"), s.ch(b, "*~ 5", "+~ 1.2"))), "clip~ 40 5000")
    v = s.obj("vcf~ 2.5")
    s.c(s.to(pulse, "hip~ 20"), 0, v, 0)
    s.c(cf, 0, v, 1)
    _out(s, s.to((v, 1), "*~ 0.75"), ln)
    return s


def flav_digi():
    s, ln = switched("digi", "$0-fw8")
    s.comment("Digi: a sine ring-modulated at an inharmonic ratio, then bit-crushed and sample-rate reduced")
    f, b = _flav_inlets(s, 2)
    car = s.to(f, "osc~")
    rr = s.to(f, "*~ 1.4142")
    s.c(s.recv("ac-fmr"), 0, rr, 1)
    ring = mul(s, car, s.to(rr, "osc~"))
    x = add(s, s.to(car, "*~ 0.6"), s.to(ring, "*~ 0.5"))
    # crush: quantise to L levels, L = 6..40 (fewer with Weird)
    lv = s.obj("*~ 16")
    s.c(x, 0, lv, 0)
    ctl(s, lv, "ac-weird", "40 - 34*$f1")
    q = s.obj("-~")
    s.c(lv, 0, q, 0)
    s.c(s.to(lv, "wrap~"), 0, q, 1)
    inv = s.obj("/~ 16")
    s.c(q, 0, inv, 0)
    ctl(s, inv, "ac-weird", "40 - 34*$f1")
    # decimate: hold at 3-11 kHz (brightness)
    hold = s.obj("samphold~")
    s.c(inv, 0, hold, 0)
    s.c(s.to(s.ch(b, "*~ 8000", "+~ 3000"), "phasor~"), 0, hold, 1)
    _out(s, s.ch(hold, "lop~ 7000", "hip~ 20", "*~ 0.5"), ln)
    return s


def flav_sync():
    s, ln = switched("sync", "$0-fw9")
    s.comment("Sync: a hard-synced saw whose slave ratio sweeps (brightness and a slow LFO) - an electric lead")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    ratio = add(s, s.ch(b, "*~ 3", "+~ 1.3"), s.ch(s.recv("$0-lb"), "* 1.3", "osc~", "*~ 0.6"))
    sl = s.ch(mul(s, ph, ratio), "wrap~", "-~ 0.5")
    # soften the reset with the master's own fall (an amplitude ramp hides the jump)
    win = s.ch(ph, "*~ -1", "+~ 1")
    _out(s, s.ch(mul(s, sl, win), "lop~ 4500", "hip~ 30", "*~ 1.1"), ln)
    return s


NEW_FLAVS = (flav_saws, flav_pwm, flav_digi, flav_sync)


# ---------------------------------------------------------------- drone designs 1..3 (0 is the original)
def _drone_freq(s):
    return s.ch(s.m(s.ch(s.recv("ac-dronep"), "line 0 40", "mtof"), "$1 40"), "line~")


def _drone_out(s, sig, ln):
    o = mul(s, s.to(sig, "hip~ 25"), ln)
    throws(s, o, o, mix=0.6, send=0.3, src=1)


def drone_analog():
    s, ln = switched("drone-analog", "ac-g-drone1")
    s.comment("Analog drone: two saws and a square an octave down through a slow resonant sweep")
    f = _drone_freq(s)
    sm = s.obj("*~ 0.3")
    for d in (1.0, 1.0042):
        s.c(s.ch(s.to(f, f"*~ {d}"), "phasor~", "-~ 0.5"), 0, sm, 0)
    sq = s.ch(s.to(f, "*~ 0.5"), "phasor~", "-~ 0.5", "*~ 1000", "clip~ -0.25 0.25")
    s.c(sq, 0, sm, 0)
    sweep = s.ch(s.obj("osc~ 0.021"), "*~ 0.5", "+~ 0.5")
    br = s.ch(s.recv("ac-bright"), "line~")
    cf = s.to(mul(s, f, add(s, s.to(mul(s, sweep, br), "*~ 10"), s.obj("sig~ 1.5"))), "clip~ 40 4000")
    v = s.obj("vcf~ 3")
    s.c(sm, 0, v, 0)
    s.c(cf, 0, v, 1)
    _drone_out(s, s.to((v, 1), "*~ 2.4"), ln)
    return s


def drone_organ():
    s, ln = switched("drone-organ", "ac-g-drone2")
    s.comment("Organ drone: drawbar partials 1 2 3 4 6 8 with a slow rotary shimmer")
    f = _drone_freq(s)
    sm = s.obj("*~ 1")
    for h, a in ((1, 0.22), (2, 0.16), (3, 0.1), (4, 0.07), (6, 0.04), (8, 0.03)):
        s.c(s.ch(s.to(f, f"*~ {h}"), "osc~", f"*~ {a}"), 0, sm, 0)
    rot = s.ch(s.obj("osc~ 0.8"), "*~ 0.18", "+~ 0.82")
    _drone_out(s, mul(s, sm, rot), ln)
    return s


def drone_fm():
    s, ln = switched("drone-fm", "ac-g-drone3")
    s.comment("FM drone: an electric growl, the index cycling slowly; a little noise in the attack band")
    f = _drone_freq(s)
    idx = s.ch(s.obj("osc~ 0.037"), "*~ 1.5", "+~ 2")
    mo = mul(s, mul(s, s.to(f, "osc~"), idx), f)
    car = s.to(add(s, f, mo), "osc~")
    _drone_out(s, s.ch(car, "lop~ 1800", "*~ 0.3"), ln)
    return s


NEW_DRONES = (drone_analog, drone_organ, drone_fm)


def sub():
    s, ln = switched("sub", "ac-g-sub")
    s.comment("Sub: a sine under everything - the pedal an octave under the tonic, or the chord root as a bass "
              "line - softly saturated so small speakers hear its harmonics; swells with the bar pulse")
    f = s.ch(s.recv("ac-subp"), "line~")
    x = s.to(f, "osc~")
    sat = s.ch(x, "*~ 1.8", "clip~ -1 1")
    y = add(s, s.to(x, "*~ 0.6"), s.to(sat, "*~ 0.25"))
    env = s.ch(s.m(s.to(s.recv("ac-dpulse"), "expr max(100, $f1-450)"), "1 450, 0 $1 450"), "vline~")
    dep = s.to(env, "*~ 0")
    pu = s.to(s.recv("ac-pulse"), "t f f")
    s.c(pu, 1, dep, 1)
    pa = s.to(dep, "+~ 1")
    s.c(s.to((pu, 0), "expr 1-$f1"), 0, pa, 1)
    o = mul(s, mul(s, s.to(y, "lop~ 500"), pa), ln)
    throws(s, o, o, mix=0.42, send=0.05)
    return s


# ---------------------------------------------------------------- electric textures 4..6
def tex_radio():
    s, ln = switched("radio", "ac-g-tex4")
    s.comment("Radio: band-limited static that comes and goes, and a heterodyne whistle drifting near a chord tone")
    st = s.ch(s.obj("noise~"), "hip~ 1200", "lop~ 3500")
    gate = s.ch(s.obj("noise~"), "lop~ 2", "*~ 60", "clip~ 0 1")
    stat = mul(s, st, gate)
    wf = s.ch(s.recv("ac-radio"), "line~")
    drift = s.ch(s.obj("osc~ 0.13"), "*~ 0.004", "+~ 1")
    wh = s.ch(mul(s, wf, drift), "osc~", "*~ 0.06")
    swell = s.ch(s.obj("osc~ 0.05"), "*~ 0.5", "+~ 0.5")
    L = mul(s, add(s, s.to(stat, "*~ 0.5"), mul(s, wh, swell)), ln)
    R = mul(s, add(s, s.to(stat, "*~ 0.35"), s.to(mul(s, wh, swell), "*~ 0.7")), ln)
    throws(s, L, R, mix=0.6, send=0.5)
    return s


def tex_data():
    s, ln = switched("data", "ac-g-tex5")
    s.comment("Data: bursts of tiny square-wave blips on chord tones, crushed - a machine thinking")
    up = s.to(s.recv("ac-data"), "unpack f f")
    env = s.ch(s.m(s.to((up, 1), "t f"), "0.5, 0 $1"), "vline~")
    hz = s.ch((up, 0), "mtof")
    sq = s.ch(s.to(hz, "phasor~"), "-~ 0.5", "*~ 1000", "clip~ -0.2 0.2")
    sig = mul(s, sq, env)
    hold = s.obj("samphold~")
    s.c(sig, 0, hold, 0)
    s.c(s.obj("phasor~ 6000"), 0, hold, 1)
    o = mul(s, s.to(hold, "*~ 3.5"), ln)
    pn = s.ch(s.obj("osc~ 0.3"), "*~ 0.4", "+~ 0.5")
    throws(s, mul(s, o, pn), mul(s, o, s.ch(pn, "*~ -1", "+~ 1")), mix=0.5, send=0.6)
    return s


def tex_buzz():
    s, ln = switched("buzz", "ac-g-tex6")
    s.comment("Buzz: an electric hum on the tonic - a narrow pulse ringing two resonances, swelling and crackling")
    f = s.ch(s.m(s.ch(s.recv("ac-dronep"), "line 0 40", "mtof"), "$1 2000"), "line~")
    pulse = s.ch(s.to(f, "phasor~"), "-~ 0.97", "max~ 0", "*~ 30")
    outs = []
    for h, q in ((3, 18), (5, 25)):
        v = s.obj(f"vcf~ {q}")
        s.c(pulse, 0, v, 0)
        s.c(s.to(f, f"*~ {h}"), 0, v, 1)
        outs.append(v)
    crack = s.ch(s.obj("noise~"), "-~ 0.998", "max~ 0", "*~ 200")
    sw = s.ch(s.obj("osc~ 0.031"), "*~ 0.45", "+~ 0.55")
    L = mul(s, mul(s, add(s, outs[0], crack), sw), ln)
    R = mul(s, mul(s, add(s, outs[1], crack), sw), ln)
    throws(s, s.to(L, "*~ 1.6"), s.to(R, "*~ 1.6"), mix=1, send=0.4)
    return s


NEW_TEXTURES = (tex_radio, tex_data, tex_buzz)


# ---------------------------------------------------------------- character on the pads (inlet 0 L, 1 R)
def _char(name, idx):
    s, ln = switched(name, f"ac-g-ch{idx}")
    L, R = s.obj("inlet~", 20, 5), s.obj("inlet~", 160, 5)
    return s, ln, L, R


def _char_out(s, ln, l, r):
    for i, o in enumerate((l, r)):
        s.c(mul(s, o, ln), 0, s.obj("outlet~", 20 + i * 200, 980), 0)


def ch_chorus():
    s, ln, L, R = _char("chorus", 1)
    s.comment("Chorus: two modulated delays a side (ensemble width)")
    outs = []
    for side, src, rates in (("l", L, (0.61, 0.83)), ("r", R, (0.71, 0.97))):
        s.to(src, f"delwrite~ $0-ch{side} 40")
        o = s.obj("*~ 0.6")
        for j, rt in enumerate(rates):
            vd = s.obj(f"vd~ $0-ch{side}")
            s.c(s.ch(s.obj(f"osc~ {rt}"), "*~ 2.5", f"+~ {11 + 6 * j}"), 0, vd, 0)
            s.c(vd, 0, o, 0)
        outs.append(o)
    _char_out(s, ln, *outs)
    return s


def ch_tape():
    s, ln, L, R = _char("tape-wear", 2)
    s.comment("Tape: wow and flutter, soft saturation, hiss, a darker top")
    wow = add(s, s.ch(s.obj("osc~ 0.37"), "*~ 1.6"), s.ch(s.obj("osc~ 6.1"), "*~ 0.12"))
    outs = []
    for side, src in (("l", L), ("r", R)):
        s.to(src, f"delwrite~ $0-tp{side} 60")
        vd = s.obj(f"vd~ $0-tp{side}")
        s.c(s.to(wow, "+~ 25"), 0, vd, 0)
        x = s.to(vd, "*~ 1.6")
        den = s.ch(x, "abs~", "+~ 1")
        sat = s.obj("/~")
        s.c(x, 0, sat, 0)
        s.c(den, 0, sat, 1)
        lvl = s.ch(src, "abs~", "lop~ 4", "*~ 0.02", "clip~ 0 0.004")
        hiss = mul(s, s.ch(s.obj("noise~"), "hip~ 4000"), lvl)
        outs.append(s.to(add(s, s.to(sat, "lop~ 7500"), hiss), "*~ 0.9"))
    _char_out(s, ln, *outs)
    return s


def ch_ring():
    s, ln, L, R = _char("ring", 3)
    s.comment("Ring: ring modulation by a sine on a chord tone (a metallic, electric halo)")
    car = s.ch(s.recv("ac-ringf"), "line~", "osc~")
    _char_out(s, ln, mul(s, L, car), mul(s, R, car))
    return s


def ch_crush():
    s, ln, L, R = _char("crush", 4)
    s.comment("Crush: 6-bit steps and a 9 kHz sample rate")
    clk = s.obj("phasor~ 9000")
    outs = []
    for src in (L, R):
        lv = s.to(src, "*~ 32")
        q = s.obj("-~")
        s.c(lv, 0, q, 0)
        s.c(s.to(lv, "wrap~"), 0, q, 1)
        h = s.obj("samphold~")
        s.c(s.to(q, "*~ 0.03125"), 0, h, 0)
        s.c(clk, 0, h, 1)
        outs.append(s.to(h, "lop~ 8000"))
    _char_out(s, ln, *outs)
    return s


CHARS = (ch_chorus, ch_tape, ch_ring, ch_crush)


# ---------------------------------------------------------------- vocoder
VOC_BANDS = [round(150 * (46.7 ** (i / 9))) for i in range(10)]


def vocoder():
    s, ln = switched("vocoder", "ac-g-voc")
    s.comment("Vocoder: the input's 10 band envelopes shape a carrier - a synth choir on the chord (vocode) or "
              "the pads themselves (morph)")
    m = s.obj("r~ ac-in")
    # carriers
    choir = s.obj("*~ 0.25")
    for k in range(4):
        hz = s.ch(s.recv(f"ac-voccar{k}"), "line~")
        s.c(s.ch(s.to(hz, "phasor~"), "-~ 0.5"), 0, choir, 0)
        s.c(s.ch(s.to(hz, "*~ 1.006"), "phasor~", "-~ 0.5"), 0, choir, 0)
    s.c(s.ch(s.obj("noise~"), "hip~ 5000", "*~ 0.15"), 0, choir, 0)
    car = add(s, mul(s, choir, s.ch(s.recv("ac-vcsyn"), "line~")),
              mul(s, s.to(s.obj("r~ ac-padsig"), "*~ 4"), s.ch(s.recv("ac-vcpad"), "line~")))
    L, R = s.obj("*~ 11"), s.obj("*~ 11")
    s.col()
    for i, fc in enumerate(VOC_BANDS):
        q = 5
        mb = s.obj(f"vcf~ {q}")
        s.c(m, 0, mb, 0)
        s.c(s.obj(f"sig~ {fc}"), 0, mb, 1)
        envl = s.ch(mb, "abs~", "lop~ 30")
        cb = s.obj(f"vcf~ {q}")
        s.c(car, 0, cb, 0)
        s.c(s.obj(f"sig~ {fc}"), 0, cb, 1)
        s.c(mul(s, cb, envl), 0, L if i % 2 == 0 else R, 0)
        if i % 3 == 2:
            s.col(160)
    throws(s, mul(s, L, ln), mul(s, R, ln), mix=1.0, send=0.6, src=0.3)
    return s
