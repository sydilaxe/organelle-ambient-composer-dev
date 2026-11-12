"""The OLED as a live score (128 x 64), drawn with /oled/g* messages to mother (oscOut).

   y 0-7    the form: one bar per section (height = energy, width = length), the current one inverted,
            a playhead; in DRIFT the energy and the section's progress
   y 9-18   key, scale, voicing (toasts take this line for 2.5 s) and the time left (elapsed in DRIFT)
   y 20-52  left: the 4 pad voices as dots on a pitch ladder (they glide), your held notes as boxes,
            tonic ticks, breath bar; middle: 7 meters (drone, pads, textures, cloud, bells, motion,
            reverb) and the input level; right: the motion layer's Euclidean pattern with a moving
            cursor, and the tempo
   y 53-63  section role, reverb, KEYS/MIDI, INT/EXT (FIN at the end)
A knob or page change shows the knob page for 2 s; SETUP takes the whole screen."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line
from data import ROLES, PAGE_NAMES, FAMILIES

OSC = "oscOut"
GLOBALS = dict(acpopt=0, actoastt=0, acfr=0, acel=0, acsecel=0, acox=0, acoxs=0, acmcur=-1, acrvlvl=0, acoled=1,
               acsetup=0, acsetpg=0, acyy=0)
ARRAYS = dict(acdisp=4, acdg=8)


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
    normal = "acsetup == 0 && acpopt == 0"
    proc(c, "ac-frame", [
        V("acfr", "acfr + 1"),
        If("acpopt > 0 && acnow >= acpopt", [V("acpopt", "0"), Call("ac-oledall")]),
        If("actoastt > 0 && acnow >= actoastt", [V("actoastt", "0"), Call("ac-scr2"), Call("ac-oledtime")]),
        If(normal, [
            Call("ac-oledmid"),
            If("int(acfr) % 2 == 0", [Call("ac-oledmeters")]),
            If("int(acfr) % 10 == 0", [Call("ac-oledform"), Call("ac-oledbottom"), Call("ac-oledtime")]),
        ]),
        FLIP,
    ])
    proc(c, "ac-oledall", [If("acsetup", [Call("ac-oledsetup")], [
        Fill(0, 0, 128, 64, 0), Call("ac-oledform"), Call("ac-scr2"), Call("ac-oledtime"), Call("ac-oledmid"),
        Call("ac-oledmeters"), Call("ac-oledrhythm"), Call("ac-oledbottom"), FLIP])])
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
    gated_text(c, "ac-toast", "acsetup == 0", 0, 9, clear=(0, 9, 128, 10))
    c.col()
    # time left (COMPOSE) or elapsed (DRIFT), "m:ss"
    proc(c, "ac-oledtime", [If(normal + " && actoastt == 0", [
        Fill(92, 9, 36, 10, 0),
        X("int(if(acmode==1 && acrun, max(0, (5 + 25*aclen)*60000 - acel), acel)/1000)",
          lambda c, src: _mmss(c, src)),
    ])])
    c.col()
    # ---- the middle: pitch ladder, meters
    mid = [Fill(0, 20, 60, 33, 0)]
    mid += [If(f"actonic + {12 * i} >= 43 && actonic + {12 * i} <= 86",
               [Fill(4, ypitch(f"actonic + {12 * i}"), 3, 1)]) for i in range(1, 5)]
    mid += [Loop("4", "aci", [
        T("acdisp", "aci", "if(acdisp[int(aci)] < 1, acch[int(aci)], acdisp[int(aci)] + (acch[int(aci)] - "
                           "acdisp[int(aci)])*0.08)"),
        Fill("10 + 11*aci", f"{ypitch('acdisp[int(aci)]')} - 1", 4, 4),
    ])]
    mid += [Loop("4", "aci", [If("aclvn[int(aci)] >= 0", [
        Box(52, f"{ypitch('aclvn[int(aci)] + acbendt[int(aclvc[int(aci)])]')} - 2", 6, 5)])])]
    mid += [If("acbreath > 0.02", [Fill(0, "52 - int(acbreath*32)", 2, "max(1, int(acbreath*32))")])]
    proc(c, "ac-oledmid", mid)
    gains = ["acgdrone", "acgpad", "acgtex", "acgcloud", "acgbell", "acgmotion", "min(1, max(0, (acrvlvl - 45)/40))"]
    gexpr = "if(aci==0, " + gains[0] + ", " + "".join(f"if(aci=={i}, {g}, " for i, g in enumerate(gains[1:], 1)) \
            + "0" + ")" * 7
    proc(c, "ac-oledmeters", [
        Fill(62, 20, 33, 33, 0),
        Loop("7", "aci", [
            T("acdg", "aci", f"acdg[int(aci)] + ({gexpr} - acdg[int(aci)])*0.25"),
            Fill("62 + 4*aci", "52 - int(acdg[int(aci)]*30)", 3, "max(1, int(acdg[int(aci)]*30))"),
        ]),
        Fill(92, "52 - int(min(1, max(0, (acinlvl - 40)/50))*30)", 2,
             "max(1, int(min(1, max(0, (acinlvl - 40)/50))*30))"),
    ])
    c.col()
    # ---- the rhythm: the Euclidean pattern (redrawn when it changes), a cursor on each step
    cell = lambda j: (f"97 + (int({j}) % 8)*4", f"22 + int(int({j})/8)*5")
    hit = "((int(aci + acmrot) % int(acmn)) * int(acmk)) % int(acmn) < acmk"
    proc(c, "ac-oledrhythm", [If(normal, [
        Fill(96, 20, 32, 33, 0), V("acmcur", "-1"),
        Loop("acmn", "aci", [If(hit, [Fill(*cell("aci"), 3, 3)],
                                [Fill(f"98 + (int(aci) % 8)*4", f"23 + int(int(aci)/8)*5", 1, 1)])]),
        X("int(acbpm + 0.5)", lambda c, src: _print_fmt(c, src, "%dbpm", 97, 36)),
        Call("ac-oledverb"),
    ])])
    proc(c, "ac-step", [If(normal + " && acgmotion > 0.01 && int(acstep) % int(acmdiv) == 0", [
        If("acmcur >= 0", [Inv(*cell("acmcur"), 3, 3)]),
        V("acmcur", "int(acstep/acmdiv) % int(acmn)"),
        Inv(*cell("acmcur"), 3, 3),
    ])])
    c.col()
    # ---- the bottom line
    proc(c, "ac-oledbottom", [If(normal, [Fill(0, 53, 128, 11, 0), If("acrun", [Call("ac-oledbot")],
                                                                      [Call("ac-oledfin")])])])
    # bottom: role and voicing; right: who plays (K = Organelle keys, M = external MIDI) and E = external clock
    Line("ac-oledbot", "list $1 $2", [("s", "acrole", ROLES), ("s", "acfam", [n for n, _, _ in FAMILIES])],
         "ac-oledbot2")(c)
    text_at(c, "ac-oledbot2", 0, 54)
    Line("ac-oledbot", "list $1", [("s", "(acext || acforce == 1) + 2*acsync", ["K", "M", "KE", "ME"])],
         "ac-oledbot3")(c)
    text_at(c, "ac-oledbot3", 116, 54)
    Line("ac-oledverb", "list $1", [("s", "acvtype", ["-", "B1", "B2", "HALL", "SHIM"])], "ac-oledverb2")(c)
    text_at(c, "ac-oledverb2", 97, 45)
    c.c(c.m(c.recv("ac-oledfin"), "/oled/gPrintln 3 0 54 8 1 FIN - B: new piece"), 0, c.obj("s " + OSC), 0)
    # redraw the pattern when it changes (each section) and on the bar
    d = c.obj("delay 5")
    c.c(c.recv("ac-section"), 0, d, 0)
    c.c(d, 0, c.obj("s ac-oledrhythm"), 0)
    c.c(d, 0, c.obj("s ac-oledform"), 0)
    c.col()
    # ---- the knob page pop-up (2 s)
    proc(c, "ac-oledpop", [If("acsetup == 0", [
        V("acpopt", "acnow + 2000"),
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
    return c


def _print_fmt(c, src, fmt, x, y):
    mf = c.obj(f"makefilename {fmt}")
    c.c(src[0], src[1], mf, 0)
    c.c(c.m(mf, f"/oled/gPrintln 3 {x} {y} 8 1 $1"), 0, c.obj("s " + OSC), 0)


def _mmss(c, src):
    t = c.obj("t f f")
    c.c(src[0], src[1], t, 0)
    _print_fmt(c, (c.to((t, 1), "expr min(99, int($f1/60))"), 0), "%2d:", 92, 9)
    _print_fmt(c, (c.to((t, 0), "expr int($f1) % 60"), 0), "%02d", 110, 9)
