"""Organelle controls: knobs (two pages, pickup), keys, aux, footswitch, screen lines, LED, toasts."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, run_steps, Line
from data import *
from pdlib import Toast, Arm
from gen_setup import NSET
from data import MIX_KNOBS
import gen_setup as _S

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
    10: [SendL("ac-motion", ["acmotion"]), Call("ac-stereo")],
    11: [Send("ac-densch"), Call("ac-pulseupd")],
}
for _i in range(12, SEND_KNOBS):              # the SENDS pages
    SIDE[_i] = [Call("ac-sendupd")]
for _i in range(SEND_KNOBS, MIX_KNOBS):      # the MIX pages: the layer levels (coalesced: knobs send fast)
    SIDE[_i] = [Send("ac-mixch")]
SIDE[28] = [Call("ac-sinkupd")]              # PERFORM: Sink, Blur, Swell (Harm applies at the next choice)
SIDE[29] = [Call("ac-revupd")]
SIDE[30] = [Send("ac-densch"), Call("ac-brightupd"), Call("ac-swellupd")]
NP = len(PAGES)
# The Organelle keys are always functions (notes come from MIDI). Low octave: the knob pages, then harmony and form;
# top octave: the layers, then input, Freeze and the transport. Aux + a low key opens that SETUP page (C = 1).
# The manual (tools/manual.py) documents these, in this order.
PAGE_KEYS = [0, 1, 2, 5, 6, 3, 7]       # low C..F#: SHAPE, SPACE, PIECE, MIX 1, MIX 2, SENDS (1, again 2), PERFORM
SAVES_PAGE = 12                         # SETUP SAVES (aux + top B)
LOW_KEYS = ["SHAPE page", "SPACE page", "PIECE page", "MIX 1 page", "MIX 2 page", "SENDS page (again: 1 / 2)",
            "PERFORM page",
            "Root (hold)", "Resolve", "chord change now", "next section", "hold section"]
LAYER_KEYS = [("acmdrone", "drone", "acgdrone"), ("acmsub", "sub", "acgsub"), ("acmpad", "pads", "acgpad"),
              ("acmbell", "bells", "acgbell"), ("acmmotion", "motion", "acgmotion"), ("acmtex", "textures", "acgtex"),
              ("acmatm", "atmosphere", "acgatm"), ("acmcloud", "cloud", "acgcloud")]
TOP_KEYS = [f"{n} in/out | aux: auto" for _, n, _ in LAYER_KEYS] + [
    "input mode | aux: capture", "Freeze | aux: ANCHOR", "start / stop | aux: COMPOSE / DRIFT",
    "new piece | hold: COMPARE | + key: load | aux: SAVES"]
SAVE_KEY = 83                           # top B: tap = new piece; held, a key loads its slot (aux: saves to it)
ANCHOR_KEY = 81                         # top A: aux + tap = ANCHOR (set, then glide back), aux + hold = anchor here
FKEYS = LOW_KEYS + TOP_KEYS
ROOT_KEY = 60 + LOW_KEYS.index("Root (hold)")
CHORD_KEY = 60 + LOW_KEYS.index("chord change now")


def knobs():
    c = Canvas("knobs", w=2400)
    c.comment("Knob pickup: when a page changes, a knob moves its value proportionally towards the end it "
              "turns to, so nothing jumps")
    for k in range(4):
        kr = c.recv(f"knob{k + 1}")
        if k == 0:     # while Root (low G) is held, knob 1 picks the next key
            rs = c.obj("spigot")
            kt = c.to(kr, "t f b")
            c.c(c.to((kt, 1), "expr acroothold"), 0, rs, 1)
            c.c(kt, 0, rs, 0)
            rt_ = c.to(rs, "t b f")
            c.c(rt_, 1, c.obj("v acrootk"), 0)
            run_steps(c, (rt_, 0), [V("acrootn", "int(acrootk*11.99)"),
                                                     If("acrootn != acpend", [Call("ac-rootset")])])
        mo = c.ch(kr, f"expr if(acroothold && {k} == 0, -1000, if(acsetup, -1 - $f1, $f1))", "moses 0")
        sk = c.to((mo, 0), "moses -500")
        c.c(c.m(c.to((sk, 1), "expr -1 - $f1"), f"{k} $1"), 0, c.obj("s ac-setknob"), 0)
        t = c.to((mo, 1), "t f f")
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
        # (a value a morph or a macro offset moves is not your hand: it neither shows nor stops the morph)
        run_steps(c, (tb, 0), SIDE.get(i, []) + [If("acmorphing == 0", [T("acmtouch", i, "1"), V("aclastk", str(i)),
                                                                        Call("ac-oledknob")]), Send("ac-dirty")])
        c.col(150)
    # the scaled length shown on the screen
    return c


def keys():
    c = Canvas("keys", w=3200)
    c.comment("The Organelle keys are functions: low octave = knob pages, harmony and form (aux + key = that SETUP "
              "page), top octave = layers, input, Freeze, transport. Hold Root (low G) and play a key or MIDI note, "
              "or turn knob 1: the next key. Aux tap: next page. Footswitch: change now.")
    up = c.to(c.recv("notesRaw"), "unpack f f")
    c.c(up, 1, c.obj("v ackv"), 0)
    kb = c.to(up, "t b f")
    c.c(kb, 1, c.obj("v ackn"), 0)
    run_steps(c, (kb, 0), [If("ackv > 0", [
        V("acauxused", "acauxheld || acauxused"),
        # top B held: the next key is a slot (low C..B = 1-12, top C..D# = 13-16) - loaded, or with aux saved
        If(f"ackn == {SAVE_KEY}", [X("1; 0; 0", "v acbdown", "v acbused", "v acbcmp"),
                                   Arm("ac-cmphold", "600", stop="ac-bstop")],
           [If("acbdown", [V("acbused", "1"), Send("ac-bstop"), If("ackn >= 60 && ackn <= 75", [
               V("acslot", "ackn - 60"), Call("ac-slotcheck"),
               If("acauxheld", [Call("ac-savepiece")], [Call("ac-loadpiece")])])],
              [If(f"acroothold && ackn != {ROOT_KEY}", [V("acrootn", "int(ackn) % 12"), Call("ac-rootset")],
                  [SendL("ac-fkey", ["ackn"])])])])],
        [If(f"ackn == {ROOT_KEY}", [V("acroothold", "0")]),
         # top B let go: a tap is a new piece (aux: the SAVES page); a hold was COMPARE, which ends
         If(f"ackn == {SAVE_KEY} && acbdown", [Send("ac-bstop"),
            If("acbcmp", [Call("ac-cmpoff")], [If("acbused == 0", [
                If("acauxheld", [V("acsetup", "1"), V("acsetpg", str(SAVES_PAGE)), Call("ac-oledsetup")],
                   [Call("ac-newkey")])])]),
            X("0; 0", "v acbdown", "v acbcmp")]),
         # top A let go (aux + A): a tap glides back to the anchor (or sets it); a hold already anchored here
         If(f"ackn == {ANCHOR_KEY} && acanp", [Send("ac-ancstop"), If("acanheld == 0", [Call("ac-anchortap")]),
                                              X("0; 0", "v acanp", "v acanheld")]),
         # low A let go: a tap changes to the next chord now; a hold already picked others (ac-reroll)
         If(f"ackn == {CHORD_KEY}", [Send("ac-rrstop"), If("acrr == 0", [Call("ac-chordnow")]), V("acrr", "-1")])])])
    mo = c.ch(c.recv("ac-fkey"), "- 60", "moses 12")
    lsel = c.to((mo, 0), "sel " + " ".join(str(i) for i in range(12)))
    tsel = c.ch((mo, 1), "- 12", "sel " + " ".join(str(i) for i in range(12)))
    c.col()

    def layer(var, label, g):
        # tap: in (always on) if it's silent now, out if it plays; aux + tap: back to auto (the piece decides)
        return [If("acauxheld", [V(var, "1"), Toast(label + " auto")],
                   [If(f"{g} > 0.01", [V(var, "0"), Toast(label + " out")], [V(var, "2"), Toast(label + " in")])]),
                V("acfade", _S.LFADE), Call("ac-layers")]

    def page(p):
        return [V("acpage", str(p)), If("acsetup", [V("acsetup", "0"), Send("ac-save"), Call("ac-oledall")]),
                Call("ac-oledpop")]

    low = [page(p) for p in PAGE_KEYS]
    # low F: SENDS 1, and again SENDS 2
    low[5] = [V("acpage", "if(acpage == 3 && acsetup == 0, 4, 3)"),
              If("acsetup", [V("acsetup", "0"), Send("ac-save"), Call("ac-oledall")]), Call("ac-oledpop")]
    low += [
        [V("acroothold", "1"), Toast("root: play a note or turn knob 1")],
        [Call("ac-resolvetoggle")],
        [V("acrr", "0"), Arm("ac-reroll", "500", stop="ac-rrstop")],
        [V("acsec", "acsec+1"), Call("ac-section"), Toast("next section")],
        [V("acsecfz", "1 - acsecfz"), If("acsecfz", [Toast("section held")], [Toast("section moves on")]),
         Call("ac-oledbottom")],
    ]
    for i, lk in enumerate(LAYER_KEYS):
        proc(c, f"ac-laykey{i}", layer(*lk))
    top = [[Call(f"ac-laykey{i}")] for i in range(len(LAYER_KEYS))] + [
        [If("acauxheld", [Call("ac-capture")],
            [V("acinmode", "(acinmode+1) % 8"), Call("ac-inputupd"), Call("ac-inmodetoast"), Call("ac-scr5")])],
        [If("acauxheld", [X("1; 0", "v acanp", "v acanheld"), Arm("ac-ancheld", "800", stop="ac-ancstop")],
            [Call("ac-freezetoggle")])],
        [If("acauxheld", [Call("ac-modetoggle")], [Call("ac-startstop")])],
        [],          # top B: on its release (above)
    ]
    assert len(low) == len(LOW_KEYS) and len(top) == len(TOP_KEYS)
    for i, f in enumerate(low):
        b = c.obj("t b")
        c.c(lsel, i, b, 0)
        # aux + a low key: that SETUP page
        run_steps(c, (b, 0), [If("acauxheld", [If(f"{i} < {NSET}", [
            V("acsetup", "1"), V("acsetpg", str(i)), Call("ac-oledsetup")])], f)])
        c.col(170)
    for i, f in enumerate(top):
        b = c.obj("t b")
        c.c(tsel, i, b, 0)
        run_steps(c, (b, 0), f)
        c.col(170)
    # top B held 0.6 s with no key: COMPARE (the slot as saved) until it is let go
    proc(c, "ac-cmphold", [If("acbdown && acbused == 0", [V("acbcmp", "1"), Call("ac-cmpon")])])
    proc(c, "ac-ancheld", [V("acanheld", "1"), Call("ac-anchorset")])
    proc(c, "ac-rootset", [V("acpend", "acrootn"), Send("ac-keytoast"), Call("ac-chordnext")])
    # low A held: another next chord now, and again every 0.7 s while it is held
    proc(c, "ac-reroll", [V("acrr", "1"), Call("ac-chordnext"), Arm("ac-reroll", "700", stop="ac-rrstop")])
    proc(c, "ac-chordnow", [Call("ac-change"), Toast("chord change")])
    proc(c, "ac-resolvetoggle", [V("acres", "1 - acres"), Call("ac-resolveupd")])
    proc(c, "ac-resolveupd", [Call("ac-change"),
                              If("acres", [Toast("resolve - open fifths")], [Toast("resolve released")])])
    proc(c, "ac-freezetoggle", [
        V("acvfreeze", "1-acvfreeze"), V("acfreeze", "acvfreeze"), Call("ac-freezeupd"), Call("ac-revupd"),
        If("acvfreeze", [Toast("freeze - reverb and cloud")], [Toast("freeze released")]), Call("ac-oledbottom")])
    Line("ac-keytoast", "list next key $1", [("s", "acpend", NOTE_NAMES)], "ac-toast")(c)
    Line("ac-inmodetoast", "list input $1", [("s", "acinmode", INMODES)], "ac-toast")(c)
    # aux: knob page
    a = c.ch(c.recv("aux"), "sel 0")
    b = c.to((a, 1), "t b")
    run_steps(c, (b, 0), [X("1; 0; acnow", "v acauxheld", "v acauxused", "v acauxt")])
    run_steps(c, (a, 0), [V("acauxheld", "0"), If("acauxused == 0", [If("acsetup", [
        V("acsetpg", f"(acsetpg + 1) % {NSET}"), Call("ac-oledsetup")], [
        V("acpage", f"(acpage+1) % {NP}"), Call("ac-oledpop")])])])
    f = c.ch(c.recv("fs"), "sel 0")
    c.c(c.to((f, 1), "t b"), 0, c.obj("s ac-change"), 0)
    return c


def screen():
    c = Canvas("screen", w=3600)
    c.comment("Line 1 state, 2 key/scale/voicing, 3 pad timbres + texture (and toasts), 4-5 the knob page")
    proc(c, "ac-scr", [Call(f"ac-scr{i}") for i in range(1, 6)])
    # line 1
    s1 = c.ch(c.recv("ac-scr1"), "expr if(acready && acstopped, 4, if(acstopped, 3, if(acended || acrun==0, 2, acmode)))",
              "sel 0 1 2 3 4")
    c.c(c.m((s1, 3), "list STOPPED - A# start"), 0, c.obj("s ac-txt1"), 0)
    c.c(c.to((s1, 4), "t b"), 0, c.obj("s ac-scr1r"), 0)
    c.c(c.to((s1, 0), "t b"), 0, c.obj("s ac-scr1d"), 0)
    c.c(c.to((s1, 1), "t b"), 0, c.obj("s ac-scr1c"), 0)
    c.c(c.m((s1, 2), "list FIN - B new piece"), 0, c.obj("s ac-txt1"), 0)
    c.col()
    Line("ac-scr1r", "list READY $1 - A# start", [("s", "acmode", ["DRIFT", "COMPOSE"])], "ac-txt1")(c)
    Line("ac-scr1d", "list DRIFT $1 $2",
         [("s", "acrole", ROLES), ("f", "acseed % 10000")], "ac-txt1")(c)
    Line("ac-scr1c", "list COMP $1 of $2 $3",
         [("f", "acsec+1"), ("f", "acnsec"),
          ("s", "acrole", ROLES)], "ac-txt1")(c)
    Line("ac-scr2", "list $1 $2 $3",
         [("s", "int(actonic) % 12", NOTE_NAMES), ("s", "acsci", [n for n, _ in SCALES]),
          ("s", "acfam", [n for n, _, _ in FAMILIES])], "ac-txt2")(c)
    # the OLED's line 2: the chord now and the next one (key and scale are on the bottom line)
    Line("ac-scr2", "list $1 > $2", [("s", "acchn", CHORD_NAMES), ("s", "acnxn", CHORD_NAMES)], "ac-oledtop")(c)
    Line("ac-scr3", "list $1 $2 $3 $4 $5",
         [("s", f"acflav[{k}]", FLAVOURS) for k in range(4)] + [("s", "actex1", TEXTURES)], "ac-txt3")(c)
    for ln in (4, 5):
        s = c.ch(c.recv(f"ac-scr{ln}"), "expr acpage", "sel " + " ".join(str(i) for i in range(NP)))
        for i in range(NP):
            c.c(c.to((s, i), "t b"), 0, c.obj(f"s ac-scr{ln}p{i}"), 0)
    c.col()
    Line("ac-scr4p0", "list Dens $1 Tide $2", [("f", "int(acdens*100)"), ("f", "int(actide*100)")], "ac-txt4")(c)
    Line("ac-scr5p0", "list Colr $1 In $2 $3",
         [("f", "int(accolor*100)"), ("f", "int(acinput*100)"),
          ("s", "if(acinmode==0, 8 + acinclass, acinmode)", INMODES + ["auto", "pitched", "plucked", "texture"])],
         "ac-txt5")(c)
    Line("ac-scr4p1", "list Mix $1 Verb $2", [("f", "int(acrvmix*100)"),
                                              ("s", "if(acrvtype < 0.2, 0, 1 + min(3, int((acrvtype-0.2)/0.2)))", VERBS)],
         "ac-txt4")(c)
    Line("ac-scr5p1", "list Time $1 s Tone $2",
         [("f", "int(1.5 + 28.5*pow(acrvtime, 1.5))"), ("f", "int(acrvtone*100)")], "ac-txt5")(c)
    Line("ac-scr4p2", "list Len $1 min Weird $2", [("f", "int(5 + 25*aclen)"), ("f", "int(acweird*100)")],
         "ac-txt4")(c)
    Line("ac-scr5p2", "list Mot $1 Rhy $2", [("f", "int(acmotion*100)"), ("f", "int(acrhythm*100)")], "ac-txt5")(c)
    # the SENDS pages: "Drone 50 Pads 50" ...
    for pg in range(3, len(PAGES)):
        for ln, pair in ((4, PAGES[pg][:2]), (5, PAGES[pg][2:])):
            Line(f"ac-scr{ln}p{pg}", "list " + " ".join(f"{lab} ${i + 1}" for i, (lab, _, _) in enumerate(pair)),
                 [("f", f"int({n}*100)") for _, n, _ in pair], f"ac-txt{ln}")(c)
    # LED: green drifting, blue composing, off when finished; white flash on a chord change
    led = c.obj("s led")
    lc = c.ch(c.recv("ac-led"), "expr if(acended || acstopped, 0, if(acmode, 5, 3))")
    c.c(lc, 0, led, 0)
    fl = c.to(c.recv("ac-flash"), "t b b")
    c.c(c.to((fl, 0), "delay 150"), 0, c.obj("s ac-led"), 0)
    c.c(c.m((fl, 1), "7"), 0, led, 0)
    return c
