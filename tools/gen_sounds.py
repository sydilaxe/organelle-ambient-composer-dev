"""More sounds: electric / synthetic pad types, drone designs, the sub, electric textures, per-piece character
(chorus, tape, ring, crush) on the pads, and the vocoder (input speaks through a synth choir or the pads)."""
from pdlib import Canvas
from gen_dsp import switched, mul, add, ctl, throws, throws_to, _flav_inlets, _out
from data import TEXG


# ---------------------------------------------------------------- pad types 6..9 (inlets: freq~, bright~)
def flav_saws():
    s, ln = switched("saws", "$0-fw6")
    s.comment("Saws: three detuned saws (an analog ensemble), low one left, high one right, each side through "
              "its own resonant low-pass that tracks the note")
    f, b = _flav_inlets(s, 2)
    saws = [s.ch(s.to(f, f"*~ {d}"), "phasor~", "-~ 0.5") for d in (0.994, 1.0, 1.0065)]
    cf = s.to(mul(s, f, s.ch(b, "*~ 9", "+~ 1.5")), "clip~ 40 5500")
    outs = []
    for side in ((1, 0.7, 0.25), (0.25, 0.7, 1)):
        sm = s.obj("*~ 0.4")
        for sw, g in zip(saws, side):
            s.c(s.to(sw, f"*~ {g}"), 0, sm, 0)
        v = s.obj("vcf~ 1.6")
        s.c(sm, 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(s.ch((v, 1), "hip~ 30", "*~ 2.8"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_pwm():
    s, ln = switched("pwm", "$0-fw7")
    s.comment("PWM: a pulse whose width breathes, through a slowly sweeping resonant filter (a Juno-like string); "
              "the right side's width moves the other way")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    lfo = s.ch(s.recv("$0-la"), "* 1.7", "osc~", "*~ 0.35")
    sweep = s.ch(s.recv("$0-lb"), "osc~", "*~ 0.5", "+~ 0.5")
    cf = s.to(mul(s, f, add(s, s.to(sweep, "*~ 4"), s.ch(b, "*~ 5", "+~ 1.2"))), "clip~ 40 5000")
    outs = []
    for sign in (1, -1):
        w = s.ch(lfo, f"*~ {sign}", "+~ 0.5")
        p2 = s.to(add(s, ph, w), "wrap~")
        pulse = s.obj("-~")
        s.c(ph, 0, pulse, 0)
        s.c(p2, 0, pulse, 1)
        v = s.obj("vcf~ 2.5")
        s.c(s.to(pulse, "hip~ 20"), 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(s.to((v, 1), "*~ 0.75"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_digi():
    s, ln = switched("digi", "$0-fw8")
    s.comment("Digi: a sine ring-modulated at an inharmonic ratio, then bit-crushed and sample-rate reduced; "
              "the right side rings a hair higher and holds at a slower clock")
    f, b = _flav_inlets(s, 2)
    car = s.to(f, "osc~")
    outs = []
    for k, (rm, clk) in enumerate(((1.0, 1.0), (1.012, 0.83))):
        rr = s.to(f, f"*~ {1.4142 * rm}")
        s.c(s.to(s.recv("ac-fmr"), f"* {rm}"), 0, rr, 1)
        ring = mul(s, car, s.to(rr, "osc~"))
        x = add(s, s.to(car, "*~ 0.6"), s.to(ring, "*~ 0.5"))
        lv = s.obj("*~ 16")
        s.c(x, 0, lv, 0)
        ctl(s, lv, "ac-weird", "40 - 34*$f1")
        q = s.obj("-~")
        s.c(lv, 0, q, 0)
        s.c(s.to(lv, "wrap~"), 0, q, 1)
        inv = s.obj("/~ 16")
        s.c(q, 0, inv, 0)
        ctl(s, inv, "ac-weird", "40 - 34*$f1")
        hold = s.obj("samphold~")
        s.c(inv, 0, hold, 0)
        s.c(s.to(s.ch(b, f"*~ {8000 * clk}", f"+~ {3000 * clk}"), "phasor~"), 0, hold, 1)
        outs.append(s.ch(hold, "lop~ 7000", "hip~ 20", "*~ 0.5"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_sync():
    s, ln = switched("sync", "$0-fw9")
    s.comment("Sync: a hard-synced saw whose slave ratio sweeps (brightness and a slow LFO) - an electric lead; "
              "the right side's slave runs a little ahead")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    ratio = add(s, s.ch(b, "*~ 3", "+~ 1.3"), s.ch(s.recv("$0-lb"), "* 1.3", "osc~", "*~ 0.6"))
    win = s.ch(ph, "*~ -1", "+~ 1")
    outs = []
    for off in (0, 0.11):
        r = s.to(ratio, f"+~ {off}") if off else ratio
        sl = s.ch(mul(s, ph, r), "wrap~", "-~ 0.5")
        outs.append(s.ch(mul(s, sl, win), "lop~ 4500", "hip~ 30", "*~ 1.1"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_tine():
    s, ln = switched("tine", "$0-fw10")
    s.comment("Tine: an electric-piano bell that strikes itself every few seconds - a soft FM body and a "
              "bright tine partial that rings out; the tines sit left and right, a hair apart")
    f, b = _flav_inlets(s, 2)
    st = s.to(s.ch(s.recv("$0-lb"), "* 0.6", "+ 0.12"), "phasor~")
    dec = s.ch(st, "*~ -1", "+~ 1")
    e2 = mul(s, dec, dec)
    e3 = mul(s, e2, dec)
    e6 = mul(s, e3, e3)
    idx = s.ch(e2, "*~ 1.4", "+~ 0.2")
    amp = s.ch(e3, "*~ 0.6", "+~ 0.4")
    outs = []
    for d, r, pt in ((1.0, 7, 1.0), (1.0023, 7.03, 0.55)):
        fd = s.to(f, f"*~ {d}")
        body = s.ch(add(s, fd, mul(s, mul(s, s.to(fd, "osc~"), idx), fd)), "osc~")
        tine = mul(s, s.ch(s.to(f, f"*~ {r}"), "osc~"), s.to(mul(s, e6, s.ch(b, "*~ 0.6", "+~ 0.25")), f"*~ {0.5 * pt}"))
        outs.append(s.to(add(s, s.to(mul(s, body, amp), "*~ 0.45"), tine), "*~ 0.8"))
    # mono-safe: the right side keeps part of the left, so a mono sum never cancels
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))
    return s


def flav_sine():
    s, ln = switched("sine", "$0-fw11")
    s.comment("Sine: a harmonic sine pad - the fundamental and harmonics 2-6 at 1/n, brightness tilting the upper "
              "ones in; the right side a hair sharp, its odd and even harmonics balanced the other way")
    f, b = _flav_inlets(s, 2)
    tilt = [None, b]
    for _ in range(4):
        tilt.append(mul(s, tilt[-1], b))
    outs = []
    for d, oddeven in ((1.0, (1.0, 0.75)), (1.0009, (0.75, 1.0))):
        sm = s.obj("*~ 0.42")
        for n in range(1, 7):
            o = s.ch(s.to(f, f"*~ {n * d}"), "osc~", f"*~ {1 / n * (oddeven[0] if n % 2 else oddeven[1]):.4f}")
            s.c(mul(s, o, tilt[n - 1]) if tilt[n - 1] is not None else o, 0, sm, 0)
        outs.append(sm)
    # mono-safe: the right side keeps part of the left
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))
    return s


def flav_glass():
    s, ln = switched("glass", "$0-fw12")
    s.comment("Glass: two glassy wavetables (acwtA, a soft body; acwtB, sparse high harmonics), brightness and a slow "
              "drift morphing between them; the right side a hair sharp, drifting the other way; a faint octave of "
              "the bright table on top")
    f, b = _flav_inlets(s, 2)
    outs = []
    for d, rate, ph in ((1.0, 0.083, 0), (1.0011, 0.071, 0.5)):
        fr = s.to(f, f"*~ {d}")
        ta, tb = s.to(fr, "tabosc4~ acwtA"), s.to(fr, "tabosc4~ acwtB")
        lfo = s.obj(f"osc~ {rate}")
        s.c(s.m(s.obj("loadbang"), str(ph)), 0, lfo, 1)
        m = s.to(add(s, s.to(b, "*~ 0.75"), s.ch(lfo, "*~ 0.2", "+~ 0.1")), "clip~ 0 1")
        dif = s.obj("-~")
        s.c(tb, 0, dif, 0)
        s.c(ta, 0, dif, 1)
        sm = s.obj("*~ 0.4")
        s.c(add(s, ta, mul(s, dif, m)), 0, sm, 0)
        s.c(s.ch(s.to(fr, "*~ 2"), "tabosc4~ acwtB", "*~ 0.12"), 0, sm, 0)
        outs.append(sm)
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))   # mono-safe
    return s


NEW_FLAVS = (flav_saws, flav_pwm, flav_digi, flav_sync, flav_tine, flav_sine, flav_glass)


# ---------------------------------------------------------------- drone designs 1..3 (0 is the original)
def _drone_freq(s):
    return s.ch(s.m(s.ch(s.recv("ac-dronep"), "line 0 40", "mtof"), "$1 40"), "line~")


def _drone_out(s, sig, ln, sigR=None):
    """stereo: a second signal for the right, or else a slowly modulated 9-14 ms copy of the left"""
    if sigR is None:
        s.to(sig, "delwrite~ $0-dw 40")
        sigR = s.obj("vd~ $0-dw")
        s.c(s.ch(s.obj("osc~ 0.07"), "*~ 2.5", "+~ 11.5"), 0, sigR, 0)
        sigR = add(s, s.to(sig, "*~ 0.35"), s.to(sigR, "*~ 0.8"))
    oL = mul(s, s.to(sig, "hip~ 25"), ln)
    oR = mul(s, s.to(sigR, "hip~ 25"), ln)
    throws_to("ac-sendd")(s, oL, oR, mix=0.6, send=0.3, src=1, bus="bed")


def drone_analog():
    s, ln = switched("drone-analog", "ac-g-drone1")
    s.comment("Analog drone: two saws and a square an octave down through a slow resonant sweep")
    f = _drone_freq(s)
    sq = s.ch(s.to(f, "*~ 0.5"), "phasor~", "-~ 0.5", "*~ 1000", "clip~ -0.25 0.25")
    br = s.ch(s.recv("ac-bright"), "line~")
    outs = []
    for d, rate in ((1.0, 0.021), (1.0042, 0.017)):          # a saw and its own sweep on each side
        sm = s.obj("*~ 0.3")
        s.c(s.ch(s.to(f, f"*~ {d}"), "phasor~", "-~ 0.5"), 0, sm, 0)
        s.c(s.to(sq, "*~ 0.7"), 0, sm, 0)
        sweep = s.ch(s.obj(f"osc~ {rate}"), "*~ 0.5", "+~ 0.5")
        cf = s.to(mul(s, f, add(s, s.to(mul(s, sweep, br), "*~ 10"), s.obj("sig~ 1.5"))), "clip~ 40 4000")
        v = s.obj("vcf~ 3")
        s.c(sm, 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(s.to((v, 1), "*~ 2.6"))
    _drone_out(s, outs[0], ln, outs[1])
    return s


def drone_organ():
    s, ln = switched("drone-organ", "ac-g-drone2")
    s.comment("Organ drone: drawbar partials 1 2 3 4 6 8 with a slow rotary shimmer")
    f = _drone_freq(s)
    sm = s.obj("*~ 1")
    for h, a in ((1, 0.22), (2, 0.16), (3, 0.1), (4, 0.07), (6, 0.04), (8, 0.03)):
        s.c(s.ch(s.to(f, f"*~ {h}"), "osc~", f"*~ {a}"), 0, sm, 0)
    rot = s.ch(s.obj("osc~ 0.8"), "*~ 0.22")
    # rotary: opposite swells left and right, and the right is a slowly moving delayed copy
    s.to(sm, "delwrite~ $0-ow 40")
    dly = s.obj("vd~ $0-ow")
    s.c(s.ch(s.obj("osc~ 0.11"), "*~ 3", "+~ 13"), 0, dly, 0)
    _drone_out(s, mul(s, sm, s.to(rot, "+~ 0.78")), ln, mul(s, dly, s.ch(rot, "*~ -1", "+~ 0.78")))
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
    throws_to("ac-sendd")(s, o, o, mix=0.42, send=0.05, bus="bed")
    return s


# ---------------------------------------------------------------- electric textures 4..6
def tex_radio():
    s, ln = switched("radio", "ac-g-tex4")
    s.comment("Radio: a soft band of static, always there and swelling in and out, and a heterodyne whistle "
              "drifting near a chord tone - tuning between stations (the static's gate is slow and smoothed, so "
              "it never crackles)")
    gate = s.ch(s.obj("noise~"), "lop~ 0.3", "*~ 200", "-~ 0.1", "clip~ 0 1", "lop~ 1", "lop~ 1")
    g2 = s.ch(gate, "*~ 0.65", "+~ 0.35")
    # each side its own static (a diffuse band, not a centred hiss)
    stat, statR = [s.to(mul(s, s.ch(s.obj("noise~"), "hip~ 900", "lop~ 2200", "lop~ 2600"), g2), "*~ 0.6")
                   for _ in range(2)]
    wf = s.ch(s.recv("ac-radio"), "line~")
    drift = s.ch(s.obj("osc~ 0.13"), "*~ 0.004", "+~ 1")
    wh = s.ch(mul(s, wf, drift), "osc~", "*~ 0.06")
    swell = s.ch(s.obj("osc~ 0.05"), "*~ 0.5", "+~ 0.5")
    L = mul(s, add(s, s.to(stat, "*~ 0.5"), mul(s, wh, swell)), ln)
    R = mul(s, add(s, s.to(statR, "*~ 0.35"), s.to(mul(s, wh, swell), "*~ 0.7")), ln)
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


# ---------------------------------------------------------------- textures 7..11: voices, echoes, nature
def _lpnoise(s, hz, scale, off, lo, hi):
    """a slowly wandering value: white noise low-passed at hz, scaled, offset, clipped (a jittering centre)"""
    return s.ch(s.obj("noise~"), f"lop~ {hz}", f"*~ {scale}", f"+~ {off}", f"clip~ {lo} {hi}")


def _syllables(s, rate, scale, smooth, phrase_hz, phase):
    """speech-like loudness: random syllable bursts (noise low-passed at rate, clipped) inside slow phrases"""
    syl = s.ch(s.obj("noise~"), f"lop~ {rate}", f"*~ {scale}", "clip~ 0 1", f"lop~ {smooth}")
    ph = s.obj(f"osc~ {phrase_hz}")
    s.c(s.m(s.obj("loadbang"), f"{phase}"), 0, ph, 1)
    phrase = s.ch(ph, "-~ 0.2", "max~ 0", "*~ 1.25")
    return mul(s, syl, phrase)


def tex_murmur():
    s, ln = switched("murmur", "ac-g-tex7")
    s.comment("Murmur: two distant voices - a breathy low buzz through two drifting vowel formants, in syllables "
              "and phrases, far back (mostly reverb)")
    outs = []
    for side, (f0, ph) in enumerate(((112, 0), (147, 0.5))):
        vib = s.ch(s.obj(f"osc~ {4.1 + side}"), "*~ 0.012", "+~ 1")
        buzz = s.ch(mul(s, s.obj(f"sig~ {f0}"), vib), "phasor~", "-~ 0.5", "lop~ 1400")
        src = add(s, buzz, s.ch(s.obj("noise~"), "lop~ 3000", "*~ 0.25"))
        sm = s.obj("+~")
        for q, (hz, sc, off, lo, hi) in ((6, (3, 30000, 550, 250, 900)), (8, (2.5, 80000, 1500, 800, 2500))):
            v = s.obj(f"vcf~ {q}")
            s.c(src, 0, v, 0)
            s.c(_lpnoise(s, hz, sc, off, lo, hi), 0, v, 1)
            s.c(v, 0, sm, 0)
        env = _syllables(s, 5, 120, 20, 0.055 + 0.017 * side, ph)
        outs.append(mul(s, mul(s, s.to(sm, "lop~ 2600"), env), ln))
        s.col(260)
    L = add(s, s.to(outs[0], f"*~ {TEXG['MURMUR_G']}"), s.to(outs[1], f"*~ {TEXG['MURMUR_X']}"))
    R = add(s, s.to(outs[1], f"*~ {TEXG['MURMUR_G']}"), s.to(outs[0], f"*~ {TEXG['MURMUR_X']}"))
    throws(s, L, R, mix=0.35, send=1.0)
    return s


def tex_echoes():
    s, ln = switched("echoes", "ac-g-tex8")
    s.comment("Echoes: alien blips on chord tones (a gliding sine ring-modulated a tritone up) into ping-pong "
              "echoes whose delay times wobble, so each repeat bends in pitch")
    up = s.to(s.recv("ac-echo"), "unpack f f")
    tf = s.to((up, 0), "t f f")
    ex = s.to((tf, 0), "expr $f1; $f1*0.86")
    pk = s.obj("pack f f")
    s.c(ex, 1, pk, 1)
    s.c(ex, 0, pk, 0)
    fr = s.ch(s.m(pk, "$1, $2 160"), "vline~")
    env = s.ch(s.m((tf, 1), "0.6, 0 180"), "vline~")
    blip = mul(s, mul(s, s.to(fr, "osc~"), s.ch(fr, "*~ 1.414", "osc~")), mul(s, env, env))
    pn = s.to((up, 1), "expr cos($f1*1.5708); sin($f1*1.5708)")
    dl, dr = s.to(blip, "*~ 1"), s.to(blip, "*~ 1")
    s.c(pn, 0, dl, 1)
    s.c(pn, 1, dr, 1)
    s.col()
    # ping-pong: each side's echo feeds the other, through a band (lop / hip) so repeats darken
    reads = []
    for name, ms, rate, dep in (("$0-ecL", 420, 0.13, 25), ("$0-ecR", 610, 0.09, 30)):
        vd = s.obj(f"vd~ {name}")
        s.c(s.ch(s.obj(f"osc~ {rate}"), f"*~ {dep}", f"+~ {ms}"), 0, vd, 0)
        reads.append(s.ch(vd, "lop~ 2400", "hip~ 250"))
    for i, (name, dry) in enumerate((("$0-ecL", dl), ("$0-ecR", dr))):
        w = add(s, dry, s.to(reads[1 - i], "*~ 0.58"))
        s.to(w, f"delwrite~ {name} 1500")
    L = mul(s, add(s, s.to(dl, "*~ 0.35"), reads[0]), ln)
    R = mul(s, add(s, s.to(dr, "*~ 0.35"), reads[1]), ln)
    throws(s, s.to(L, f"*~ {TEXG['ECHO_G']}"), s.to(R, f"*~ {TEXG['ECHO_G']}"), mix=0.6, send=0.6)
    return s


def tex_whisper():
    s, ln = switched("whisper", "ac-g-tex9")
    s.comment("Whisper: breath noise shaped by two moving formants into fast syllables, in phrases - one each "
              "side")
    outs = []
    for side, ph in enumerate((0, 0.35)):
        src = s.ch(s.obj("noise~"), "hip~ 1200")
        sm = s.obj("+~")
        for q, (hz, sc, off, lo, hi) in ((4, (6, 60000, 2200, 1200, 3500)), (5, (5, 90000, 5000, 3500, 8000))):
            v = s.obj(f"vcf~ {q}")
            s.c(src, 0, v, 0)
            s.c(_lpnoise(s, hz, sc, off, lo, hi), 0, v, 1)
            s.c(v, 0, sm, 0)
        env = _syllables(s, 8, 150, 40, 0.045 + 0.013 * side, ph)
        outs.append(mul(s, mul(s, sm, env), ln))
        s.col(260)
    throws(s, s.to(outs[0], f"*~ {TEXG['WHISPER_G']}"), s.to(outs[1], f"*~ {TEXG['WHISPER_G']}"), mix=0.6, send=0.6)
    return s


def tex_leaves():
    s, ln = switched("leaves", "ac-g-tex10")
    s.comment("Leaves: a rustle in the trees - high noise in a fast flutter, dry little clicks, swelling with gusts")
    gust = s.ch(add(s, s.obj("osc~ 0.051"), s.ch(s.obj("osc~ 0.083"), "*~ 0.7")), "*~ 0.45", "+~ 0.35", "max~ 0.05")
    outs = []
    for side in range(2):
        n = s.ch(s.obj("noise~"), "hip~ 2500", "lop~ 9000")
        flutter = s.ch(s.obj("noise~"), "lop~ 60", "abs~", "*~ 25", "clip~ 0 1")
        ticks = s.ch(s.obj("noise~"), "-~ 0.997", "max~ 0", "*~ 300", "lop~ 7000")
        o = add(s, mul(s, n, flutter), s.to(ticks, "*~ 0.3"))
        outs.append(mul(s, mul(s, o, s.to(gust, f"*~ {1 - 0.15 * side}")), ln))
    throws(s, s.to(outs[0], f"*~ {TEXG['LEAVES_G']}"), s.to(outs[1], f"*~ {TEXG['LEAVES_G']}"), mix=0.6, send=0.4)
    return s


def tex_brook():
    s, ln = switched("brook", "ac-g-tex11")
    s.comment("Brook: a babbling stream - brown noise ringing very narrow bands whose pitch jitters at a few "
              "hertz (the classic brook model), two layers each side")
    outs = []
    for side in range(2):
        brown = s.ch(s.obj("noise~"), "lop~ 70", "*~ 12")
        sm = s.obj("+~")
        for sc, off in ((8000, 500 + 40 * side), (16000, 1000 + 80 * side)):
            v = s.obj("vcf~ 30")
            s.c(brown, 0, v, 0)
            s.c(_lpnoise(s, 14, sc, off, 150, 4000), 0, v, 1)
            s.c(v, 0, sm, 0)
        outs.append(mul(s, s.ch(sm, "hip~ 120"), ln))
    throws(s, s.to(outs[0], f"*~ {TEXG['BROOK_G']}"), s.to(outs[1], f"*~ {TEXG['BROOK_G']}"), mix=0.6, send=0.4)
    return s


NEW_TEXTURES = (tex_radio, tex_data, tex_buzz, tex_murmur, tex_echoes, tex_whisper, tex_leaves, tex_brook)


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
    """The vocoder at half rate (22.05 kHz; its bands reach 7 kHz): an outer canvas feeds the input and the pad
    signal in, and throws what comes out."""
    o = Canvas("vocoder", w=900)
    o.comment("Vocoder: the input's 10 band envelopes shape a carrier - a synth choir on the chord (vocode) or "
              "the pads themselves (morph). The work runs at half rate inside.")
    core = o.sub(_vocoder_core())
    o.c(o.ch(o.obj("r~ ac-in"), "lop~ 8000"), 0, core, 0)
    o.c(o.ch(o.obj("r~ ac-padsig"), "lop~ 8000"), 0, core, 1)
    throws_to("ac-sendi")(o, (core, 0), (core, 1), mix=1.0, send=0.6, src=0.3)
    return o


def _vocoder_core():
    s, ln = switched("vocoder-core", "ac-g-voc", block="32 1 0.5")   # = one parent block: even load
    m = s.obj("inlet~", 20, 5)
    padsig = s.obj("inlet~", 200, 5)
    # carriers
    choir = s.obj("*~ 0.25")
    for k in range(4):
        hz = s.ch(s.recv(f"ac-voccar{k}"), "line~")
        s.c(s.ch(s.to(hz, "phasor~"), "-~ 0.5"), 0, choir, 0)
        s.c(s.ch(s.to(hz, "*~ 1.006"), "phasor~", "-~ 0.5"), 0, choir, 0)
    s.c(s.ch(s.obj("noise~"), "hip~ 5000", "*~ 0.15"), 0, choir, 0)
    car = add(s, mul(s, choir, s.ch(s.recv("ac-vcsyn"), "line~")),
              mul(s, s.to(padsig, "*~ 4"), s.ch(s.recv("ac-vcpad"), "line~")))
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
    for i, x in enumerate((L, R)):
        s.c(mul(s, x, ln), 0, s.obj("outlet~ lin", 20 + i * 200, 980), 0)
    return s


# ---------------------------------------------------------------- atmospheres (a background bed, not every piece)
def atm_haze():
    s, ln = switched("atm-haze", "ac-g-atm0")
    s.comment("Haze: air shimmering on the chord - noise through 6 narrow bands on chord partials, each "
              "swelling on its own, spread across the field")
    L, R = s.obj("*~ 3"), s.obj("*~ 3")
    for k in range(6):
        v = s.obj("vcf~ 14")
        s.c(s.obj("noise~"), 0, v, 0)
        s.c(s.ch(s.recv(f"ac-atmf{k}"), "line~"), 0, v, 1)
        sw = s.ch(s.obj(f"osc~ {0.021 + 0.013 * k}"), "*~ 0.5", "+~ 0.5")
        b = mul(s, v, sw)
        gl, gr = [(1, 0.2), (0.2, 1), (0.8, 0.5), (0.5, 0.8), (1, 0.4), (0.4, 1)][k]
        s.c(s.to(b, f"*~ {gl}"), 0, L, 0)
        s.c(s.to(b, f"*~ {gr}"), 0, R, 0)
    throws_to("ac-senda")(s, mul(s, L, ln), mul(s, R, ln), mix=0.5, send=0.6)
    return s


def atm_deep():
    s, ln = switched("atm-deep", "ac-g-atm1")
    s.comment("Deep: a low rumble, different on each side, swelling slowly; now and then distant thunder rolls")
    th = s.ch(s.m(s.recv("ac-thunder"), "1 2500, 0 7000 2500"), "vline~")
    outs = []
    for k, rate in enumerate((0.027, 0.019)):
        r = s.ch(s.obj("noise~"), "lop~ 90", "lop~ 180", "*~ 14")
        sw = s.ch(s.obj(f"osc~ {rate}"), "*~ 0.4", "+~ 0.6")
        thn = mul(s, s.ch(s.obj("noise~"), "lop~ 260", "lop~ 400", "*~ 10"), s.to(th, f"*~ {[1, 0.6][k]}"))
        outs.append(mul(s, add(s, mul(s, r, sw), thn), ln))
    throws_to("ac-senda")(s, outs[0], outs[1], mix=0.22, send=0.25)
    return s


def atm_space():
    s, ln = switched("atm-space", "ac-g-atm2")
    s.comment("Space: air ringing in two combs tuned to the chord (root left, fifth right) - a far-away choir")
    outs = []
    for k in range(2):
        a = s.obj("+~")
        s.c(s.ch(s.obj("noise~"), "lop~ 3000", "*~ 0.03"), 0, a, 0)
        s.to(a, f"delwrite~ $0-sp{k} 40")
        vd = s.obj(f"vd~ $0-sp{k}")
        s.c(s.ch(s.recv(f"ac-atmc{k}"), "line~"), 0, vd, 0)
        s.c(s.ch(vd, "lop~ 2200", "*~ 0.985"), 0, a, 1)
        sw = s.ch(s.obj(f"osc~ {0.017 + 0.009 * k}"), "*~ 0.45", "+~ 0.55")
        outs.append(mul(s, mul(s, s.ch(vd, "hip~ 60", "*~ 5"), sw), ln))
    throws_to("ac-senda")(s, outs[0], outs[1], mix=0.8, send=0.8)
    return s


def atm_night():
    s, ln = switched("atm-night", "ac-g-atm3")
    s.comment("Night: distant insects - six high tones chirring at their own rates, scattered across the field, "
              "over a faint hiss")
    L, R = s.obj("*~ 0.16"), s.obj("*~ 0.16")
    for k in range(6):
        tone = s.ch(s.recv(f"ac-atmn{k}"), "line~", "osc~")
        pulse = s.ch(s.obj(f"osc~ {19 + 2.3 * k}"), "max~ 0")
        gate = s.ch(s.obj(f"osc~ {0.09 + 0.07 * k}"), "-~ 0.3", "max~ 0", "*~ 1.4")
        b = mul(s, mul(s, tone, mul(s, pulse, pulse)), gate)
        pos = [0.1, 0.85, 0.35, 0.65, 0.2, 0.95][k]
        s.c(s.to(b, f"*~ {(1 - pos) ** 0.5:.3f}"), 0, L, 0)
        s.c(s.to(b, f"*~ {pos ** 0.5:.3f}"), 0, R, 0)
    bed = [s.ch(s.obj("noise~"), "hip~ 6000", "*~ 0.004") for _ in range(2)]
    throws_to("ac-senda")(s, mul(s, add(s, L, bed[0]), ln), mul(s, add(s, R, bed[1]), ln), mix=1, send=0.5)
    return s


def atm_tides():
    s, ln = switched("atm-tides", "ac-g-atm4")
    s.comment("Tides: waves that wash across from one side to the other - noise whose level and brightness "
              "rise and fall over ~11 s, the right side a third of a wave behind")
    ph = s.obj("phasor~ 0.09")
    outs = []
    for off in (0, 0.33):
        p = s.ch(ph, f"+~ {off}", "wrap~") if off else ph
        e = s.ch(p, "cos~", "*~ -0.5", "+~ 0.5")
        e2 = mul(s, e, e)
        v = s.obj("vcf~ 0.8")
        s.c(s.obj("noise~"), 0, v, 0)
        s.c(s.ch(e2, "*~ 2200", "+~ 300"), 0, v, 1)
        outs.append(mul(s, s.ch(mul(s, (v, 1), e2), "*~ 1.1"), ln))
    throws_to("ac-senda")(s, outs[0], outs[1], mix=0.9, send=0.5)
    return s


ATMOS = (atm_haze, atm_deep, atm_space, atm_night, atm_tides)
