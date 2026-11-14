"""SETUP (hold aux 1 s), settings saved in the patch folder, MIDI clock and notes out, MIDI clock in.

SETUP page 1: MIDI out (off / tempo only / tempo+notes / notes only), Sync (internal / follow), Keys (auto / play /
functions), Bloom (clean / vintage). Page 2: Follow (how much the chords follow you), MPE bend range,
MIDI out base channel, breath curve. Page 3: output, width, pan motion, tempo range. Page 4: which
parts go out as MIDI notes, the arp chord octave. Page 5 (SOUNDS): pad type, drone, texture, character
(auto or your choice, applied at once). Page 6 (MUSIC): key, scale, chord voicing (auto or fixed), the bar pulse.
Page 7 (MIDI IN): where notes go, what breath does, what pressure does, the breath level. Page 8 (CC MAP):
what each CC does, the last CC in, the vibrato rate. Page 9 (VOICES): the bells' and the motion's engines, the pads' glide. Aux tap = the other page, hold aux 1 s = leave (and save)."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line, Arm, Toast
from gen_oled import Fill, OSC, FLIP, gated_text
from data import PAGES, TEMPOS, FILE_KNOBS, SEND_KNOBS, SUBMODES, ARCHETYPES, ATMOS_NAMES, ROLES, STRIKES, FLAVOURS, DRONES, TEXTURES, CHARACTERS, SCALES, FAMILIES, NOTE_NAMES

GLOBALS = dict(acmout=1, acsync=0, acvintage=0, acoutch=1, accurve=1.2, acsk=0, acsv=0, acextbpm=60,
               acrtb=0, acoutroot=-1, acclkon=0, acsaved=0, actrange=0,
               acmparts=0, acarpoct=48, acoutbass=-1, acload=0, acloadtest=0, acshedt=0, acldraw=0, acguard=1,
               ackeyc=0, acsclc=0, acchdc=0, acpulc=2, acroute=0, acbrto=0, acpressto=1, acccsel=0, aclastcc=0, aclastv=0, acvibr=5.5,
               acmap0=2, acmap1=1, acmap2=1, acmap3=1, acmap4=6, acmap5=0, acmap6=3, acsbell=0, acsmot=0, acglide=5, acmodesel=0, acssub=0, acsform=0, acstempo=0, acsmeter=0, acsatm=0, acnsx=0, acchx=0, acslot=0, acslotfull=0, acsvp49=1, acsvp50=1, acsetpgl=-1)
ARRAYS = dict(acout=4, acarp=4)
NP = len(PAGES)
KNOBS = [n for p in PAGES for _, n, _ in p]
SETTINGS = KNOBS[:FILE_KNOBS] + ["acmout", "acsync", "acforce", "acvintage", "acfollow", "acnbr",
                                                  "acoutch", "accurve", "acmono", "acwidth", "acpanmot",
                                                  "actrange", "acmparts", "acarpoct", "acguard"] + KNOBS[FILE_KNOBS:SEND_KNOBS] + \
           ["acspad", "acsdrone", "acstex", "acschar"] + \
           ["ackeyc", "acsclc", "acchdc", "acpulc", "acroute", "acbrto", "acpressto", "acvibr"] + \
           [f"acmap{j}" for j in range(7)] + ["acsbell", "acsmot", "acglide"] + KNOBS[SEND_KNOBS:] + ["acmodesel", "acssub", "acsform", "acstempo", "acsmeter", "acsatm"]
IN_IDX = [n for p in PAGES for _, n, _ in p].index("acinput")     # the In knob's slot in acparams
MOUT = ["off", "tempo only", "tempo+notes", "notes only"]
PARTS = ["all", "harmony", "arp only"]
OUTPUTS = ["stereo wide", "mono", "split"]   # split: pads + drone left, everything else right (mono stems)
NSET = 13                                  # SETUP pages
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
           "reverb", "swell", "motion", "resolve", "root", "next section", "chord now", "glide"]
TARGET_KNOB = {7: "acdens", 8: "accolor", 9: "acrvmix", 11: "acmotion"}   # piece targets: the knob they move
CCSEL = "if(acccsel == 0, 1, " + ", ".join(f"if(acccsel == {j}, {n}" for j, n in enumerate(CCS) if j) + ", 0" + ")" * 7
MAPSEL = "if(acccsel == 0, acmap0, " + ", ".join(f"if(acccsel == {j}, acmap{j}" for j in range(1, 7)) + ", 0" + ")" * 7
BENDS = [12, 24, 48, 96]
# SETUP page 9, VOICES: the engine of the bells and of the motion (auto = the piece's)
SBELLS = ["auto"] + STRIKES
SMOTS = ["auto"] + STRIKES
# how the pad voices move to a new chord: off = they jump; slow = the full glide (25-75 % of the time between
# changes, at least 1.5 s); the steps between scale that glide
GLIDES = ["off", "fast", "short", "medium", "long", "slow"]
# the sub (page 9 row 4): auto = the piece's mode
SSUBS = ["auto"] + SUBMODES
# SETUP page 10, FORM: the form's shape (custom = your sections, page 11), a fixed tempo, the meter, the atmosphere
SFORMS = ["auto"] + ARCHETYPES + ["custom"]
STEMPOS = ["auto"] + [f"{t} bpm" for t in (40, 48, 56, 64, 72, 80, 90, 100, 110, 120, 140)]
SMETERS = ["auto"] + [f"{m} beats" for m in (3, 4, 5, 6, 7)]
SATMS = ["auto"] + ATMOS_NAMES
# SETUP pages 11-12, SECTIONS and SECTION MIX: the custom form, section by section (a role of "end" ends the
# piece there); each section's length, pad type, and each layer's play state and level
SROLES = ROLES + ["end"]
SLENS = ["short", "normal", "long"]
SEC_LAYER_NAMES = ["drone", "sub", "pads", "bells", "motion", "textures", "atmos", "cloud"]
SPLAY = ["auto", "off", "on"]
# SETUP page 13, SAVES: 16 slots in saves.txt, each the seed and everything that shapes the piece
NSLOTS = 16
SAVE_SCALARS = ["acseed", "acmodesel"] + [n for p in PAGES for _, n, _ in p if n != "acinput"] + \
    ["acspad", "acsdrone", "acstex", "acschar", "ackeyc", "acsclc", "acchdc", "acpulc", "acsbell", "acsmot", "acglide",
     "acssub", "acsform", "acstempo", "acsmeter", "acsatm", "acscount"] + \
    ["acm" + n for n in ("drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud")]
SAVE_ARRAYS = [("acsroles", 12), ("acslens", 12), ("acssp", 12), ("acsst", 96), ("acslv", 96)]
SAVE_LEN = len(SAVE_SCALARS) + sum(n for _, n in SAVE_ARRAYS)
ARRAYS["acsavebuf"] = SAVE_LEN
GLIDE_X = "if(acglide == 0, 0, if(acglide == 1, 0.05, if(acglide == 2, 0.15, if(acglide == 3, 0.3, if(acglide == 4, 0.6, 1)))))"


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
                           SendL("ac-lvvibr", ["acvibr"]), V("acmode", "acmodesel == 0")])
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
            ("list 1 Bells $1", [("s", "acsbell", SBELLS)]),
            ("list 1 Form $1", [("s", "acsform", SFORMS)]),
            ("list 1 Section $1 of $2", [("f", "acsecsel + 1"), ("f", "if(acscount > 0, acscount, acnsec)")]),
            ("list 1 Section $1", [("f", "acsecsel + 1")]),
            ("list 1 Slot $1 $2", [("f", "acslot + 1"), ("s", "acslotfull", ["empty", "saved"])])),
        (2, ("list 2 Sync $1", [("s", "acsync", ["internal", "follow clock"])]),
            ("list 2 MPE bend $1", [("f", "acnbr")]), ("list 2 Width $1", [("f", "int(acwidth*100)")]),
            ("list 2 Arp octave C$1", [("f", "acarpoct/12 - 1")]),
            ("list 2 Drone $1", [("s", "acsdrone", SDRONES)]),
            ("list 2 Scale $1", [("s", "acsclc", SSCALES)]),
            ("list 2 Breath to $1", [("s", "acbrto", BRTOS)]),
            ("list 2 to $1", [("s", MAPSEL, TARGETS)]),
            ("list 2 Motion $1", [("s", "acsmot", SMOTS)]),
            ("list 2 Tempo $1", [("s", "acstempo", STEMPOS)]),
            ("list 2 Role $1", [("s", "if(acscount > 0, acsroles[int(acsecsel)], acroles[int(acsecsel)])", SROLES)]),
            ("list 2 Layer $1", [("s", "acslay", SEC_LAYER_NAMES)]),
            ("list 2 Save - turn up", None)),
        (3, ("list 3 Mode $1", [("s", "acmodesel", ["COMPOSE", "DRIFT"])]),
            ("list 3 MIDI out ch $1", [("f", "acoutch")]), ("list 3 Pan motion $1", [("f", "int(acpanmot*100)")]),
            ("list 3 CPU $1% lite $2", [("f", "int(acload*100)"), ("f", "acshed")]),
            ("list 3 Texture $1", [("s", "acstex", STEXS)]),
            ("list 3 Chords $1", [("s", "acchdc", SCHORDS)]),
            ("list 3 Pressure to $1", [("s", "acpressto", TARGETS)]),
            ("list 3 Last CC $1 = $2", [("f", "aclastcc"), ("f", "aclastv")]),
            ("list 3 Glide $1", [("s", "acglide", GLIDES)]),
            ("list 3 Meter $1", [("s", "acsmeter", SMETERS)]),
            ("list 3 Length $1", [("s", "acslens[int(acsecsel)]", SLENS)]),
            ("list 3 Play $1", [("s", "acsst[int(acsecsel*8 + acslay)]", SPLAY)]),
            ("list 3 Load - turn up", None)),
        (4, ("list 4 Bloom $1", [("s", "acvintage", ["clean", "vintage"])]),
            ("list 4 Breath curve $1", [("f", "int(accurve*100)")]), ("list 4 Tempo $1 $2-$3", [("s", "actrange", [n for n, _, _ in TEMPOS]),
                                          ("f", "actlo[int(actrange)]"), ("f", "acthi[int(actrange)]")]),
            ("list 4 CPU guard $1", [("s", "acguard", ["off", "on"])]),
            ("list 4 Character $1", [("s", "acschar", SCHARS)]),
            ("list 4 Pulse $1", [("s", "acpulc", PULSES)]),
            ("list 4 Breath in $1%", [("f", "int(aclbv*100)")]),
            ("list 4 Vib rate $1 Hz", [("f", "acvibr")]),
            ("list 4 Sub $1", [("s", "acssub", SSUBS)]),
            ("list 4 Atmos $1", [("s", "acsatm", SATMS)]),
            ("list 4 Pads $1", [("s", "acssp[int(acsecsel)]", SPADS)]),
            ("list 4 Level $1%", [("f", "int(acslv[int(acsecsel*8 + acslay)]*100)")]),
            ("list 4 Seed $1", [("f", "acseed")])),
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
        If("acsetpg != acsetpgl", [X("1; 1; acsetpg", "v acsvp49", "v acsvp50", "v acsetpgl")]),
        If(f"{item} == 0", [V("acmout", "int(acsv*3.99)"), If("acmout == 0 || acmout == 3", [Call("ac-clockstop")],
                                                               [Call("ac-clockstart")]),
                            If("acmout < 2", [Call("ac-notesoff")], [Call("ac-outchord")])]),
        If(f"{item} == 1", [V("acsync", "acsv > 0.5"), SendL("ac-bpm", ["acbpm"])]),
        If(f"{item} == 2", [If("(acsv > 0.5) != acmodesel", [Call("ac-modetoggle")])]),
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
        # the glide applies from the next chord change
        If(f"{item} == 34", [V("acglide", f"int(acsv*{len(GLIDES) - 0.01})")]),
        If(f"{item} == 35", [V("acssub", f"int(acsv*{len(SSUBS) - 0.01})")]),
        # FORM: the shape applies to the next piece (or now, while the piece waits ready); the tempo and meter at
        # once; the atmosphere from the next section
        If(f"{item} == 36", [V("acsnew", f"int(acsv*{len(SFORMS) - 0.01})"), If("acsnew != acsform", [
            V("acsform", "acsnew"), Call("ac-formset")])]),
        If(f"{item} == 37", [V("acsnew", f"int(acsv*{len(STEMPOS) - 0.01})"), If("acsnew != acstempo", [
            V("acstempo", "acsnew"), Call("ac-settempo")])]),
        If(f"{item} == 38", [V("acsnew", f"int(acsv*{len(SMETERS) - 0.01})"), If("acsnew != acsmeter", [
            V("acsmeter", "acsnew"), If("acsmeter > 0", [V("acmeter", "acsmeter + 2")])])]),
        If(f"{item} == 39", [V("acsatm", f"int(acsv*{len(SATMS) - 0.01})"), If("acsatm > 0", [
            V("acatmcur", "acsatm - 1"), V("acfade", "3000"), Call("ac-layers")])]),
        # SECTIONS / SECTION MIX: editing a section turns the form to custom (from the piece's plan, the first
        # time); it applies to the piece at once (sections to come; the current one's layers now)
        If(f"{item} == 40 || {item} == 44", [V("acsecsel", "int(acsv*11.99)")]),
        If(f"{item} == 45", [V("acslay", "int(acsv*7.99)")]),
    ] + [If(f"{item} == {it}", [Call("ac-customcopy"), V("acsform", "6"), act, Call("ac-customapply"),
                                Call("ac-secovr"), V("acfade", "1000"), Call("ac-layers")] + extra)
         for it, act, extra in (
             (41, T("acsroles", "acsecsel", f"int(acsv*{len(SROLES) - 0.01})"), []),
             (42, T("acslens", "acsecsel", f"int(acsv*{len(SLENS) - 0.01})"), []),
             (43, T("acssp", "acsecsel", f"int(acsv*{len(SPADS) - 0.01})"), [If("acsecsel == acsec", [Call("ac-padpick")])]),
             (46, T("acsst", "acsecsel*8 + acslay", f"int(acsv*{len(SPLAY) - 0.01})"), []),
             (47, T("acslv", "acsecsel*8 + acslay", "2*acsv"), []))
    ] + [
        # SAVES: knob 1 the slot, knob 2 up past 90 % saves, knob 3 loads (each re-arms below 90 %; a page change
        # re-arms only after the knob has gone down, so arriving with a knob up does nothing)
        If(f"{item} == 48", [V("acslot", f"int(acsv*{NSLOTS - 0.01})"), Call("ac-slotcheck")]),
        If(f"{item} == 49", [If("acsv > 0.9 && acsvp49 <= 0.9", [Call("ac-savepiece")]), V("acsvp49", "acsv")]),
        If(f"{item} == 50", [If("acsv > 0.9 && acsvp50 <= 0.9", [Call("ac-loadpiece")]), V("acsvp50", "acsv")]),
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
            c.c(c.to((s, j), "t b"), 0, c.obj(f"s ac-setl{k}{'abcdefghijklmnop'[j]}"), 0)
            if parts:
                Line(f"ac-setl{k}{'abcdefghijklmnop'[j]}", ln, parts, f"ac-sett{k}")(c)
            else:
                c.c(c.m(c.recv(f"ac-setl{k}{'abcdefghijklmnop'[j]}"), ln), 0, c.obj(f"s ac-sett{k}"), 0)
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


def saves():
    """SAVES (SETUP page 13): saves.txt holds one line per saved slot: the slot number, then SAVE_SCALARS and
    SAVE_ARRAYS. Loading sets them all and prepares the piece from its seed (ready while stopped)."""
    c = Canvas("saves", w=2600)
    c.comment("Saves: slot lines in saves.txt (slot, seed, mode, knobs, sounds, form, sections, layer states)")
    td = c.obj("text define acsaves")
    c.c(c.m(c.recv("ac-loadsettings"), "read saves.txt"), 0, td, 0)
    c.c(c.ch(c.recv("ac-loadsettings"), "delay 5"), 0, c.obj("s ac-slotcheck"), 0)
    # is the slot saved?
    sc = c.ch(c.recv("ac-slotcheck"), "expr acslot + 1", "text search acsaves 0", "expr $f1 >= 0", "t b f")
    c.c(sc, 1, c.obj("v acslotfull"), 0)
    c.c(sc, 0, c.obj("s ac-oledsetupq"), 0)
    c.col()
    # save: the values into acsavebuf, then the line (slot first) replaces the slot's line, or is added
    off = len(SAVE_SCALARS)
    steps = [T("acsavebuf", i, n) for i, n in enumerate(SAVE_SCALARS)]
    for name, n in SAVE_ARRAYS:
        steps += [Loop(str(n), "aci", [T("acsavebuf", f"{off} + aci", f"{name}[int(aci)]")])]
        off += n
    proc(c, "ac-savepiece", steps + [Send("ac-savewrite"), Call("ac-slotcheck"), Send("ac-savesay")])
    w = c.to(c.recv("ac-savewrite"), "t b b b")
    ts = c.obj("text set acsaves")
    c.c(c.ch((w, 2), "expr acslot + 1", "text search acsaves 0", "expr if($f1 < 0, 1e+06, $f1)"), 0, ts, 1)
    lp = c.obj("list prepend")
    c.c(c.to((w, 1), "expr acslot + 1"), 0, lp, 1)
    c.c(c.ch((w, 1), "t b", f"array get acsavebuf"), 0, lp, 0)
    c.c(c.to(lp, "list trim"), 0, ts, 0)
    c.c(c.m((w, 0), "write saves.txt"), 0, td, 0)
    c.col()
    # load
    ld = c.ch(c.recv("ac-loadpiece"), "expr acslot + 1", "text search acsaves 0", "moses 0")
    c.c(c.to((ld, 0), "t b"), 0, c.obj("s ac-loadempty"), 0)
    gl = c.ch((ld, 1), "text get acsaves", "list split 1")
    c.c((gl, 1), 0, c.obj("array set acsavebuf"), 0)
    c.c(c.to((gl, 1), "t b"), 0, c.obj("s ac-loadapply"), 0)
    proc(c, "ac-loadempty", [Toast("slot is empty")])
    knobs = [n for p in PAGES for _, n, _ in p]
    off = len(SAVE_SCALARS)
    steps = [V(n, f"acsavebuf[{i}]") for i, n in enumerate(SAVE_SCALARS)]
    for name, n in SAVE_ARRAYS:
        steps += [Loop(str(n), "aci", [T(name, "aci", f"acsavebuf[int({off} + aci)]")])]
        off += n
    steps += [T("acparams", knobs.index(n), n) for n in knobs if n != "acinput"]
    steps += [Loop(str(len(knobs)), "aci", [SendL("ac-pset", ["aci", "acparams[int(aci)]"])]),
              V("acmode", "acmodesel == 0"), V("acknown0", "0"), V("acknown1", "0"), V("acknown2", "0"),
              V("acknown3", "0"),
              Call("ac-sendupd"), Call("ac-revupd"), Call("ac-verbsel"), Call("ac-stereo"),
              # the piece from its seed: ready while stopped, playing otherwise
              If("acstopped", [V("acready", "1")]), SendL("ac-setseed", ["acseed"]),
              Send("ac-loadsay"), Send("ac-dirty")]
    proc(c, "ac-loadapply", steps)
    Line("ac-savesay", "list saved to slot $1", [("f", "acslot + 1")], "ac-toast")(c)
    Line("ac-loadsay", "list loaded slot $1", [("f", "acslot + 1")], "ac-toast")(c)
    # the SETUP screen, if it shows
    run_steps(c, (c.recv("ac-oledsetupq"), 0), [If("acsetup", [Call("ac-oledsetup")])])
    return c
