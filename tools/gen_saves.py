"""SAVES (SETUP page 13) and the factory pieces.

saves.txt holds one line per saved slot: the slot number, then SAVE_SCALARS, SAVE_ARRAYS and SAVE_EXTRA (all in
gen_setup). A load sets them (the knobs through the morph engine, gen_perform) and prepares the piece; an empty slot
1-6 loads a factory piece from factory.txt, written at build time by factory_rows()."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line, Toast
from data import FACTORY, PAGES, NK
from gen_setup import (GLOBALS, KNOBS, SAVE_SCALARS, SAVE_ARRAYS, SAVE_EXTRA, SAVE_EXTRA_AT, SAVE_LEN, SOUND_ONLY,
                       SMORPH, SFORMS, SSCALES, SCHORDS, SATMS, SDRONES, SPADS, SBELLS, SMOTS, STEMPOS, SSUBS, _pick)


def factory_rows():
    """factory.txt: one save line (without the slot number) per factory piece"""
    import gen_brain as B
    import gen_live as L
    d = {}
    for g in (B.GLOBALS, L.GLOBALS, GLOBALS):
        d.update(g)
    d.update({n: v for p in PAGES for _, n, v in p})
    d.update({n: 1 for n in ("acmdrone", "acmsub", "acmpad", "acmbell", "acmmotion", "acmtex", "acmatm", "acmcloud")})
    d.update(dict(SAVE_EXTRA))
    lists = dict(acsform=SFORMS, acsclc=SSCALES, acchdc=SCHORDS, acsatm=SATMS, acsdrone=SDRONES, acspad=SPADS,
                 acsbell=SBELLS, acsmot=SMOTS, acstempo=STEMPOS, acssub=SSUBS)
    arrdef = dict(acsroles=8, acslens=1, acssp=0, acsst=0, acslv=1)
    rows = []
    for name, seed, over in FACTORY:
        v = dict(d, acseed=seed)
        for k, x in over.items():
            v[k] = lists[k].index(x) if isinstance(x, str) else x
        row = [v[n] for n in SAVE_SCALARS]
        for name_, n in SAVE_ARRAYS:
            row += [arrdef[name_]] * n
        row += [v[n] for n, _ in SAVE_EXTRA]
        assert len(row) == SAVE_LEN
        rows.append(" ".join(f"{x:g}" for x in row) + ";")
    return "\n".join(rows) + "\n"


def saves():
    """SAVES (SETUP page 13): saves.txt holds one line per saved slot: the slot number, then SAVE_SCALARS and
    SAVE_ARRAYS. Loading sets them all and prepares the piece from its seed (ready while stopped)."""
    c = Canvas("saves", w=2600)
    c.comment("Saves: slot lines in saves.txt (slot, seed, mode, knobs, sounds, form, sections, layer states)")
    td = c.obj("text define acsaves")
    c.c(c.m(c.recv("ac-loadsettings"), "read saves.txt"), 0, td, 0)
    c.c(c.ch(c.recv("ac-loadsettings"), "delay 5"), 0, c.obj("s ac-slotcheck"), 0)
    # is the slot saved?
    # (a saved slot: its name, key and scale, read for the SAVES page)
    ex = [n for n, _ in SAVE_EXTRA]
    at = lambda n: SAVE_EXTRA_AT + ex.index(n)
    sc = c.ch(c.recv("ac-slotcheck"), "expr acslot + 1", "text search acsaves 0", "t b f")
    c.c(c.to((sc, 1), "expr $f1 >= 0"), 0, c.obj("v acslotfull"), 0)
    mo = c.to((sc, 1), "moses 0")
    run_steps(c, (mo, 0), [X("0; -1", "v acslnm", "v acslkey")])
    rd = c.ch((mo, 1), "text get acsaves", "list split 1")
    t3 = c.to((rd, 1), "t b l b")
    run_steps(c, (t3, 2), [T("acslotbuf", at("acsname"), "0"), T("acslotbuf", at("acstonic"), "-1")])
    c.c((t3, 1), 0, c.obj("array set acslotbuf"), 0)
    run_steps(c, (t3, 0), [X(f"acslotbuf[{at('acsname')}]; acslotbuf[{at('acstonic')}]; acslotbuf[{at('acsscale')}]",
                             "v acslnm", "v acslkey", "v acslsc")])
    c.c(sc, 0, c.obj("s ac-oledsetupq"), 0)
    c.col()
    # save: the values into acsavebuf, then the line (slot first) replaces the slot's line, or is added
    off = len(SAVE_SCALARS)
    steps = [T("acsavebuf", i, n) for i, n in enumerate(SAVE_SCALARS)]
    for name, n in SAVE_ARRAYS:
        steps += [Loop(str(n), "aci", [T("acsavebuf", f"{off} + aci", f"{name}[int(aci)]")])]
        off += n
    steps = [X("int(actonic) % 12; acsci", "v acstonic", "v acsscale")] + steps
    off2 = SAVE_EXTRA_AT
    steps += [T("acsavebuf", off2 + i, n) for i, (n, _) in enumerate(SAVE_EXTRA)]
    proc(c, "ac-savepiece", steps + [Send("ac-savewrite"), Call("ac-slotcheck"), Call("ac-basesetnow"),
                                     V("acslotcur", "acslot"), Send("ac-savesay")])
    w = c.to(c.recv("ac-savewrite"), "t b b b")
    ts = c.obj("text set acsaves")
    c.c(c.ch((w, 2), "expr acslot + 1", "text search acsaves 0", "expr if($f1 < 0, 1e+06, $f1)"), 0, ts, 1)
    lp = c.obj("list prepend")
    c.c(c.to((w, 1), "expr acslot + 1"), 0, lp, 1)
    c.c(c.ch((w, 1), "t b", "array get acsavebuf"), 0, lp, 0)
    c.c(c.to(lp, "list trim"), 0, ts, 0)
    c.c(c.m((w, 0), "write saves.txt"), 0, td, 0)
    c.col()
    # load: the slot's line, or for an empty slot 1-6 a factory piece (factory.txt), or nothing
    ft = c.obj("text define acfactory")
    c.c(c.m(c.recv("ac-loadsettings"), "read factory.txt"), 0, ft, 0)
    ld = c.ch(c.recv("ac-loadpiece"), "expr acslot + 1", "text search acsaves 0", "moses 0")
    c.c(c.to((ld, 0), "t b"), 0, c.obj("s ac-loadfact"), 0)
    gl = c.ch((ld, 1), "text get acsaves", "list split 1")
    c.c((gl, 1), 0, c.obj("s ac-loadrow"), 0)
    fg = c.ch(c.recv("ac-loadfact2"), "text get acfactory")
    c.c(fg, 0, c.obj("s ac-loadrow"), 0)
    proc(c, "ac-loadfact", [If(f"acslot < {len(FACTORY)}", [SendL("ac-loadfact2", ["acslot"])], [Toast("slot is empty")])])
    # (the fields a line saved before them lacks keep their defaults)
    row = c.to(c.recv("ac-loadrow"), "t b l b")
    run_steps(c, (row, 2), [T("acsavebuf", SAVE_EXTRA_AT + i, str(d)) for i, (_, d) in enumerate(SAVE_EXTRA)])
    c.c((row, 1), 0, c.obj("array set acsavebuf"), 0)
    c.c((row, 0), 0, c.obj("s ac-loadapply"), 0)
    knobs = KNOBS
    off = len(SAVE_SCALARS)
    piece_only = lambda n: n not in SOUND_ONLY
    # the knobs go to the morph's target (In stays); everything else is set; Recall "sound only" leaves the seed,
    # the music, the form and the sections as they are
    steps = [Loop(str(NK), "aci", [T("acmto", "aci", "acparams[int(aci)]")])]
    for i, n in enumerate(SAVE_SCALARS):
        if n in knobs:
            if n != "acinput":
                steps += [T("acmto", knobs.index(n), f"acsavebuf[{i}]")]
        elif piece_only(n):
            steps += [If("acrecall == 0 || acstopped", [V(n, f"acsavebuf[{i}]")])]
        else:
            steps += [V(n, f"acsavebuf[{i}]")]
    arr = []
    for name, n in SAVE_ARRAYS:
        arr += [Loop(str(n), "aci", [T(name, "aci", f"acsavebuf[int({off} + aci)]")])]
        off += n
    steps += [If("acrecall == 0 || acstopped", arr)]
    for i, (n, _) in enumerate(SAVE_EXTRA):
        if n in knobs:
            steps += [T("acmto", knobs.index(n), f"acsavebuf[{SAVE_EXTRA_AT + i}]")]
        else:
            steps += [V(n, f"acsavebuf[{SAVE_EXTRA_AT + i}]")]
    # the knobs glide over Morph (at once while stopped); the anchor lets go; this is the slot COMPARE plays
    steps += [Call("ac-verbcut"), V("acmdur", f"if(acstopped, 0, {_pick('acmorph', SMORPH)})"), Call("ac-morphgo"),
              Call("ac-basesetto"), V("acancs", "0"), V("acslotcur", "acslot"),
              V("acknown0", "0"), V("acknown1", "0"), V("acknown2", "0"), V("acknown3", "0"),
              Call("ac-sendupd"), Call("ac-revupd"), Call("ac-stereo"), Call("ac-rvcolour"), Call("ac-sinkupd"),
              Call("ac-pumpupd"), Call("ac-sparkupd"), Call("ac-jourupd"), Call("ac-sndovr"), Call("ac-padpick"), V("acfade", "3000"),
              Call("ac-layers"),
              # a piece: from its seed, ready while stopped, playing otherwise
              If("acrecall == 0 || acstopped", [V("acmode", "acmodesel == 0"), If("acstopped", [V("acready", "1")]),
                                                SendL("ac-setseed", ["acseed"])]),
              If("acslotfull", [Send("ac-loadsay")], [Send("ac-factsay")]), Send("ac-dirty")]
    proc(c, "ac-loadapply", steps)
    Line("ac-savesay", "list saved to slot $1", [("f", "acslot + 1")], "ac-toast")(c)
    Line("ac-loadsay", "list loaded slot $1", [("f", "acslot + 1")], "ac-toast")(c)
    Line("ac-factsay", "list slot $1: $2", [("f", "acslot + 1"), ("s", "acslot", [n for n, _, _ in FACTORY] + ["-"] * 10)],
         "ac-toast")(c)
    # the SETUP screen, if it shows
    run_steps(c, (c.recv("ac-oledsetupq"), 0), [If("acsetup", [Call("ac-oledsetup")])])
    return c
