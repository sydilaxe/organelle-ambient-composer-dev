"""Organelle controls: knobs (two pages, pickup), keys, aux, footswitch, screen lines, LED, toasts."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, run_steps, Line, lookup
from data import *
from pdlib import Toast

SECNAMES = ["emerge", "haze", "drift", "bloom", "swell", "dissolve"]
DRIFTNAMES = ["haze", "drift", "bloom", "swell", "surge"]
SIDE = {  # what to do after a knob changes a value (index = page*4 + knob)
    0: [Send("ac-densch")],
    2: [Call("ac-brightupd")],
    3: [Call("ac-inputupd")],
    4: [Call("ac-revupd")],
    5: [Call("ac-verbsel")],
    6: [Call("ac-revupd")],
    7: [Call("ac-revupd")],
    9: [SendL("ac-weird", ["acweird"]), Call("ac-brightupd")],
    10: [SendL("ac-motion", ["acmotion"])],
    11: [Send("ac-densch"), SendL("ac-pulse", ["acrpulse[int(acrole)] * (0.3 + 1.4*acrhythm)"])],
}
NP = len(PAGES)


def knobs():
    c = Canvas("knobs", w=2400)
    c.comment("Knob pickup: when a page changes, a knob moves its value proportionally towards the end it "
              "turns to, so nothing jumps")
    for k in range(4):
        r = c.recv(f"knob{k + 1}")
        t = c.to(r, "t f f")
        P = f"acparams[int(acpage*4+{k})]"
        R = f"acraw[{k}]"
        e = c.to((t, 1), f"expr if(acknown{k}, min(1, max(0, if($f1 > {R}, {P} + ($f1-{R})*(1-{P})/max(0.001, 1-{R}), "
                         f"{P} - ({R}-$f1)*{P}/max(0.001, {R})))), {P}); acpage*4+{k}")
        pk = c.obj("pack f f")
        c.c(e, 1, pk, 1)
        c.c(e, 0, pk, 0)
        tl = c.to(pk, "t l l")
        up = c.to((tl, 1), "unpack f f")
        tw = c.obj("tabwrite acparams")
        c.c(up, 1, tw, 1)
        c.c(up, 0, tw, 0)
        c.c(c.m((tl, 0), "$2 $1"), 0, c.obj("s ac-param"), 0)
        tr = c.to((t, 0), "t b f")
        ex = c.to((tr, 1), f"expr $f1; {k}")
        tw2 = c.obj("tabwrite acraw")
        c.c(ex, 1, tw2, 1)
        c.c(ex, 0, tw2, 0)
        c.c(c.m((tr, 0), "1"), 0, c.obj(f"v acknown{k}"), 0)
        c.col()
    r = c.recv("ac-param")
    names = [n for p in PAGES for _, n, _ in p]
    rt = c.to(r, "route " + " ".join(str(i) for i in range(4 * NP)))
    for i, n in enumerate(names):
        tb = c.to((rt, i), "t b f")
        c.c(tb, 1, c.obj("v " + n), 0)
        run_steps(c, (tb, 0), SIDE.get(i, []) + [Call("ac-scr4"), Call("ac-scr5")])
        c.col(150)
    # the scaled length shown on the screen
    return c


def keys():
    c = Canvas("keys", w=3000)
    c.comment("Keys play notes, unless an external controller is playing (or aux is held): then low octave = next "
              "key centre, top octave = functions. Aux tap: knob page. Footswitch: change now.")
    up = c.to(c.recv("notesRaw"), "unpack f f")
    c.c(up, 1, c.obj("v ackv"), 0)
    kb = c.to(up, "t b f")
    c.c(kb, 1, c.obj("v ackn"), 0)
    run_steps(c, (kb, 0), [If("acext || acauxheld || acforce == 1", [
        If("ackv > 0", [V("acauxused", "acauxheld"), SendL("ac-fkey", ["ackn"])],
           [SendL("ac-livenote", ["0", "ackn", "0"])])],
        [SendL("ac-livenote", ["0", "ackn", "ackv"])])])
    mo = c.ch(c.recv("ac-fkey"), "- 60", "moses 12")
    kt = c.to((mo, 0), "t b f")
    c.c(kt, 1, c.obj("v acpend"), 0)
    c.c(kt, 0, c.obj("s ac-keytoast"), 0)
    sel = c.ch((mo, 1), "- 12", "sel " + " ".join(str(i) for i in range(12)))
    c.col()

    def mute(var, label):
        return [V(var, f"1-{var}"), V("acfade", "2500"), Call("ac-layers"),
                If(var, [Toast(label + " on")], [Toast(label + " off")])]

    funcs = [
        [V("acmode", "1-acmode"), V("acended", "0"), V("acrun", "1"), Send("ac-master", "1 3000"),
         If("acmode==1", [V("acsec", "0"), Call("ac-plan"), Call("ac-section"), Call("ac-change"),
                          Toast("COMPOSE new arc")],
            [Call("ac-section"), Call("ac-change"), Toast("DRIFT endless")]),
         Call("ac-scr"), Send("ac-led")],
        [Call("ac-change"), Toast("chord change")],
        [V("acsec", "acsec+1"), Call("ac-section"), Toast("next section")],
        mute("acmdrone", "drone"), mute("acmpad", "pads"), mute("acmtex", "texture"),
        mute("acmcloud", "cloud"), mute("acmbell", "bells"),
        [Call("ac-capture")],
        [V("acinmode", "(acinmode+1) % 6"), Call("ac-inputupd"), Call("ac-inmodetoast"), Call("ac-scr5")],
        [V("acvfreeze", "1-acvfreeze"), V("acfreeze", "acvfreeze"), Call("ac-freezeupd"), Call("ac-revupd"),
         If("acvfreeze", [Toast("hold - reverb and cloud")], [Toast("hold released")])],
        [Call("ac-reseed"), Toast("new piece")],
    ]
    for i, f in enumerate(funcs):
        b = c.obj("t b")
        c.c(sel, i, b, 0)
        run_steps(c, (b, 0), f)
        c.col(170)
    Line("ac-keytoast", "list next key $1", [("s", "acpend", NOTE_NAMES)], "ac-toast")(c)
    Line("ac-inmodetoast", "list input $1", [("s", "acinmode", INMODES)], "ac-toast")(c)
    # aux: knob page
    a = c.ch(c.recv("aux"), "sel 0")
    b = c.to((a, 1), "t b")
    run_steps(c, (b, 0), [X("1; 0; acnow", "v acauxheld", "v acauxused", "v acauxt")])
    run_steps(c, (a, 0), [V("acauxheld", "0"), If("acauxused == 0", [
        V("acpage", f"(acpage+1) % {NP}"), Call("ac-pagetoast"), Call("ac-scr4"), Call("ac-scr5")])])
    Line("ac-pagetoast", "list page $1", [("s", "acpage", PAGE_NAMES)], "ac-toast")(c)
    f = c.ch(c.recv("fs"), "sel 0")
    c.c(c.to((f, 1), "t b"), 0, c.obj("s ac-change"), 0)
    return c


def screen():
    c = Canvas("screen", w=3600)
    c.comment("Line 1 state, 2 key/scale/voicing, 3 pad timbres + texture (and toasts), 4-5 the knob page")
    proc(c, "ac-scr", [Call(f"ac-scr{i}") for i in range(1, 6)])
    # line 1
    s1 = c.ch(c.recv("ac-scr1"), "expr if(acended || acrun==0, 2, acmode)", "sel 0 1 2")
    c.c(c.to((s1, 0), "t b"), 0, c.obj("s ac-scr1d"), 0)
    c.c(c.to((s1, 1), "t b"), 0, c.obj("s ac-scr1c"), 0)
    c.c(c.m((s1, 2), "list FIN - B new piece"), 0, c.obj("s screenLine1"), 0)
    c.col()
    Line("ac-scr1d", "list DRIFT $1 $2",
         [("s", "acrole", ROLES), ("f", "acseed % 10000")], "screenLine1")(c)
    Line("ac-scr1c", "list COMP $1 of $2 $3",
         [("f", "acsec+1"), ("f", "acnsec"),
          ("s", "acrole", ROLES)], "screenLine1")(c)
    Line("ac-scr2", "list $1 $2 $3",
         [("s", "int(actonic) % 12", NOTE_NAMES), ("s", "acsci", [n for n, _ in SCALES]),
          ("s", "acfam", [n for n, _, _ in FAMILIES])], "screenLine2")(c)
    Line("ac-scr3", "list $1 $2 $3 $4 $5",
         [("s", f"acflav[{k}]", FLAVOURS) for k in range(4)] + [("s", "actex1", TEXTURES)], "screenLine3")(c)
    for ln in (4, 5):
        s = c.ch(c.recv(f"ac-scr{ln}"), "expr acpage", "sel " + " ".join(str(i) for i in range(NP)))
        for i in range(NP):
            c.c(c.to((s, i), "t b"), 0, c.obj(f"s ac-scr{ln}p{i}"), 0)
    c.col()
    Line("ac-scr4p0", "list Dens $1 Tide $2", [("f", "int(acdens*100)"), ("f", "int(actide*100)")], "screenLine4")(c)
    Line("ac-scr5p0", "list Colr $1 In $2 $3",
         [("f", "int(accolor*100)"), ("f", "int(acinput*100)"),
          ("s", "if(acinmode==0, 6 + acinclass, acinmode)", INMODES + ["auto", "pitched", "plucked", "texture"])],
         "screenLine5")(c)
    Line("ac-scr4p1", "list Mix $1 Verb $2", [("f", "int(acrvmix*100)"),
                                              ("s", "if(acrvtype < 0.2, 0, 1 + min(3, int((acrvtype-0.2)/0.2)))", VERBS)],
         "screenLine4")(c)
    Line("ac-scr5p1", "list Time $1 s Tone $2",
         [("f", "int(1.5 + 28.5*pow(acrvtime, 1.5))"), ("f", "int(acrvtone*100)")], "screenLine5")(c)
    Line("ac-scr4p2", "list Len $1 min Weird $2", [("f", "int(5 + 25*aclen)"), ("f", "int(acweird*100)")],
         "screenLine4")(c)
    Line("ac-scr5p2", "list Mot $1 Rhy $2", [("f", "int(acmotion*100)"), ("f", "int(acrhythm*100)")], "screenLine5")(c)
    # toasts on line 3, then line 3 comes back
    t = c.to(c.recv("ac-toast"), "t a b")
    d = c.obj("delay 2500")
    c.c(t, 1, d, 0)
    c.c(t, 0, c.obj("s screenLine3"), 0)
    c.c(d, 0, c.obj("s ac-scr3"), 0)
    # LED: green drifting, blue composing, off when finished; white flash on a chord change
    led = c.obj("s led")
    lc = c.ch(c.recv("ac-led"), "expr if(acended, 0, if(acmode, 5, 3))")
    c.c(lc, 0, led, 0)
    fl = c.to(c.recv("ac-flash"), "t b b")
    c.c(c.to((fl, 0), "delay 150"), 0, c.obj("s ac-led"), 0)
    c.c(c.m((fl, 1), "7"), 0, led, 0)
    return c
