"""SETUP (hold aux 1 s), settings saved in the patch folder, MIDI clock and notes out, MIDI clock in.

SETUP page 1: MIDI out (off / clock / clock+notes / notes), Sync (internal / follow), Keys (auto / play /
functions), Bloom (clean / vintage). Page 2: Follow (how much the chords follow you), MPE bend range,
MIDI out base channel, breath curve. Aux tap = the other page, hold aux 1 s = leave (and save)."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line, Arm, Toast
from gen_oled import Fill, OSC, FLIP, gated_text
from data import PAGES

GLOBALS = dict(acmout=1, acsync=0, acvintage=0, acoutch=1, accurve=1.2, acsk=0, acsv=0, acextbpm=60,
               acrtb=0, acoutroot=-1, acclkon=0, acsaved=0)
ARRAYS = dict(acout=4)
NP = len(PAGES)
SETTINGS = [n for p in PAGES for _, n, _ in p] + ["acmout", "acsync", "acforce", "acvintage", "acfollow", "acnbr",
                                                  "acoutch", "accurve", "acmono", "acwidth", "acpanmot"]
MOUT = ["off", "clock", "clock+notes", "notes"]
BENDS = [12, 24, 48, 96]


def settings():
    c = Canvas("settings", w=2400)
    c.comment("settings.txt: the 12 knob values and the 8 SETUP values, one line. Loaded at start-up, "
              "saved 3 s after a change and when SETUP closes.")
    td = c.obj("text define acsettings")
    r = c.recv("ac-loadsettings")
    t = c.to(r, "t b b")
    c.c(c.m((t, 1), "read settings.txt"), 0, td, 0)
    mo = c.ch((t, 0), "text size acsettings", "moses 1")
    got = c.ch(c.m((mo, 1), "0"), "text get acsettings")
    ln = c.to(got, "t l l")
    c.c(c.ch((ln, 1), "list split 12"), 0, c.obj("array set acparams"), 0)
    sp = c.ch((ln, 0), "list split 12")
    up = c.to((sp, 1), "unpack " + " ".join(["f"] * (len(SETTINGS) - 12)))
    for i, n in enumerate(SETTINGS[12:]):
        c.c(up, i, c.obj("v " + n), 0)
    c.col()
    # knob values out of the array into their values
    tb = c.to((ln, 0), "t b")
    run_steps(c, (tb, 0), [Loop("12", "aci", [SendL("ac-pset", ["aci", "acparams[int(aci)]"])]),
                           SendL("ac-vintage", ["acvintage"]), SendL("ac-brcurve", ["accurve"])])
    rt = c.to(c.recv("ac-pset"), "route " + " ".join(str(i) for i in range(12)))
    for i, n in enumerate(SETTINGS[:12]):
        c.c(rt, i, c.obj("v " + n), 0)
    c.col()
    # save (3 s after the last change)
    d = c.to(c.recv("ac-dirty"), "delay 3000")
    ex = c.obj("expr " + "; ".join(SETTINGS[12:]))
    c.c(d, 0, c.obj("s ac-save"), 0)
    tsv = c.to(c.recv("ac-save"), "t b b")
    pk = c.obj("pack " + " ".join(["f"] * (len(SETTINGS) - 12)))
    for i in range(len(SETTINGS) - 13, -1, -1):
        c.c(ex, i, pk, i)
    ag = c.obj("array get acparams")
    la = c.obj("list append")
    c.c(tsv, 1, ex, 0)
    c.c(pk, 0, la, 1)
    c.c(tsv, 0, ag, 0)
    c.c(ag, 0, la, 0)
    tl = c.to(la, "t b l")
    c.c(c.ch((tl, 1), "list prepend set", "list trim"), 0, td, 0)
    c.c(c.m((tl, 0), "write settings.txt"), 0, td, 0)
    return c


def setup():
    c = Canvas("setup", w=2600)
    c.comment("SETUP: hold aux 1 s. Knobs set the 4 items of the page (absolute), aux tap = other page.")
    # aux held 1 s without a key: enter / leave SETUP
    d = c.obj("delay 1000")
    c.c(c.to((c.ch(c.recv("aux"), "sel 0"), 1), "t b"), 0, d, 0)
    c.c(c.m(c.ch(c.recv("aux"), "sel 0"), "stop"), 0, d, 0)
    run_steps(c, (d, 0), [If("acauxheld && acauxused == 0", [
        V("acauxused", "1"), V("acsetup", "1 - acsetup"), V("acsetpg", "0"),
        If("acsetup", [Call("ac-oledsetup")], [Send("ac-save"), Call("ac-oledall"), Toast("settings saved")]),
    ])])
    c.col()
    # knob values in SETUP arrive here as "knob value"
    up = c.to(c.recv("ac-setknob"), "unpack f f")
    c.c(up, 1, c.obj("v acsv"), 0)
    tb = c.to(up, "t b f")
    c.c(tb, 1, c.obj("v acsk"), 0)
    item = "acsetpg*4 + acsk"
    run_steps(c, (tb, 0), [
        If(f"{item} == 0", [V("acmout", "int(acsv*3.99)"), If("acmout == 0 || acmout == 3", [Call("ac-clockstop")],
                                                               [Call("ac-clockstart")])]),
        If(f"{item} == 1", [V("acsync", "acsv > 0.5"), SendL("ac-bpm", ["acbpm"])]),
        If(f"{item} == 2", [V("acforce", "int(acsv*2.99) - 1")]),
        If(f"{item} == 3", [V("acvintage", "acsv > 0.5"), SendL("ac-vintage", ["acvintage"])]),
        If(f"{item} == 4", [V("acfollow", "acsv")]),
        If(f"{item} == 5", [V("acnbr", f"if(acsv < 0.25, 12, if(acsv < 0.5, 24, if(acsv < 0.75, 48, 96)))")]),
        If(f"{item} == 6", [V("acoutch", "1 + int(acsv*12.99)")]),
        If(f"{item} == 7", [V("accurve", "0.5 + 1.5*acsv"), SendL("ac-brcurve", ["accurve"])]),
        If(f"{item} == 8", [V("acmono", "acsv > 0.5"), Call("ac-stereo")]),
        If(f"{item} == 9", [V("acwidth", "0.5 + acsv"), Call("ac-stereo")]),
        If(f"{item} == 10", [V("acpanmot", "acsv"), Call("ac-stereo")]),
        Call("ac-oledsetup"), Send("ac-dirty"),
    ])
    c.col()
    proc(c, "ac-oledsetup", [
        Fill(0, 0, 128, 64, 0),
        Call("ac-setl0"), Call("ac-setl1"), Call("ac-setl2"), Call("ac-setl3"), Call("ac-setl4"),
        FLIP,
    ])
    Line("ac-setl0", "list SETUP $1 of 3 - hold aux", [("f", "acsetpg + 1")], "ac-sett0")(c)
    # page-dependent rows: two Lines per row, chosen by the page
    defs = [
        (1, ("list 1 MIDI out $1", [("s", "acmout", MOUT)]), ("list 1 Follow you $1", [("f", "int(acfollow*100)")]),
         ("list 1 Output $1", [("s", "acmono", ["stereo wide", "mono"])])),
        (2, ("list 2 Sync $1", [("s", "acsync", ["internal", "follow clock"])]),
            ("list 2 MPE bend $1", [("f", "acnbr")]), ("list 2 Width $1", [("f", "int(acwidth*100)")])),
        (3, ("list 3 Keys $1", [("s", "acforce + 1", ["auto", "play notes", "functions"])]),
            ("list 3 MIDI out ch $1", [("f", "acoutch")]), ("list 3 Pan motion $1", [("f", "int(acpanmot*100)")])),
        (4, ("list 4 Bloom $1", [("s", "acvintage", ["clean", "vintage"])]),
            ("list 4 Breath curve $1", [("f", "int(accurve*100)")]), ("list 4 -", [])),
    ]
    for k, a, b, d in defs:
        s = c.ch(c.recv(f"ac-setl{k}"), "expr acsetpg", "sel 0 1 2")
        for j, (ln, parts) in enumerate((a, b, d)):
            c.c(c.to((s, j), "t b"), 0, c.obj(f"s ac-setl{k}{'abc'[j]}"), 0)
            if parts:
                Line(f"ac-setl{k}{'abc'[j]}", ln, parts, f"ac-sett{k}")(c)
            else:
                c.c(c.m(c.recv(f"ac-setl{k}{'abc'[j]}"), ln), 0, c.obj(f"s ac-sett{k}"), 0)
    for k in range(5):
        gated_text(c, f"ac-sett{k}", "acsetup", 0, 2 + k * 12)
    # aux tap in SETUP: the other page
    return c


def midi_out():
    c = Canvas("midi-out", w=2600)
    c.comment("MIDI out: raw bytes and notes go through ac-midibyte / ac-noteout (so tests can watch them). "
              "Clock: 24 ticks a beat, Start when a piece starts, Stop at its end. Notes: chords (base ch), "
              "drone (ch+1), bells (ch+2), motion (ch+3).")
    mo = c.obj("midiout")
    c.c(c.recv("ac-midibyte"), 0, mo, 0)
    no = c.obj("noteout")
    up = c.to(c.recv("ac-noteout"), "unpack f f f")
    c.c(up, 2, no, 2)
    c.c(up, 1, no, 1)
    c.c(up, 0, no, 0)
    c.col()
    clk = "(acmout == 1 || acmout == 2) && acsync == 0"
    proc(c, "ac-tick", [If(clk + " && acclkon", [SendL("ac-midibyte", ["248"])])])
    proc(c, "ac-clockstart", [If(clk, [SendL("ac-midibyte", ["250"]), V("acclkon", "1")])])
    proc(c, "ac-clockstop", [If("acclkon", [SendL("ac-midibyte", ["252"]), V("acclkon", "0")]), Call("ac-notesoff")])
    notes = "acmout >= 2"
    # chords: the 4 pad pitches (rounded), the old ones off first
    proc(c, "ac-outchord", [If(notes + " && acrun", [Loop("4", "aci", [
        If("acout[int(aci)] > 0", [SendL("ac-noteout", ["acout[int(aci)]", "0", "acoutch"])]),
        T("acout", "aci", "int(acnew[int(aci)] + 0.5)"),
        SendL("ac-noteout", ["acout[int(aci)]", "64", "acoutch"]),
    ]), If("acoutroot != int(actonic)", [
        If("acoutroot > 0", [SendL("ac-noteout", ["acoutroot", "0", "acoutch + 1"])]),
        V("acoutroot", "int(actonic)"), SendL("ac-noteout", ["acoutroot", "70", "acoutch + 1"])])])])
    proc(c, "ac-notesoff", [Loop("4", "aci", [If("acout[int(aci)] > 0", [
        SendL("ac-noteout", ["acout[int(aci)]", "0", "acoutch"]), T("acout", "aci", "0")])]),
        If("acoutroot > 0", [SendL("ac-noteout", ["acoutroot", "0", "acoutch + 1"]), V("acoutroot", "-1")])])
    # bells and motion: notes with a length
    for rc, ch, dur, sel in (("ac-bell", 2, 500, "$1 $2"), ("ac-mnote", 3, 150, "$1 $2")):
        sp = c.obj("spigot")
        c.c(c.to(c.recv("ac-frame"), "expr " + notes), 0, sp, 1)
        c.c(c.recv(rc), 0, sp, 0)
        u = c.to(sp, "unpack f f")
        mk = c.obj(f"makenote 64 {dur}")
        c.c(c.to((u, 1), "expr int($f1*110)"), 0, mk, 1)
        c.c(c.to(u, "expr int($f1 + 0.5)"), 0, mk, 0)
        pk = c.obj("pack f f f")
        c.c(c.to(c.recv("ac-frame"), f"expr acoutch + {ch}"), 0, pk, 2)
        c.c(mk, 1, pk, 1)
        c.c(mk, 0, pk, 0)
        c.c(pk, 0, c.obj("s ac-noteout"), 0)
        c.col(200)
    return c


def clock_in():
    c = Canvas("clock-in", w=1800)
    c.comment("Follow an incoming MIDI clock (SETUP Sync = follow clock): its ticks drive Amble's rhythm, Start "
              "restarts the bar, Stop pauses the rhythm layers; the tempo is measured")
    rti = c.obj("midirealtimein")
    c.c(rti, 0, c.obj("s ac-rtin"), 0)
    up = c.to(c.recv("ac-rtin"), "t f f")
    tm = c.obj("timer")
    sel = c.to(up, "sel 248 250 251 252")
    tk = c.to((sel, 0), "t b b b")
    c.c(tk, 2, tm, 1)
    c.c(tk, 1, tm, 0)
    c.c(tm, 0, c.obj("v acrtb"), 0)
    run_steps(c, (tk, 0), [If("acsync", [
        V("acextbpm", "if(acrtb > 2 && acrtb < 200, 0.95*acextbpm + 0.05*60000/(24*acrtb), acextbpm)"),
        Send("ac-tick"),
        If("int(actick) % 24 == 0", [V("acbpm", "acextbpm")]),
    ])])
    # the timer measures from one tick to the next: read (right inlet) then restart (left)
    run_steps(c, (sel, 1), [If("acsync", [V("actick", "-1"), Toast("clock start")])])
    run_steps(c, (sel, 3), [If("acsync", [Toast("clock stop")])])
    return c
