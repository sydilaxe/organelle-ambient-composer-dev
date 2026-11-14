"""The OLED as a live score (128 x 64), drawn with /oled/g* messages to mother (oscOut).

   y 0-7    the form: one bar per section (height = energy, width = length), the current one inverted,
            a playhead; in DRIFT the energy and the section's progress
   y 9-18   key, scale, voicing (toasts take this line for 2.5 s) and the time left (elapsed in DRIFT)
   y 20-52  left: the 4 pad voices as dots on a pitch ladder (they glide), your held notes as boxes,
            tonic ticks, breath bar; middle: 7 meters (drone, pads, textures, cloud, bells, motion,
            reverb) and the input level; right: the motion layer's Euclidean pattern with a moving
            cursor, and the tempo; while external audio plays, an INPUT panel instead: the last 6 s of
            the input's level as a waveform (onsets ticked above), the input mode and what Amble hears
            (pitch / pluck / textr), a dot while it records a memory; a sung or played pitch is drawn
            as a line across the pitch ladder
   y 53-63  section role, reverb, KEYS/MIDI, INT/EXT (FIN at the end)
A knob or page change shows the knob page for 2 s; SETUP takes the whole screen."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line
from data import ROLES, PAGE_NAMES, FAMILIES, PAGES

OSC = "oscOut"
GLOBALS = dict(acpopt=0, actoastt=0, acfr=0, acel=0, acsecel=0, acox=0, acoxs=0, acmcur=-1, acrvlvl=0, acoled=1,
               acsetup=0, acsetpg=0, acyy=0, acinv=0, acinlast=-1e+06, acinon=0, acinhi=0, aclastk=0)
ARRAYS = dict(acdisp=4, acdg=9, acinh=32, acino=32)
MIX_FROM = 3       # the knob pages from here on (SENDS, MIX) show the MIX view
# the play view's voice tags (2 x 4) and the MIX view's columns: (letter, knob, layer); the reverb last
TAG_LAYERS = ["drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud"]
TAG_LETTERS = dict(drone="Dr", sub="Sb", pad="Pd", bell="Bl", motion="Mo", tex="Tx", atm="At", cloud="Cl", verb="Rv")
MIX_COLS = [("Dr", "acmxd", "drone"), ("Sb", "acmxs", "sub"), ("Pd", "acmxp", "pad"), ("Bl", "acmxb", "bell"),
            ("Mo", "acmxm", "motion"), ("Tx", "acmxt", "tex"), ("Cl", "acmxc", "cloud"), ("At", "acmxa", "atm"),
            ("Rv", "acrvmix", "verb")]
SEND_COLS = [("Dr", "acsndd", "drone"), ("Pd", "acsndp", "pad"), ("Bl", "acsndb", "bell"), ("Mo", "acsndm", "motion"),
             ("Tx", "acsndt", "tex"), ("Cl", "acsndc", "cloud"), ("At", "acsnda", "atm"), ("In", "acsndi", None),
             ("Rv", "acrvmix", "verb")]


def Fill(x, y, w, h, c=1):
    return SendL(OSC, [str(x), str(y), str(w), str(h), str(c)], "/oled/gFillArea 3 $1 $2 $3 $4 $5")


def Inv(x, y, w, h):
    return SendL(OSC, [str(x), str(y), str(w), str(h)], "/oled/gInvertArea 3 $1 $2 $3 $4")


def Box(x, y, w, h, c=1):
    return SendL(OSC, [str(x), str(y), str(w), str(h), str(c)], "/oled/gBox 3 $1 $2 $3 $4 $5")


FLIP = Send(OSC, "/oled/gFlip 3")


def text_at(c, recv, x, y):
    """[r recv] (a list) -> printed at x, y"""
    lp = c.to(c.recv(recv), f"list prepend /oled/gPrintln 3 {x} {y} 8 1")
    c.c(c.to(lp, "list trim"), 0, c.obj("s " + OSC), 0)


def gated_text(c, recv, cond, x, y, clear=None):
    """[r recv] (a list) -> printed at x, y if cond holds when it arrives (optionally clearing a box first)"""
    t = c.to(c.recv(recv), "t a b")
    sp = c.obj("spigot")
    c.c(c.to((t, 1), "expr " + cond), 0, sp, 1)
    c.c(t, 0, sp, 0)
    if clear:
        t2 = c.to(sp, "t a b")
        run_steps(c, (t2, 1), [Fill(*clear, 0)])
        sp = t2
    lp = c.to(sp, f"list prepend /oled/gPrintln 3 {x} {y} 8 1")
    c.c(c.to(lp, "list trim"), 0, c.obj("s " + OSC), 0)


def ypitch(p):
    return f"max(20, min(52, int(52 - (({p}) - 43)*32/43)))"


def oled():
    c = Canvas("oled", w=4200, h=1200)
    c.comment("The score: regions redrawn at their own rates, a flip every 100 ms")
    lb = c.to(c.recv("ac-init"), "delay 200")
    c.c(c.m(lb, "/oled/gShowInfoBar 3 0"), 0, c.obj("s " + OSC), 0)
    c.c(lb, 0, c.obj("s ac-oledall"), 0)
    met = c.obj("metro 100")
    c.c(lb, 0, met, 0)
    c.c(met, 0, c.obj("s ac-frame"), 0)
    c.col()
    normal = f"acsetup == 0 && acpopt == 0 && acpage < {MIX_FROM}"
    mixv = f"acsetup == 0 && acpage >= {MIX_FROM}"
    proc(c, "ac-frame", [
        V("acfr", "acfr + 1"),
        If("acpopt > 0 && acnow >= acpopt", [V("acpopt", "0"), Call("ac-oledall")]),
        If("actoastt > 0 && acnow >= actoastt", [V("actoastt", "0"), Call("ac-scr2"), Call("ac-oledtime"),
                                                  If(mixv, [Call("ac-oledmixhead")])]),
        If(mixv, [If("int(acfr) % 2 == 0", [Call("ac-oledmixbars")])]),
        If(normal, [
            Call("ac-oledmid"),
            If("int(acfr) % 2 == 0", [Call("ac-oledinput")]),
            If("int(acfr) % 5 == 0", [Call("ac-oledtags")]),
            If("int(acfr) % 10 == 0", [Call("ac-oledform"), Call("ac-oledbottom"), Call("ac-oledtime")]),
        ]),
        FLIP,
    ])
    proc(c, "ac-oledall", [If("acsetup", [Call("ac-oledsetup")], [If(mixv, [Call("ac-oledmix")], [
        Fill(0, 0, 128, 64, 0), Call("ac-oledform"), Call("ac-scr2"), Call("ac-oledtime"), Call("ac-oledmid"),
        Call("ac-oledtags"), Call("ac-oledrhythm"), Call("ac-oledbottom"), FLIP])])])
    c.col()
    # ---- the form strip
    bar_x = "int(128*acox/acpsum)"
    bar_w = "max(1, int(128*acpdur[int(aci)]/acpsum) - 1)"
    bar_h = "(1 + int(acplan[int(aci)]*6))"
    proc(c, "ac-oledform", [If(normal, [
        Fill(0, 0, 128, 8, 0),
        If("acmode == 1", [
            V("acox", "0"),
            Loop("acnsec", "aci", [
                Fill(bar_x, f"8 - {bar_h}", bar_w, bar_h),
                If("aci == acsec", [V("acoxs", "acox"), Inv(bar_x, 0, bar_w, 8)]),
                V("acox", "acox + acpdur[int(aci)]"),
            ]),
            If("acsec < acnsec", [Fill("int(128*(acoxs + min(1, acsecel/max(1, acsecdur*actime))*acpdur[int(acsec)])"
                                       "/acpsum)", 0, 1, 8, 0)]),
        ], [Fill(0, 1, "max(1, int(acenergy*127))", 4),
            Fill(0, 7, "max(1, int(127*min(1, acsecel/max(1, acsecdur*actime))))", 1)]),
    ])])
    c.col()
    # ---- line 2: key / scale / voicing (ac-txt2), and the time; toasts take the line for 2.5 s
    gated_text(c, "ac-oledtop", normal + " && actoastt == 0", 0, 9, clear=(0, 9, 90, 10))
    proc(c, "ac-toast", [V("actoastt", "acnow + 2500")])
    gated_text(c, "ac-toast", f"acsetup == 0 && acpage < {MIX_FROM}", 0, 9, clear=(0, 9, 128, 10))
    gated_text(c, "ac-toast", mixv, 0, 0, clear=(0, 0, 128, 9))
    c.col()
    # time left (COMPOSE) or elapsed (DRIFT), "m:ss"
    proc(c, "ac-oledtime", [If(normal + " && actoastt == 0", [
        Fill(92, 9, 36, 10, 0),
        X("int(if(acmode==1 && (acrun || acstopped), max(0, (5 + 25*aclen)*60000 - acel), acel)/1000)",
          lambda c, src: _mmss(c, src)),
    ])])
    c.col()
    # ---- the middle: pitch ladder, meters
    mid = [Fill(0, 20, 60, 33, 0)]
    mid += [If(f"actonic + {12 * i} >= 43 && actonic + {12 * i} <= 86",
               [Fill(4, ypitch(f"actonic + {12 * i}"), 3, 1)]) for i in range(1, 5)]
    # the input's pitch, when Amble hears one, as a line across the ladder
    mid += [If("acinv && acpconf > 0.45 && acinp > 0 && acinp >= 43 && acinp <= 86",
               [Fill(8, ypitch("acinp"), 42, 1)])]
    mid += [Loop("4", "aci", [
        T("acdisp", "aci", "if(acdisp[int(aci)] < 1, acch[int(aci)], acdisp[int(aci)] + (acch[int(aci)] - "
                           "acdisp[int(aci)])*0.08)"),
        Fill("10 + 11*aci", f"{ypitch('acdisp[int(aci)]')} - 1", 4, 4),
    ])]
    mid += [Loop("4", "aci", [If("aclvn[int(aci)] >= 0", [
        Box(52, f"{ypitch('aclvn[int(aci)] + acbendt[int(aclvc[int(aci)])]')} - 2", 6, 5)])])]
    mid += [If("acbreath > 0.02", [Fill(0, "52 - int(acbreath*32)", 2, "max(1, int(acbreath*32))")])]
    proc(c, "ac-oledmid", mid)
    # the voices: two letters each (Dr Sb / Pd Bl / Mo Tx / At Cl, the layer keys' order) while it sounds, a dot
    # while it rests (auto), a dash when it's out
    tags = [Fill(62, 20, 33, 33, 0)]
    for i, n in enumerate(TAG_LAYERS):
        x, y = 64 + 16 * (i % 2), 21 + 8 * (i // 2)
        tags += [If(f"acg{n}*acsl{n} > 0.02", [Send(f"ac-oledtag{i}")],
                    [If(f"ace{n} == 0", [Fill(x + 1, y + 3, 10, 1)], [Fill(x + 5, y + 3, 2, 2)])])]
    proc(c, "ac-oledtags", [If(normal, tags)])
    for i, n in enumerate(TAG_LAYERS):
        c.c(c.m(c.recv(f"ac-oledtag{i}"), f"/oled/gPrintln 3 {64 + 16 * (i % 2)} {21 + 8 * (i // 2)} 8 1 {TAG_LETTERS[n]}"),
            0, c.obj("s " + OSC), 0)
    c.col()
    # ---- the rhythm: the Euclidean pattern (redrawn when it changes), a cursor on each step
    cell = lambda j: (f"97 + (int({j}) % 8)*4", f"22 + int(int({j})/8)*5")
    hit = "((int(aci + acmrot) % int(acmn)) * int(acmk)) % int(acmn) < acmk"
    proc(c, "ac-oledrhythm", [If(normal + " && acinv == 0", [
        Fill(96, 20, 32, 33, 0), V("acmcur", "-1"),
        Loop("acmn", "aci", [If(hit, [Fill(*cell("aci"), 3, 3)],
                                [Fill(f"98 + (int(aci) % 8)*4", f"23 + int(int(aci)/8)*5", 1, 1)])]),
        # 3-digit tempi drop the "m" so they stay inside the screen
        X("int(acbpm + 0.5)", lambda c, src: _print_bpm(c, src)),
        Call("ac-oledverb"),
    ])])
    proc(c, "ac-step", [If(normal + " && acinv == 0 && acgmotion > 0.01 && int(acstep) % int(acmdiv) == 0", [
        If("acmcur >= 0", [Inv(*cell("acmcur"), 3, 3)]),
        V("acmcur", "int(acstep/acmdiv) % int(acmn)"),
        Inv(*cell("acmcur"), 3, 3),
    ])])
    c.col()
    # ---- the INPUT panel (replaces the rhythm column while external audio plays; back 5 s after it stops)
    inx = "(int(acinhi + 1 + aci) % 32)"
    proc(c, "ac-oledinput", [
        # the history: one column per 200 ms
        V("acinhi", "(acinhi + 1) % 32"),
        T("acinh", "acinhi", "min(1, max(0, (acinlvl - 36)/58))*(acinput > 0.01)"),
        T("acino", "acinhi", "acinon*(acinput > 0.01)"), V("acinon", "0"),
        If("acinput > 0.01 && acact > 0.15", [V("acinlast", "acnow")]),
        If("acinv == 0 && acnow - acinlast < 5000", [V("acinv", "1"), If(normal, [Call("ac-oledinlbl")])]),
        If("acinv && acnow - acinlast >= 5000", [V("acinv", "0"), Call("ac-oledrhythm")]),
        If(normal + " && acinv", [
            Fill(96, 21, 32, 13, 0),
            Loop("32", "aci", [
                Fill("96 + aci", f"28 - int(acinh[{inx}]*5)", 1, f"1 + 2*int(acinh[{inx}]*5)"),
                If(f"acino[{inx}]", [Fill("96 + aci", 21, 1, 1)]),
            ]),
            If("int(acfr) % 10 == 0", [Call("ac-oledinlbl")]),
        ]),
    ])
    proc(c, "ac-oledinlbl", [If(normal + " && acinv", [Fill(96, 34, 32, 19, 0), Call("ac-oledinl1"),
                                                        Call("ac-oledinl2"),
                                                        If("acrec", [Fill(125, 46, 3, 3)])])])
    Line("ac-oledinl1", "list $1", [("s", "acinmode", ["auto", "reso", "cloud", "tape", "ghost", "bands", "vocod",
                                                       "morph"])], "ac-oledinl1b")(c)
    text_at(c, "ac-oledinl1b", 97, 35)
    Line("ac-oledinl2", "list $1", [("s", "acinclass", ["quiet", "pitch", "pluck", "textr"])], "ac-oledinl2b")(c)
    text_at(c, "ac-oledinl2b", 97, 43)
    c.col()
    # ---- the bottom line
    proc(c, "ac-oledbottom", [If(normal, [Fill(0, 53, 128, 11, 0), If("acrun", [Call("ac-oledbot")],
                                                                      [If("acstopped", [Call("ac-oledstop")],
                                                                          [Call("ac-oledfin")])])])])
    # bottom: role and voicing; right: who plays (K = Organelle keys, M = external MIDI) and E = external clock
    Line("ac-oledbot", "list $1 $2", [("s", "acrole", ROLES), ("s", "acfam", [n for n, _, _ in FAMILIES])],
         "ac-oledbot2")(c)
    text_at(c, "ac-oledbot2", 0, 54)
    Line("ac-oledbot", "list $1", [("s", "acsync", ["M", "ME"])],
         "ac-oledbot3")(c)
    text_at(c, "ac-oledbot3", 116, 54)
    Line("ac-oledverb", "list $1", [("s", "acvtype", ["-", "B1", "B2", "HALL", "SHIM"])], "ac-oledverb2")(c)
    text_at(c, "ac-oledverb2", 97, 45)
    c.c(c.m(c.recv("ac-oledfin"), "/oled/gPrintln 3 0 54 8 1 FIN - B: new piece"), 0, c.obj("s " + OSC), 0)
    c.c(c.m(c.recv("ac-oledstop"), "/oled/gPrintln 3 0 54 8 1 STOPPED - A#: start"), 0, c.obj("s " + OSC), 0)
    # redraw the pattern when it changes (each section) and on the bar
    d = c.obj("delay 5")
    c.c(c.recv("ac-section"), 0, d, 0)
    c.c(d, 0, c.obj("s ac-oledrhythm"), 0)
    c.c(d, 0, c.obj("s ac-oledform"), 0)
    c.col()
    # ---- the knob page pop-up (6 s after the last knob turn or aux tap)
    # (a value moved from elsewhere - a CC on another page's knob - shows as a message)
    proc(c, "ac-oledknob", [If(mixv, [Send("ac-mixknob"), Call("ac-scr4"), Call("ac-scr5")],
                               [If("int(aclastk/4) == acpage", [Call("ac-oledpop")], [Send("ac-mixknob")])])])
    Line("ac-mixknob", "list $1 $2", [("s", "aclastk", [lab for p in PAGES for lab, _, _ in p]),
                                       ("f", f"int(acparams[int(aclastk)]*100)")], "ac-toast")(c)
    proc(c, "ac-oledpop", [If(mixv, [V("acpopt", "0"), Call("ac-oledmix")]), If(normal.replace(" && acpopt == 0", ""), [
        V("acpopt", "acnow + 6000"),
        Fill(0, 9, 128, 55, 0),
        Call("ac-oledpghead"),
        Call("ac-scr4"), Call("ac-scr5"),
        Loop("4", "aci", [Box("1 + 32*aci", 50, 30, 8), Fill("2 + 32*aci", 51,
                                                            "max(1, int(28*acparams[int(acpage*4 + aci)]))", 6)]),
        FLIP,
    ])])
    Line("ac-oledpghead", "list page $1", [("s", "acpage", PAGE_NAMES)], "ac-oledpg2")(c)
    text_at(c, "ac-oledpg2", 0, 11)
    for ln, y in ((4, 24), (5, 36)):
        gated_text(c, f"ac-txt{ln}", "acsetup == 0 && acpopt > 0", 0, y, clear=(0, y, 128, 10))
    mixview(c, mixv)
    return c


def mixview(c, mixv):
    """the MIX view (on the MIX and SENDS pages): a bar per voice and the reverb - the live level filled, the
    knob's level as a tick, the voice's two letters below (the 4 the knobs turn inverted); a voice that is forced on
    has a dot on top, one that is out a dash at the foot"""
    cols = []
    for i, ((ml, mk, mn), (sl, sk, sn)) in enumerate(zip(MIX_COLS, SEND_COLS)):
        x = 2 + 14 * i
        def live(k, n):
            if n is None:
                return f"min(1, max(0, (acinlvl - 40)/50))*{k}"
            if n == "verb":
                return "min(1, max(0, (acrvlvl - 45)/40))"
            return f"min(1, acg{n}*acsl{n}*{k})"
        knob = f"if(acpage >= 5, {mk}, {sk})"
        lv = f"if(acpage >= 5, {live(mk, mn)}, {live(sk, sn)})"
        cols += [T("acdg", str(i), f"acdg[{i}] + ({lv} - acdg[{i}])*0.3"),
                 If(f"acdg[{i}] > 0.02", [Fill(x + 2, f"52 - int(acdg[{i}]*40)", 6, f"int(acdg[{i}]*40)")]),
                 Fill(x, f"52 - int(min(1, {knob})*40)", 10, 1)]
        for n, cond in ((mn, "acpage >= 5"), (sn, "acpage < 5")):
            if n not in (None, "verb"):
                cols += [If(f"{cond} && ace{n} == 2", [Fill(x + 4, 10, 2, 2)]),
                         If(f"{cond} && ace{n} == 0", [Fill(x, 52, 10, 1)])]
    proc(c, "ac-oledmixbars", [If(mixv, [Fill(0, 10, 128, 43, 0)] + cols)])
    proc(c, "ac-oledmix", [If(mixv, [
        Fill(0, 0, 128, 64, 0), Call("ac-oledmixhead"), Call("ac-oledmixbars"),
        If("acpage >= 5", [Send("ac-oledmixl")], [Send("ac-oledsndl")]),
        # the four the knobs turn
        Inv("if(acpage == 3 || acpage == 5, 0, 56)", 54, 56, 10),
        FLIP])])
    Line("ac-oledmixhead", "list $1 - $2 of $3 $4",
         [("s", "acpage", PAGE_NAMES), ("f", "acsec + 1"), ("f", "acnsec"), ("s", "acrole", ROLES)], "ac-oledmixh")(c)
    gated_text(c, "ac-oledmixh", mixv + " && actoastt == 0", 0, 0, clear=(0, 0, 128, 9))
    for recv, colset in (("ac-oledmixl", MIX_COLS), ("ac-oledsndl", SEND_COLS)):
        r = c.recv(recv)
        for i, (lab, _, _) in enumerate(colset):
            c.c(c.m(r, f"/oled/gPrintln 3 {2 + 14 * i} 55 8 1 {lab}"), 0, c.obj("s " + OSC), 0)


def _print_fmt(c, src, fmt, x, y):
    mf = c.obj(f"makefilename {fmt}")
    c.c(src[0], src[1], mf, 0)
    c.c(c.m(mf, f"/oled/gPrintln 3 {x} {y} 8 1 $1"), 0, c.obj("s " + OSC), 0)


def _print_bpm(c, src):
    mo = c.obj("moses 100")
    c.c(src[0], src[1], mo, 0)
    _print_fmt(c, (mo, 0), "%dbpm", 97, 36)
    _print_fmt(c, (mo, 1), "%dbp", 97, 36)


def _mmss(c, src):
    t = c.obj("t f f")
    c.c(src[0], src[1], t, 0)
    _print_fmt(c, (c.to((t, 1), "expr min(99, int($f1/60))"), 0), "%2d:", 92, 9)
    _print_fmt(c, (c.to((t, 0), "expr int($f1) % 60"), 0), "%02d", 110, 9)
