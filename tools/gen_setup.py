"""SETUP (hold aux 1 s), settings saved in the patch folder, MIDI clock and notes out, MIDI clock in.

SETUP page 1: MIDI out (off / tempo only / tempo+notes / notes only), Sync (internal / follow), Keys (auto / play /
functions), Bloom (clean / vintage). Page 2: Follow (how much the chords follow you), MPE bend range,
MIDI out base channel, breath curve. Page 3: output, width, pan motion, tempo range. Page 4: which
parts go out as MIDI notes, the arp chord octave. Page 5 (SOUNDS): pad type, drone, texture, character
(auto or your choice, applied at once). Page 6 (MUSIC): key, scale, chord voicing (auto or fixed), the bar pulse.
Page 7 (MIDI IN): where notes go, what breath does, what pressure does, the breath level. Page 8 (CC MAP):
what each CC does, the last CC in, the vibrato rate. Page 9 (VOICES): the bells' and the motion's engines. Aux tap = the other page, hold aux 1 s = leave (and save)."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line, Arm, Toast
from gen_oled import Fill, OSC, FLIP, gated_text
from data import PAGES, TEMPOS, FILE_KNOBS, STRIKES, FLAVOURS, DRONES, TEXTURES, CHARACTERS, SCALES, FAMILIES, NOTE_NAMES

GLOBALS = dict(acmout=1, acsync=0, acvintage=0, acoutch=1, accurve=1.2, acsk=0, acsv=0, acextbpm=60,
               acrtb=0, acoutroot=-1, acclkon=0, acsaved=0, actrange=0,
               acmparts=0, acarpoct=48, acoutbass=-1, acload=0, acloadtest=0, acshedt=0, acldraw=0, acguard=1,
               ackeyc=0, acsclc=0, acchdc=0, acpulc=2, acroute=0, acbrto=0, acpressto=1, acccsel=0, aclastcc=0, aclastv=0, acvibr=5.5,
               acmap0=2, acmap1=1, acmap2=1, acmap3=1, acmap4=6, acmap5=0, acmap6=3, acsbell=0, acsmot=0)
ARRAYS = dict(acout=4, acarp=4)
NP = len(PAGES)
KNOBS = [n for p in PAGES for _, n, _ in p]
SETTINGS = KNOBS[:FILE_KNOBS] + ["acmout", "acsync", "acforce", "acvintage", "acfollow", "acnbr",
                                                  "acoutch", "accurve", "acmono", "acwidth", "acpanmot",
                                                  "actrange", "acmparts", "acarpoct", "acguard"] + KNOBS[FILE_KNOBS:] + \
           ["acspad", "acsdrone", "acstex", "acschar"] + \
           ["ackeyc", "acsclc", "acchdc", "acpulc", "acroute", "acbrto", "acpressto", "acvibr"] + \
           [f"acmap{j}" for j in range(7)] + ["acsbell", "acsmot"]
IN_IDX = [n for p in PAGES for _, n, _ in p].index("acinput")     # the In knob's slot in acparams
MOUT = ["off", "tempo only", "tempo+notes", "notes only"]
PARTS = ["all", "harmony", "arp only"]
OUTPUTS = ["stereo wide", "mono", "split"]   # split: pads + drone left, everything else right (mono stems)
NSET = 9                                   # SETUP pages
# SETUP page 5, SOUNDS: auto = the piece chooses; otherwise your choice, at once (to audition) and for every section
SPADS = ["auto", "raw"] + FLAVOURS
SDRONES = ["auto"] + DRONES
STEXS = ["auto"] + TEXTURES
SCHARS = ["auto"] + CHARACTERS
# SETUP page 6, MUSIC: a fixed key or scale stays (no modulation); the pulse is the drone and sub swell on the bar
SKEYS = ["auto"] + NOTE_NAMES
SSCALES = ["auto"] + [n for n, _ in SCALES]
SCHORDS = ["auto"] + [n for n, _, _ in FAMILIES]
PULSES = ["off", "gentle", "normal", "strong"]
PULSE_X = "if(acpulc == 0, 0, if(acpulc == 1, 0.45, if(acpulc == 2, 1, 1.6)))"
# SETUP page 7, MIDI IN: notes (MIDI in and the Organelle keys) play the live voice, or set the chord, the drone,
# strike the bells, or tune the cloud; breath shapes the live voice and the density, or one thing of the piece
ROUTES = ["voice", "chords", "drone", "bells", "cloud"]
BRTOS = ["voice+piece", "voice", "density", "brightness", "reverb", "swell"]
# SETUP page 8, CC MAP: what each CC (and channel / poly pressure, on page 7) does. breath = the breath path (Breath
# to); the voice targets act per note on the CC's channel (MPE; channel 1 = every voice); the piece targets move
# the knob of that name
CCS = [1, 2, 7, 11, 64, 71, 74]
CC_DEFAULTS = [2, 1, 1, 1, 6, 0, 3]          # mod = vibrato, 2 / 7 / 11 = breath, 64 = hold, 71 off, 74 = voice tone
TARGETS = ["off", "breath", "vibrato", "voice tone", "voice level", "voice type", "hold", "density", "colour",
           "reverb", "swell", "motion", "resolve"]
TARGET_KNOB = {7: "acdens", 8: "accolor", 9: "acrvmix", 11: "acmotion"}   # piece targets: the knob they move
CCSEL = "if(acccsel == 0, 1, " + ", ".join(f"if(acccsel == {j}, {n}" for j, n in enumerate(CCS) if j) + ", 0" + ")" * 7
MAPSEL = "if(acccsel == 0, acmap0, " + ", ".join(f"if(acccsel == {j}, acmap{j}" for j in range(1, 7)) + ", 0" + ")" * 7
BENDS = [12, 24, 48, 96]
# SETUP page 9, VOICES: the engine of the bells and of the motion (auto = the piece's)
SBELLS = ["auto"] + STRIKES
SMOTS = ["auto"] + STRIKES


def settings():
    c = Canvas("settings", w=2400)
    c.comment("settings.txt: the first 12 knob values, the SETUP values, then the SENDS knobs, one line. Loaded at start-up, "
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
    for i, n in enumerate(SETTINGS[12:]):     # SETUP values, then the knobs after the first 12 (older files lack them)
        c.c(up, i, c.obj("v " + n), 0)
    c.col()
    # knob values out of the array into their values
    tb = c.to((ln, 0), "t b")
    # the In knob (external audio) always starts at 0, whatever was saved: nothing reaches the input until
    # you turn it up
    run_steps(c, (tb, 0), [T("acparams", IN_IDX, "0")]
              + [T("acparams", FILE_KNOBS + i, n) for i, n in enumerate(KNOBS[FILE_KNOBS:])] + [
                           Loop(str(len(KNOBS)), "aci", [SendL("ac-pset", ["aci", "acparams[int(aci)]"])]),
                           Call("ac-sendupd"),
                           SendL("ac-vintage", ["acvintage"]), SendL("ac-brcurve", ["accurve"]),
                           SendL("ac-lvvibr", ["acvibr"])])
    rt = c.to(c.recv("ac-pset"), "route " + " ".join(str(i) for i in range(len(KNOBS))))
    for i, n in enumerate(KNOBS):
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
    ag = c.obj(f"array get acparams 0 {FILE_KNOBS}")
    la = c.obj("list append")
    c.c(tsv, 1, ex, 0)
    c.c(pk, 0, la, 1)
    c.c(tsv, 0, ag, 0)
    c.c(ag, 0, la, 0)
    tl = c.to(la, "t b l")
    c.c(c.ch((tl, 1), "list prepend set", "list trim"), 0, td, 0)
    c.c(c.m((tl, 0), "write settings.txt"), 0, td, 0)
    return c


def setup_rows():
    """SETUP: for each screen row 1..4, its item on pages 1..8 as (text with $n, parts). Also read by
    tools/manual.py, so the manual lists exactly these items."""
    return [
        (1, ("list 1 MIDI out $1", [("s", "acmout", MOUT)]), ("list 1 Follow you $1", [("f", "int(acfollow*100)")]),
         ("list 1 Output $1", [("s", "acmono", OUTPUTS)]),
         ("list 1 MIDI notes $1", [("s", "acmparts", PARTS)]),
            ("list 1 Pads $1", [("s", "acspad", SPADS)]),
            ("list 1 Key $1", [("s", "ackeyc", SKEYS)]),
            ("list 1 Notes to $1", [("s", "acroute", ROUTES)]),
            ("list 1 CC $1", [("f", CCSEL)]),
            ("list 1 Bells $1", [("s", "acsbell", SBELLS)])),
        (2, ("list 2 Sync $1", [("s", "acsync", ["internal", "follow clock"])]),
            ("list 2 MPE bend $1", [("f", "acnbr")]), ("list 2 Width $1", [("f", "int(acwidth*100)")]),
            ("list 2 Arp octave C$1", [("f", "acarpoct/12 - 1")]),
            ("list 2 Drone $1", [("s", "acsdrone", SDRONES)]),
            ("list 2 Scale $1", [("s", "acsclc", SSCALES)]),
            ("list 2 Breath to $1", [("s", "acbrto", BRTOS)]),
            ("list 2 to $1", [("s", MAPSEL, TARGETS)]),
            ("list 2 Motion $1", [("s", "acsmot", SMOTS)])),
        (3, ("list 3 Keys $1", [("s", "acforce + 1", ["auto", "play notes", "functions"])]),
            ("list 3 MIDI out ch $1", [("f", "acoutch")]), ("list 3 Pan motion $1", [("f", "int(acpanmot*100)")]),
            ("list 3 CPU $1% lite $2", [("f", "int(acload*100)"), ("f", "acshed")]),
            ("list 3 Texture $1", [("s", "acstex", STEXS)]),
            ("list 3 Chords $1", [("s", "acchdc", SCHORDS)]),
            ("list 3 Pressure to $1", [("s", "acpressto", TARGETS)]),
            ("list 3 Last CC $1 = $2", [("f", "aclastcc"), ("f", "aclastv")]),
            ("list 3 -", None)),
        (4, ("list 4 Bloom $1", [("s", "acvintage", ["clean", "vintage"])]),
            ("list 4 Breath curve $1", [("f", "int(accurve*100)")]), ("list 4 Tempo $1 $2-$3", [("s", "actrange", [n for n, _, _ in TEMPOS]),
                                          ("f", "actlo[int(actrange)]"), ("f", "acthi[int(actrange)]")]),
            ("list 4 CPU guard $1", [("s", "acguard", ["off", "on"])]),
            ("list 4 Character $1", [("s", "acschar", SCHARS)]),
            ("list 4 Pulse $1", [("s", "acpulc", PULSES)]),
            ("list 4 Breath in $1%", [("f", "int(aclbv*100)")]),
            ("list 4 Vib rate $1 Hz", [("f", "acvibr")]),
            ("list 4 -", None)),
    ]

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
                                                               [Call("ac-clockstart")]),
                            If("acmout < 2", [Call("ac-notesoff")], [Call("ac-outchord")])]),
        If(f"{item} == 1", [V("acsync", "acsv > 0.5"), SendL("ac-bpm", ["acbpm"])]),
        If(f"{item} == 2", [V("acforce", "int(acsv*2.99) - 1")]),
        If(f"{item} == 3", [V("acvintage", "acsv > 0.5"), SendL("ac-vintage", ["acvintage"])]),
        If(f"{item} == 4", [V("acfollow", "acsv")]),
        If(f"{item} == 5", [V("acnbr", f"if(acsv < 0.25, 12, if(acsv < 0.5, 24, if(acsv < 0.75, 48, 96)))")]),
        If(f"{item} == 6", [V("acoutch", "1 + int(acsv*12.99)")]),
        If(f"{item} == 7", [V("accurve", "0.5 + 1.5*acsv"), SendL("ac-brcurve", ["accurve"])]),
        If(f"{item} == 8", [V("acmono", f"int(acsv*{len(OUTPUTS) - 0.01})"), Call("ac-stereo")]),
        If(f"{item} == 9", [V("acwidth", "0.5 + acsv"), Call("ac-stereo")]),
        If(f"{item} == 10", [V("acpanmot", "acsv"), Call("ac-stereo")]),
        If(f"{item} == 11", [V("actrange", f"int(acsv*{len(TEMPOS) - 0.01})"), Call("ac-settempo")]),
        If(f"{item} == 12", [V("acmparts", f"int(acsv*{len(PARTS) - 0.01})"), Call("ac-notesoff"), Call("ac-outchord")]),
        If(f"{item} == 13", [V("acarpoct", "24 + 12*int(acsv*4.99)"), Call("ac-notesoff"), Call("ac-outchord")]),
        If(f"{item} == 15", [V("acguard", "acsv > 0.5"),
                             If("acguard == 0 && acshed > 0", [V("acshed", "0"), Call("ac-layers"), Call("ac-inputupd")])]),
    ] + [
        # SOUNDS: act only when the choice changes, so turning the knob within one choice does not re-pick
        If(f"{item} == {16 + j}", [V("acsnew", f"int(acsv*{len(opts) - 0.01})"), If(f"acsnew != {var}", [
            V(var, "acsnew")] + ([V("acflstag", "0"), Call("ac-padpick")] if j == 0 else []) + [
            Call("ac-sndovr"), V("acfade", "1500"), Call("ac-layers")])])
        for j, (var, opts) in enumerate((("acspad", SPADS), ("acsdrone", SDRONES), ("acstex", STEXS), ("acschar", SCHARS)))
    ] + [
        # MUSIC: a choice applies at the next chord, which comes now
        If(f"{item} == 20", [V("acsnew", f"int(acsv*{len(SKEYS) - 0.01})"), If("acsnew != ackeyc", [
            V("ackeyc", "acsnew"), If("ackeyc > 0", [V("acpend", "ackeyc - 1"), V("achome", "35 + ackeyc"),
                                                     Call("ac-change")])])]),
        If(f"{item} == 21", [V("acsnew", f"int(acsv*{len(SSCALES) - 0.01})"), If("acsnew != acsclc", [
            V("acsclc", "acsnew"), If("acsclc > 0", [V("acsci", "acsclc - 1"), Call("ac-loadscale"),
                                                     Call("ac-change")])])]),
        If(f"{item} == 22", [V("acsnew", f"int(acsv*{len(SCHORDS) - 0.01})"), If("acsnew != acchdc", [
            V("acchdc", "acsnew"), If("acchdc > 0", [V("acfam", "acchdc - 1"), Call("ac-change")])])]),
        If(f"{item} == 23", [V("acpulc", f"int(acsv*{len(PULSES) - 0.01})"), Call("ac-pulseupd")]),
        # MIDI IN
        If(f"{item} == 24", [V("acsnew", f"int(acsv*{len(ROUTES) - 0.01})"), If("acsnew != acroute", [
            Call("ac-allnotesoff"), V("acroute", "acsnew"), Call("ac-routehome"), V("acfade", "1500"),
            Call("ac-layers")])]),
        If(f"{item} == 25", [V("acsnew", f"int(acsv*{len(BRTOS) - 0.01})"), If("acsnew != acbrto", [
            V("acbrto", "acsnew"), Call("ac-brfxoff")])]),
        If(f"{item} == 26", [V("acpressto", f"int(acsv*{len(TARGETS) - 0.01})")]),
        # CC MAP: knob 1 picks a CC, knob 2 its target, knob 4 the vibrato rate
        If(f"{item} == 28", [V("acccsel", f"int(acsv*{len(CCS) - 0.01})")]),
        If(f"{item} == 29", [If(f"acccsel == {j}", [V(f"acmap{j}", f"int(acsv*{len(TARGETS) - 0.01})")])
                             for j in range(len(CCS))] + [If("achold && " + " && ".join(f"acmap{j} != 6" for j in range(7))
                                                            + " && acpressto != 6", [V("achold", "0"), Call("ac-holdoff")])]),
        If(f"{item} == 31", [V("acvibr", "0.5*int(6 + 10*acsv)"), SendL("ac-lvvibr", ["acvibr"])]),
        # VOICES: the bells' and the motion's engine, crossfaded at once
    ] + [
        If(f"{item} == {32 + j}", [V("acsnew", f"int(acsv*{len(opts) - 0.01})"), If(f"acsnew != {var}", [
            V(var, "acsnew"), V("acfade", "600"), Call("ac-layers")])])
        for j, (var, opts) in enumerate((("acsbell", SBELLS), ("acsmot", SMOTS)))
    ] + [
        Call("ac-oledsetup"), Send("ac-dirty"),
    ])
    c.col()
    proc(c, "ac-oledsetup", [
        Fill(0, 0, 128, 64, 0),
        Call("ac-setl0"), Call("ac-setl1"), Call("ac-setl2"), Call("ac-setl3"), Call("ac-setl4"),
        FLIP,
    ])
    Line("ac-setl0", f"list SETUP $1 of {NSET} - hold aux", [("f", "acsetpg + 1")], "ac-sett0")(c)
    # page-dependent rows: two Lines per row, chosen by the page
    defs = setup_rows()
    for k, *rows in defs:
        s = c.ch(c.recv(f"ac-setl{k}"), "expr acsetpg", "sel " + " ".join(str(j) for j in range(NSET)))
        for j, (ln, parts) in enumerate(rows):
            c.c(c.to((s, j), "t b"), 0, c.obj(f"s ac-setl{k}{'abcdefghi'[j]}"), 0)
            if parts:
                Line(f"ac-setl{k}{'abcdefghi'[j]}", ln, parts, f"ac-sett{k}")(c)
            else:
                c.c(c.m(c.recv(f"ac-setl{k}{'abcdefghi'[j]}"), ln), 0, c.obj(f"s ac-sett{k}"), 0)
    for k in range(5):
        gated_text(c, f"ac-sett{k}", "acsetup", 0, 2 + k * 12)
    # aux tap in SETUP: the other page
    return c


def midi_out():
    c = Canvas("midi-out", w=2600)
    c.comment("MIDI out: raw bytes and notes go through ac-midibyte / ac-noteout (so tests can watch them). "
              "Clock: 24 ticks a beat, Start when a piece starts, Stop at its end. Notes: the chord as voiced (base "
              "ch), tonic (+1), bells (+2), motion (+3), bass (+4), arp chord in close position (+5). Parts: all / "
              "harmony (no bells, motion) / arp chord only.")
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
    ch = lambda k: f"((acoutch - 1 + {k}) % 16 + 1)"      # base channel + k, wrapping at 16
    vel = "int(40 + 70*acenergy)"                         # chords and bass follow the piece's energy
    harm = notes + " && acmparts <= 1"
    # the sub's note: the pedal under the tonic or the chord root as a bass line (as the sub plays it)
    bass = ("int(0.5 + if(acsubm==0 || (acsubm==2 && int(acsec) % 2 == 0), actonic - 12, "
            "acnew[0] - 12*ceil((acnew[0] - 42)/12)))")
    # the arp chord: the chord's pitch classes stacked close above its root, from the Arp octave (no doubles)
    pc = lambda e: f"((int({e} + 0.5) % 12 + 12) % 12)"
    arp_i = (f"if({' || '.join(f'(aci > {j} && {pc(f'acnew[{j}]')} == {pc('acnew[int(aci)]')})' for j in range(3))}, 0, "
             f"acarpoct + {pc('acnew[0]')} + ({pc('acnew[int(aci)]')} - {pc('acnew[0]')} + 12) % 12)")
    proc(c, "ac-outchord", [If(notes + " && acrun", [
        # the chord as Amble voices it (base channel)
        # (all the old notes off first, then the new ones on, so a shared pitch is not cut off)
        If("acmparts <= 1", [
            Loop("4", "aci", [If("acout[int(aci)] > 0", [SendL("ac-noteout", ["acout[int(aci)]", "0", ch(0)])])]),
            Loop("4", "aci", [T("acout", "aci", "int(acnew[int(aci)] + 0.5)"),
                              SendL("ac-noteout", ["acout[int(aci)]", vel, ch(0)])]),
        ]),
        # the arp chord (base + 5): close position for arpeggiators and chord-following synths
        Loop("4", "aci", [If("acarp[int(aci)] > 0", [SendL("ac-noteout", ["acarp[int(aci)]", "0", ch(5)])])]),
        Loop("4", "aci", [T("acarp", "aci", arp_i),
                          If("acarp[int(aci)] > 0", [SendL("ac-noteout", ["acarp[int(aci)]", vel, ch(5)])])]),
        # the tonic (base + 1) and the bass (base + 4), held while they stay
        If("acmparts <= 1 && acoutroot != int(actonic)", [
            If("acoutroot > 0", [SendL("ac-noteout", ["acoutroot", "0", ch(1)])]),
            V("acoutroot", "int(actonic)"), SendL("ac-noteout", ["acoutroot", "70", ch(1)])]),
        If(f"acmparts <= 1 && acoutbass != {bass}", [
            If("acoutbass > 0", [SendL("ac-noteout", ["acoutbass", "0", ch(4)])]),
            V("acoutbass", bass), SendL("ac-noteout", ["acoutbass", vel, ch(4)])]),
    ])])
    proc(c, "ac-notesoff", [
        Loop("4", "aci", [If("acout[int(aci)] > 0", [SendL("ac-noteout", ["acout[int(aci)]", "0", ch(0)]),
                                                     T("acout", "aci", "0")])]),
        Loop("4", "aci", [If("acarp[int(aci)] > 0", [SendL("ac-noteout", ["acarp[int(aci)]", "0", ch(5)]),
                                                     T("acarp", "aci", "0")])]),
        If("acoutroot > 0", [SendL("ac-noteout", ["acoutroot", "0", ch(1)]), V("acoutroot", "-1")]),
        If("acoutbass > 0", [SendL("ac-noteout", ["acoutbass", "0", ch(4)]), V("acoutbass", "-1")]),
    ])
    # bells and motion: notes with a length
    for rc, chn, dur, sel in (("ac-bell", 2, 500, "$1 $2"), ("ac-mnote", 3, 150, "$1 $2")):
        sp = c.obj("spigot")
        c.c(c.to(c.recv("ac-frame"), "expr " + notes + " && acmparts == 0"), 0, sp, 1)
        c.c(c.recv(rc), 0, sp, 0)
        u = c.to(sp, "unpack f f")
        mk = c.obj(f"makenote 64 {dur}")
        c.c(c.to((u, 1), "expr int($f1*110)"), 0, mk, 1)
        c.c(c.to(u, "expr int($f1 + 0.5)"), 0, mk, 0)
        pk = c.obj("pack f f f")
        c.c(c.to(c.recv("ac-frame"), f"expr (acoutch - 1 + {chn}) % 16 + 1"), 0, pk, 2)
        c.c(mk, 1, pk, 1)
        c.c(mk, 0, pk, 0)
        c.c(pk, 0, c.obj("s ac-noteout"), 0)
        c.col(200)
    return c


def cpu_guard():
    c = Canvas("cpu-guard", w=1800)
    c.comment("CPU guard: Pd's load = CPU time / logical time, each second. Above 78 % the piece gets lighter "
              "(1: cloud and atmosphere off, 2: textures and pad character off, 3: auto-vocoder off); below 50 % "
              "for 20 s it steps back. SETUP page 4 can turn the guard off. In a batch (offline) run the load reads near 0. acloadtest overrides "
              "it for tests.")
    met = c.obj("metro 1000")
    c.c(c.to(c.recv("ac-init"), "delay 3000"), 0, met, 0)
    # right to left: elapsed logical time, elapsed CPU time (-> the load), then both restart
    tb = c.to(met, "t b b b b")
    ct, tm = c.obj("cputime"), c.obj("timer")
    pk = c.obj("pack f f")
    c.c(tb, 3, tm, 1)
    c.c(tm, 0, pk, 1)
    c.c(tb, 2, ct, 1)
    c.c(ct, 0, pk, 0)
    c.c(tb, 1, ct, 0)
    c.c(tb, 0, tm, 0)
    up = c.ch(pk, "expr $f1/max(1, $f2)", "t b f")
    c.c(up, 1, c.obj("v acldraw"), 0)
    run_steps(c, (up, 0), [V("acload", "max(acloadtest, 0.6*acload + 0.4*acldraw)"), Call("ac-cpucheck")])
    c.col()
    proc(c, "ac-cpucheck", [
        If("acguard && acload > 0.78 && acshed < 3 && acnow - acshedt > 4000", [
            X("acshed + 1; acnow", "v acshed", "v acshedt"), Call("ac-layers"), Call("ac-inputupd"),
            Toast("CPU high - lighter"),
        ]),
        If("acload < 0.5 && acshed > 0 && acnow - acshedt > 20000", [
            X("acshed - 1; acnow", "v acshed", "v acshedt"), Call("ac-layers"), Call("ac-inputupd"),
        ]),
        If("acsetup && acsetpg == 3", [Call("ac-oledsetup")]),
    ])
    return c


def clock_in():
    c = Canvas("clock-in", w=1800)
    c.comment("Follow an incoming MIDI clock (SETUP Sync = follow clock): its ticks drive Amble's rhythm, Start "
              "restarts the bar (and starts a stopped piece), Stop stops the piece; the tempo is measured")
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
    run_steps(c, (sel, 1), [If("acsync", [V("actick", "-1"), Call("ac-start"), Toast("clock start")])])
    run_steps(c, (sel, 3), [If("acsync", [Call("ac-stop"), Toast("clock stop")])])
    return c
