"""SETUP (hold aux 1 s, or aux + a low key for that page): 21 pages of 4 rows, each row set by its knob.

Where things are:
  the choices of each row        constants below (SPADS, SFORMS, SMORPH ...), next to a comment naming the page
  the pages and their rows       setup_pages() - page by page, the text and what fills it
  what turning a knob does       setup() - the handler, one If(at("PAGE", row), ...) per row
  settings.txt                   SETTINGS (the order on the line) and settings() (load and save)
  a saved piece's fields         SAVE_SCALARS, SAVE_ARRAYS, SAVE_EXTRA (saves and loads: gen_saves)
  CC MAP targets                 TARGETS (what a CC can do; gen_live.cc_map acts on them)
Also the CPU guard (cpu_guard()), whose setting and readout are on page 4."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line, Toast, Later
from gen_oled import Fill, FLIP, gated_text
from data import FACTORY, PAGES, TEMPOS, FILE_KNOBS, SEND_KNOBS, MIX_KNOBS, SUBMODES, ARCHETYPES, ATMOS_NAMES, ROLES, STRIKES, FLAVOURS, DRONES, TEXTURES, CHARACTERS, SCALES, FAMILIES, NOTE_NAMES

GLOBALS = dict(acmout=1, acsync=0, acvintage=0, acoutch=1, accurve=1.2, acsk=0, acsv=0, acextbpm=60,
               acrtb=0, acoutroot=-1, acclkon=0, actrange=0,
               acmparts=0, acarpoct=48, acoutbass=-1, acload=0, acloadtest=0, acshedt=0, acldraw=0, acguard=1,
               ackeyc=0, acsclc=0, acchdc=0, acpulc=2, acroute=0, acbrto=0, acpressto=1, acccsel=0, aclastcc=0, aclastv=0, acvibr=5.5,
               acmap0=2, acmap1=1, acmap2=1, acmap3=1, acmap4=6, acmap5=0, acmap6=3, acsbell=0, acsmot=0, acglide=5, acmodesel=0, acssub=0, acsform=0, acstempo=0, acsmeter=0, acsatm=0, acnsx=0, acchx=0, acslot=0, acslotfull=0, acsvp49=1, acsvp50=1, acsetpgl=-1, acmixcc=0, acpgm=0, aclfd=1, acsfd=2,
               acmorph=0, acrecall=0, acancg=2, accmp=0, acpump=0, acpumpd=0.5, acduck=0, acduckr=2, acmcsel=0, acmcn=0, acmcin=0,
               acmc0mode=0, acmc0ta=0, acmc0da=0.75, acmc0tb=0, acmc0db=0.75, acmc0v=0, acmc0p=0, acmc1mode=0, acmc1ta=0, acmc1da=0.75, acmc1tb=0, acmc1db=0.75, acmc1v=0, acmc1p=0, acmc2mode=0, acmc2ta=0, acmc2da=0.75, acmc2tb=0, acmc2db=0.75, acmc2v=0, acmc2p=0, acmc3mode=0, acmc3ta=0, acmc3da=0.75, acmc3tb=0, acmc3db=0.75, acmc3v=0, acmc3p=0,
               acsname=0, acstonic=-1, acsscale=0, acspark=0, acsparko=1, acslnm=0, acslkey=-1, acslsc=0, acjour=0, acjpad=0, acjdrone=0, acjstrike=0, acrvpre=0, acrvera=3, acccout=0, acccch=1, acccbase=0, acccrate=1)
ARRAYS = dict(acout=4, acarp=4)
NP = len(PAGES)
KNOBS = [n for p in PAGES for _, n, _ in p]
SETTINGS = KNOBS[:FILE_KNOBS] + ["acmout", "acsync", "acforce", "acvintage", "acfollow", "acnbr",
                                                  "acoutch", "accurve", "acmono", "acwidth", "acpanmot",
                                                  "actrange", "acmparts", "acarpoct", "acguard"] + KNOBS[FILE_KNOBS:SEND_KNOBS] + \
           ["acspad", "acsdrone", "acstex", "acschar"] + \
           ["ackeyc", "acsclc", "acchdc", "acpulc", "acroute", "acbrto", "acpressto", "acvibr"] + \
           [f"acmap{j}" for j in range(7)] + ["acsbell", "acsmot", "acglide"] + KNOBS[SEND_KNOBS:MIX_KNOBS] + ["acmodesel", "acssub", "acsform", "acstempo", "acsmeter", "acsatm"] + \
           ["acmixcc", "acpgm", "aclfd", "acsfd"] + KNOBS[MIX_KNOBS:] + \
           ["acmorph", "acrecall", "acancg", "acpump", "acpumpd", "acduck", "acduckr"] + \
           [f"acmc{m}{f}" for m in range(4) for f in ("mode", "ta", "da", "tb", "db")] + \
           ["acjour", "acjpad", "acjdrone", "acjstrike", "acrvpre", "acrvera", "acccout", "acccch", "acccbase", "acccrate"] + \
           ["acspark", "acsparko"]
IN_IDX = [n for p in PAGES for _, n, _ in p].index("acinput")     # the In knob's slot in acparams
MOUT = ["off", "tempo only", "tempo+notes", "notes only"]
PARTS = ["all", "harmony", "arp only"]
OUTPUTS = ["stereo wide", "mono", "split"]   # split: pads + drone left, everything else right (mono stems)
NSET = 21                                  # SETUP pages
SETUP_NAMES = ["GENERAL", "PLAYING", "OUTPUT", "NOTES OUT", "SOUNDS", "MUSIC", "MIDI IN", "CC MAP", "VOICES", "FORM",
               "SECTIONS", "SECTION MIX", "SAVES", "LIVE", "RECALL", "GROOVE", "MACRO A", "MACRO B", "JOURNEY",
               "COLOUR", "CC OUT"]
# a saved slot's name: a word, or auto (its key and scale, kept when it was saved)
NAME_WORDS = ["auto", "Dawn", "Ember", "Tide", "Glass", "Frost", "Drift", "Hollow", "Mist", "Lantern", "Harbor", "Orbit",
              "Moss", "Signal", "Velvet", "Ash", "Bloom", "Night", "River", "Static", "Halo", "Cinder", "Prism", "Dune",
              "Echo", "Still", "Aurora", "Rain", "Slate", "Thaw", "Lumen", "Ochre"]
# GLINT (SETUP COLOUR): sparse FM sparkles high over the chord tones while the drone or pads sound
SSPARKO = ["+1 oct", "+2 oct", "+3 oct"]
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
           "reverb", "swell", "motion", "resolve", "root", "next section", "chord now", "glide",
           "anchor", "compare", "macro 1", "macro 2", "macro 3", "macro 4", "journey step", "sink", "blur",
           "swell all", "harm", "sparkle"]
TARGET_KNOB = {7: "acdens", 8: "accolor", 9: "acrvmix", 11: "acmotion",       # piece targets: the knob they move
               24: "acsink", 25: "acblur", 26: "acswell", 27: "acharmx"}
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
SPLAY = ["auto", "off", "on", "in 1/4", "in 1/2", "in 3/4", "out 1/4", "out 1/2", "out 3/4"]
# SETUP page 14, LIVE: a bank of 16 CCs (8 layer levels, then 8 layer in/out buttons), program change loads a
# save slot, the fade of a layer key (or button), the swell of a layer coming in or going out within a section
SMIXCC = ["off", "CC 20-35", "CC 102-117"]
MIXCC_BASE = "if(acmixcc == 1, 20, 102)"
SPGM = ["off", "loads a slot"]
SLFADE = [("0.5 s", 500), ("2.5 s", 2500), ("5 s", 5000), ("10 s", 10000), ("20 s", 20000)]
SSFADE = [("2 s", 2000), ("5 s", 5000), ("10 s", 10000), ("20 s", 20000), ("40 s", 40000)]


def _pick(var, table):
    e = str(table[-1][1])
    for i in range(len(table) - 2, -1, -1):
        e = f"if({var} == {i}, {table[i][1]}, {e})"
    return e


LFADE = _pick("aclfd", SLFADE)


def msel(f):
    """the selected macro's field (SETUP MACRO pages): acmc<m><f>"""
    return "if(acmcsel == 0, acmc0" + f + ", if(acmcsel == 1, acmc1" + f + ", if(acmcsel == 2, acmc2" + f + ", acmc3" + f + ")))"
SFADE = _pick("acsfd", SSFADE)
# SETUP page 13, SAVES: 16 slots in saves.txt, each the seed and everything that shapes the piece
NSLOTS = 16
SAVE_SCALARS = ["acseed", "acmodesel"] + [n for p in PAGES[:7] for _, n, _ in p if n != "acinput"] + \
    ["acspad", "acsdrone", "acstex", "acschar", "ackeyc", "acsclc", "acchdc", "acpulc", "acsbell", "acsmot", "acglide",
     "acssub", "acsform", "acstempo", "acsmeter", "acsatm", "acscount"] + \
    ["acm" + n for n in ("drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud")]
SAVE_ARRAYS = [("acsroles", 12), ("acslens", 12), ("acssp", 12), ("acsst", 96), ("acslv", 96)]
# (added after the arrays, so a line saved before them still loads: they take these defaults)
SAVE_EXTRA = [("acsink", 0), ("acblur", 0), ("acswell", 0), ("acharmx", 0), ("acpump", 0), ("acpumpd", 0.5),
              ("acduck", 0), ("acjour", 0), ("acjpad", 0), ("acjdrone", 0), ("acjstrike", 0), ("acrvpre", 0),
              ("acrvera", 3), ("acsname", 0), ("acstonic", -1), ("acsscale", 0), ("acspark", 0), ("acsparko", 1)]
SAVE_EXTRA_AT = len(SAVE_SCALARS) + sum(n for _, n in SAVE_ARRAYS)
SAVE_LEN = SAVE_EXTRA_AT + len(SAVE_EXTRA)
# what a recall of "sound only" brings: the knobs, the sounds, the layers - not the seed, the music or the form
SOUND_ONLY = set(KNOBS) | {"acspad", "acsdrone", "acstex", "acschar", "acsbell", "acsmot", "acglide", "acssub",
                          "acsatm"} | {"acm" + n for n in ("drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud")} \
             | {n for n, _ in SAVE_EXTRA}
# the SAVES page's slot: empty, a factory piece, or a saved one by its name (a word, or its key and scale)
_NSC = len(SCALES)
SLOT_LABELS = (["empty", "saved"] + [n for n, _, _ in FACTORY] + NAME_WORDS[1:]
               + [f"{k} {sc}" for k in NOTE_NAMES for sc, _ in SCALES])
SLOT_LABEL = (f"if(acslotfull == 0, if(acslot < {len(FACTORY)}, 2 + acslot, 0), if(acslnm > 0, {1 + len(FACTORY)} + acslnm, "
              f"if(acslkey >= 0, {1 + len(FACTORY) + len(NAME_WORDS)} + acslkey*{_NSC} + acslsc, 1)))")


# SETUP page 15, RECALL: how a load comes in (the knobs glide over Morph; the choices switch at once), what it
# brings, how ANCHOR glides back, and COMPARE (the slot as saved, while the knob is up)
SMORPH = [("cut", 0), ("1 s", 1000), ("2 s", 2000), ("4 s", 4000), ("8 s", 8000), ("15 s", 15000), ("30 s", 30000),
          ("1 min", 60000), ("2 min", 120000)]
SRECALL = ["piece", "sound only"]
SANCG = [("2 s", 2000), ("4 s", 4000), ("8 s", 8000), ("15 s", 15000), ("30 s", 30000)]
# SETUP page 16, GROOVE: PUMP ducks the bed (drone, sub, pads, atmosphere) on a grid; DUCK dips the piece while
# you play (notes held or breath), coming back over its release
SPUMP = ["off", "4 bars", "2 bars", "1 bar", "1/2 bar", "beat"]
PUMP_BEATS = "if(acpump == 1, 4*acmeter, if(acpump == 2, 2*acmeter, if(acpump == 3, acmeter, if(acpump == 4, max(1, int(acmeter/2)), 1))))"
SDUCKR = [("0.5 s", 500), ("1 s", 1000), ("2 s", 2000), ("4 s", 4000), ("8 s", 8000)]
# SETUP pages 17-18, MACRO A / B: four macros (CC targets macro 1-4), each moving two knobs with a depth of its
# own (-100 .. +100 %): offset (the knob's value moves away while the macro is up, back as it comes down) or latch
# (the macro drags the knob's value, which stays where it is left)
MT_KNOBS = [i for i, n in enumerate(KNOBS) if n not in ("acinput", "acrvtype")]
_SHORT = {"acrvmix": "Rv mix", "acrvtime": "Rv time", "acrvtone": "Rv tone"}
MTARGETS = ["off"] + [_SHORT.get(KNOBS[i], [l for p in PAGES for l, _, _ in p][i] +
                      (" snd" if 12 <= i < 20 else " lvl" if 20 <= i < 28 else "")) for i in MT_KNOBS]
SMMODE = ["offset", "latch"]
# SETUP page 19, JOURNEY: the layers travel through their engines, each step slowly crossfaded - the pad voices
# (each on its own schedule) through a set of pad types, the drone through its designs, the bells and the motion
# through the struck engines. Speed sets the time between steps; a CC (journey step) steps them by hand.
SJOUR = [("held", 0), ("very slow", 180000), ("slow", 90000), ("medium", 40000), ("fast", 15000)]
JPAD_SETS = [("off", []), ("soft", ["sine", "glass", "part", "beat", "vox", "bow"]),
             ("bright", ["saws", "pwm", "sync", "fm", "tine", "digi"]),
             ("all", ["sine", "glass", "beat", "vox", "saws", "pwm", "part", "bow", "tine", "fm", "sync", "fold"])]
SJDRONE = ["off", "on"]
SJSTRIKE = ["off", "bells", "motion", "both"]
# SETUP page 20, COLOUR: a pre-delay before every reverb, the era of its converters (70s: narrow band, few
# bits .. now: full band)
SPRE = [0, 10, 25, 50, 80, 120, 200]
SERA = ["70s", "80s", "90s", "now"]
# SETUP page 21, CC OUT: what moves inside, out as 16 CCs from a base (the layers' levels, energy, density,
# brightness, the way to the next chord and section, the reverb, the pads' motion, the swell), on change
SCCBASE = [20, 40, 70, 102]
SCCRATE = [("2 Hz", 500), ("5 Hz", 200), ("10 Hz", 100)]
CC_OUT = ["drone", "sub", "pads", "bells", "motion", "textures", "atmos", "cloud", "energy", "density",
          "brightness", "to chord", "section", "reverb", "pad drift", "swell"]
ARRAYS["acsavebuf"] = SAVE_LEN
ARRAYS["acsetbuf"] = len(SETTINGS) - 12
ARRAYS["acslotbuf"] = SAVE_LEN
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
                           SendL("ac-vintage", ["acvintage"]),
                           SendL("ac-lvvibr", ["acvibr"]), V("acmode", "acmodesel == 0"),
                           Call("ac-rvcolour"), Call("ac-sinkupd"), Call("ac-pumpupd"), Call("ac-sparkupd"), Later("ac-jourupd", 400)])
    rt = c.to(c.recv("ac-pset"), "route " + " ".join(str(i) for i in range(len(KNOBS))))
    for i, n in enumerate(KNOBS):
        c.c(rt, i, c.obj("v " + n), 0)
    c.col()
    # save (3 s after the last change)
    d = c.to(c.recv("ac-dirty"), "delay 3000")
    c.c(d, 0, c.obj("s ac-save"), 0)
    # (the values go through an array: one expr holds at most 100 of them)
    tsv = c.to(c.recv("ac-save"), "t b b")
    run_steps(c, (tsv, 1), [T("acsetbuf", i, n) for i, n in enumerate(SETTINGS[12:])])
    t2 = c.to((tsv, 0), "t b b")
    la = c.obj("list append")
    c.c(c.to((t2, 1), "array get acsetbuf"), 0, la, 1)
    c.c(c.to((t2, 0), f"array get acparams 0 {FILE_KNOBS}"), 0, la, 0)
    tl = c.to(la, "t b l")
    c.c(c.ch((tl, 1), "list prepend set", "list trim"), 0, td, 0)
    c.c(c.m((tl, 0), "write settings.txt"), 0, td, 0)
    return c


def setup_pages():
    """SETUP, page by page: (name, [row 1, row 2, row 3, row 4]), each row (text with $n, parts) - the parts as
    Line takes them, or None for a fixed text. Knob k of a page sets its row k (setup(): the handler, by at()). Also
    read by tools/manual.py, so the manual lists exactly these rows."""
    return [
        ("GENERAL", [
            ("list 1 MIDI out $1", [("s", "acmout", MOUT)]),
            ("list 2 Sync $1", [("s", "acsync", ["internal", "follow clock"])]),
            ("list 3 Mode $1", [("s", "acmodesel", ["COMPOSE", "DRIFT"])]),
            ("list 4 Bloom $1", [("s", "acvintage", ["clean", "vintage"])]),
        ]),
        ("PLAYING", [
            ("list 1 Follow you $1", [("f", "int(acfollow*100)")]),
            ("list 2 MPE bend $1", [("f", "acnbr")]),
            ("list 3 MIDI out ch $1", [("f", "acoutch")]),
            ("list 4 Breath curve $1", [("f", "int(accurve*100)")]),
        ]),
        ("OUTPUT", [
            ("list 1 Output $1", [("s", "acmono", OUTPUTS)]),
            ("list 2 Width $1", [("f", "int(acwidth*100)")]),
            ("list 3 Pan motion $1", [("f", "int(acpanmot*100)")]),
            ("list 4 Tempo $1 $2-$3", [("s", "actrange", [n for n, _, _ in TEMPOS]), ("f", "actlo[int(actrange)]"), ("f", "acthi[int(actrange)]")]),
        ]),
        ("NOTES OUT", [
            ("list 1 MIDI notes $1", [("s", "acmparts", PARTS)]),
            ("list 2 Arp octave C$1", [("f", "acarpoct/12 - 1")]),
            ("list 3 CPU $1% lite $2", [("f", "int(acload*100)"), ("f", "acshed")]),
            ("list 4 CPU guard $1", [("s", "acguard", ["off", "on"])]),
        ]),
        ("SOUNDS", [
            ("list 1 Pads $1", [("s", "acspad", SPADS)]),
            ("list 2 Drone $1", [("s", "acsdrone", SDRONES)]),
            ("list 3 Texture $1", [("s", "acstex", STEXS)]),
            ("list 4 Character $1", [("s", "acschar", SCHARS)]),
        ]),
        ("MUSIC", [
            ("list 1 Key $1", [("s", "ackeyc", SKEYS)]),
            ("list 2 Scale $1", [("s", "acsclc", SSCALES)]),
            ("list 3 Chords $1", [("s", "acchdc", SCHORDS)]),
            ("list 4 Pulse $1", [("s", "acpulc", PULSES)]),
        ]),
        ("MIDI IN", [
            ("list 1 Notes to $1", [("s", "acroute", ROUTES)]),
            ("list 2 Breath to $1", [("s", "acbrto", BRTOS)]),
            ("list 3 Pressure to $1", [("s", "acpressto", TARGETS)]),
            ("list 4 Breath in $1%", [("f", "int(aclbv*100)")]),
        ]),
        ("CC MAP", [
            ("list 1 CC $1", [("f", CCSEL)]),
            ("list 2 to $1", [("s", MAPSEL, TARGETS)]),
            ("list 3 Last CC $1 = $2", [("f", "aclastcc"), ("f", "aclastv")]),
            ("list 4 Vib rate $1 Hz", [("f", "acvibr")]),
        ]),
        ("VOICES", [
            ("list 1 Bells $1", [("s", "acsbell", SBELLS)]),
            ("list 2 Motion $1", [("s", "acsmot", SMOTS)]),
            ("list 3 Glide $1", [("s", "acglide", GLIDES)]),
            ("list 4 Sub $1", [("s", "acssub", SSUBS)]),
        ]),
        ("FORM", [
            ("list 1 Form $1", [("s", "acsform", SFORMS)]),
            ("list 2 Tempo $1", [("s", "acstempo", STEMPOS)]),
            ("list 3 Meter $1", [("s", "acsmeter", SMETERS)]),
            ("list 4 Atmos $1", [("s", "acsatm", SATMS)]),
        ]),
        ("SECTIONS", [
            ("list 1 Section $1/$2 $3", [("f", "acsecsel + 1"), ("f", "if(acscount > 0, acscount, acnsec)"), ("s", "acsecfol", ["fixed", "now"])]),
            ("list 2 Role $1", [("s", "if(acscount > 0, acsroles[int(acsecsel)], acroles[int(acsecsel)])", SROLES)]),
            ("list 3 Length $1", [("s", "acslens[int(acsecsel)]", SLENS)]),
            ("list 4 Pads $1", [("s", "acssp[int(acsecsel)]", SPADS)]),
        ]),
        ("SECTION MIX", [
            ("list 1 Section $1 $2", [("f", "acsecsel + 1"), ("s", "acsecfol", ["fixed", "now"])]),
            ("list 2 Layer $1", [("s", "acslay", SEC_LAYER_NAMES)]),
            ("list 3 Play $1", [("s", "acsst[int(acsecsel*8 + acslay)]", SPLAY)]),
            ("list 4 Level $1%", [("f", "int(acslv[int(acsecsel*8 + acslay)]*100)")]),
        ]),
        ("SAVES", [
            ("list 1 Slot $1 $2", [("f", "acslot + 1"), ("s", SLOT_LABEL, SLOT_LABELS)]),
            ("list 2 Save - turn up", None),
            ("list 3 Load - turn up", None),
            ("list 4 Name $1", [("s", "acsname", NAME_WORDS)]),
        ]),
        ("LIVE", [
            ("list 1 Mix CCs $1", [("s", "acmixcc", SMIXCC)]),
            ("list 2 Prog change $1", [("s", "acpgm", SPGM)]),
            ("list 3 Key fade $1", [("s", "aclfd", [n for n, _ in SLFADE])]),
            ("list 4 Entry fade $1", [("s", "acsfd", [n for n, _ in SSFADE])]),
        ]),
        ("RECALL", [
            ("list 1 Morph $1", [("s", "acmorph", [n for n, _ in SMORPH])]),
            ("list 2 Recall $1", [("s", "acrecall", SRECALL)]),
            ("list 3 Anchor glide $1", [("s", "acancg", [n for n, _ in SANCG])]),
            ("list 4 Compare $1", [("s", "accmp", ["yours", "saved"])]),
        ]),
        ("GROOVE", [
            ("list 1 Pump $1", [("s", "acpump", SPUMP)]),
            ("list 2 Pump depth $1%", [("f", "int(acpumpd*100)")]),
            ("list 3 Duck $1%", [("f", "int(acduck*100)")]),
            ("list 4 Duck release $1", [("s", "acduckr", [n for n, _ in SDUCKR])]),
        ]),
        ("MACRO A", [
            ("list 1 Macro $1", [("f", "acmcsel + 1")]),
            ("list 2 Mode $1", [("s", msel("mode"), SMMODE)]),
            ("list 3 A $1", [("s", msel("ta"), MTARGETS)]),
            ("list 4 A depth $1%", [("f", f"int(200*{msel('da')} - 100)")]),
        ]),
        ("MACRO B", [
            ("list 1 Macro $1", [("f", "acmcsel + 1")]),
            ("list 2 B $1", [("s", msel("tb"), MTARGETS)]),
            ("list 3 B depth $1%", [("f", f"int(200*{msel('db')} - 100)")]),
            ("list 4 Value $1%", [("f", f"int(100*{msel('v')})")]),
        ]),
        ("JOURNEY", [
            ("list 1 Speed $1", [("s", "acjour", [n for n, _ in SJOUR])]),
            ("list 2 Pads $1", [("s", "acjpad", [n for n, _ in JPAD_SETS])]),
            ("list 3 Drone $1", [("s", "acjdrone", SJDRONE)]),
            ("list 4 Bells $1", [("s", "acjstrike", SJSTRIKE)]),
        ]),
        ("COLOUR", [
            ("list 1 Pre-delay $1 ms", [("f", _pick("acrvpre", list(enumerate(SPRE))))]),
            ("list 2 Era $1", [("s", "acrvera", SERA)]),
            ("list 3 Sparkle $1%", [("f", "int(acspark*100)")]),
            ("list 4 Sparkle $1", [("s", "acsparko", SSPARKO)]),
        ]),
        ("CC OUT", [
            ("list 1 CC out $1", [("s", "acccout", ["off", "on"])]),
            ("list 2 Channel $1", [("f", "acccch")]),
            ("list 3 From CC $1", [("f", _pick("acccbase", list(enumerate(SCCBASE))))]),
            ("list 4 Rate $1", [("s", "acccrate", [n for n, _ in SCCRATE])]),
        ]),
    ]


def setup_rows():
    """the same table row by row: [(1, page 1 row 1, page 2 row 1, ...), (2, ...), ...] (setup() draws it so)"""
    pages = setup_pages()
    assert [n for n, _ in pages] == SETUP_NAMES
    return [(k + 1,) + tuple(rows[k] for _, rows in pages) for k in range(4)]

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
    item = "acsetpg*4 + acsk"           # the knob turned: page (0..) x 4 + knob (0..3)

    def at(page, row):
        """the condition: knob `row` (1-4) turned on SETUP page `page` (its name)"""
        return f"{item} == {SETUP_NAMES.index(page) * 4 + row - 1}"
    run_steps(c, (tb, 0), [
        If("acsetpg != acsetpgl", [X("1; 1; acsetpg", "v acsvp49", "v acsvp50", "v acsetpgl")]),
        If(at("GENERAL", 1), [V("acmout", "int(acsv*3.99)"), If("acmout == 0 || acmout == 3", [Call("ac-clockstop")],
                                                               [Call("ac-clockstart")]),
                            If("acmout < 2", [Call("ac-notesoff")], [Call("ac-outchord")])]),
        If(at("GENERAL", 2), [V("acsync", "acsv > 0.5"), SendL("ac-bpm", ["acbpm"])]),
        If(at("GENERAL", 3), [If("(acsv > 0.5) != acmodesel", [Call("ac-modetoggle")])]),
        If(at("GENERAL", 4), [V("acvintage", "acsv > 0.5"), SendL("ac-vintage", ["acvintage"])]),
        If(at("PLAYING", 1), [V("acfollow", "acsv")]),
        If(at("PLAYING", 2), [V("acnbr", "if(acsv < 0.25, 12, if(acsv < 0.5, 24, if(acsv < 0.75, 48, 96)))")]),
        If(at("PLAYING", 3), [V("acoutch", "1 + int(acsv*12.99)")]),
        If(at("PLAYING", 4), [V("accurve", "0.5 + 1.5*acsv")]),
        If(at("OUTPUT", 1), [V("acmono", f"int(acsv*{len(OUTPUTS) - 0.01})"), Call("ac-stereo")]),
        If(at("OUTPUT", 2), [V("acwidth", "0.5 + acsv"), Call("ac-stereo")]),
        If(at("OUTPUT", 3), [V("acpanmot", "acsv"), Call("ac-stereo")]),
        If(at("OUTPUT", 4), [V("actrange", f"int(acsv*{len(TEMPOS) - 0.01})"), Call("ac-settempo")]),
        If(at("NOTES OUT", 1), [V("acmparts", f"int(acsv*{len(PARTS) - 0.01})"), Call("ac-notesoff"), Call("ac-outchord")]),
        If(at("NOTES OUT", 2), [V("acarpoct", "24 + 12*int(acsv*4.99)"), Call("ac-notesoff"), Call("ac-outchord")]),
        If(at("NOTES OUT", 4), [V("acguard", "acsv > 0.5"),
                             If("acguard == 0 && acshed > 0", [V("acshed", "0"), Call("ac-layers"), Call("ac-inputupd")])]),
    ] + [
        # SOUNDS: act only when the choice changes, so turning the knob within one choice does not re-pick
        If(at("SOUNDS", 1 + j), [V("acsnew", f"int(acsv*{len(opts) - 0.01})"), If(f"acsnew != {var}", [
            V(var, "acsnew")] + ([V("acflstag", "0"), Call("ac-padpick")] if j == 0 else []) + [
            Call("ac-sndovr"), V("acfade", "1500"), Call("ac-layers")])])
        for j, (var, opts) in enumerate((("acspad", SPADS), ("acsdrone", SDRONES), ("acstex", STEXS), ("acschar", SCHARS)))
    ] + [
        # MUSIC: a choice applies at the next chord, which comes now
        If(at("MUSIC", 1), [V("acsnew", f"int(acsv*{len(SKEYS) - 0.01})"), If("acsnew != ackeyc", [
            V("ackeyc", "acsnew"), If("ackeyc > 0", [V("acpend", "ackeyc - 1"), V("achome", "35 + ackeyc"),
                                                     Call("ac-change")])])]),
        If(at("MUSIC", 2), [V("acsnew", f"int(acsv*{len(SSCALES) - 0.01})"), If("acsnew != acsclc", [
            V("acsclc", "acsnew"), If("acsclc > 0", [V("acsci", "acsclc - 1"), Call("ac-loadscale"),
                                                     Call("ac-change")])])]),
        If(at("MUSIC", 3), [V("acsnew", f"int(acsv*{len(SCHORDS) - 0.01})"), If("acsnew != acchdc", [
            V("acchdc", "acsnew"), If("acchdc > 0", [V("acfam", "acchdc - 1"), Call("ac-change")])])]),
        If(at("MUSIC", 4), [V("acpulc", f"int(acsv*{len(PULSES) - 0.01})"), Call("ac-pulseupd")]),
        # MIDI IN
        If(at("MIDI IN", 1), [V("acsnew", f"int(acsv*{len(ROUTES) - 0.01})"), If("acsnew != acroute", [
            Call("ac-allnotesoff"), V("acroute", "acsnew"), Call("ac-routehome"), V("acfade", "1500"),
            Call("ac-layers")])]),
        If(at("MIDI IN", 2), [V("acsnew", f"int(acsv*{len(BRTOS) - 0.01})"), If("acsnew != acbrto", [
            V("acbrto", "acsnew"), Call("ac-brfxoff")])]),
        If(at("MIDI IN", 3), [V("acpressto", f"int(acsv*{len(TARGETS) - 0.01})")]),
        # CC MAP: knob 1 picks a CC, knob 2 its target, knob 4 the vibrato rate
        If(at("CC MAP", 1), [V("acccsel", f"int(acsv*{len(CCS) - 0.01})")]),
        If(at("CC MAP", 2), [If(f"acccsel == {j}", [V(f"acmap{j}", f"int(acsv*{len(TARGETS) - 0.01})")])
                             for j in range(len(CCS))] + [If("achold && " + " && ".join(f"acmap{j} != 6" for j in range(7))
                                                            + " && acpressto != 6", [V("achold", "0"), Call("ac-holdoff")])]),
        If(at("CC MAP", 4), [V("acvibr", "0.5*int(6 + 10*acsv)"), SendL("ac-lvvibr", ["acvibr"])]),
        # VOICES: the bells' and the motion's engine, crossfaded at once
    ] + [
        If(at("VOICES", 1 + j), [V("acsnew", f"int(acsv*{len(opts) - 0.01})"), If(f"acsnew != {var}", [
            V(var, "acsnew"), V("acfade", "600"), Call("ac-layers")])])
        for j, (var, opts) in enumerate((("acsbell", SBELLS), ("acsmot", SMOTS)))
    ] + [
        # the glide applies from the next chord change
        If(at("VOICES", 3), [V("acglide", f"int(acsv*{len(GLIDES) - 0.01})")]),
        If(at("VOICES", 4), [V("acssub", f"int(acsv*{len(SSUBS) - 0.01})")]),
        # FORM: the shape applies to the next piece (or now, while the piece waits ready); the tempo and meter at
        # once; the atmosphere from the next section
        If(at("FORM", 1), [V("acsnew", f"int(acsv*{len(SFORMS) - 0.01})"), If("acsnew != acsform", [
            V("acsform", "acsnew"), Call("ac-formset")])]),
        If(at("FORM", 2), [V("acsnew", f"int(acsv*{len(STEMPOS) - 0.01})"), If("acsnew != acstempo", [
            V("acstempo", "acsnew"), Call("ac-settempo")])]),
        If(at("FORM", 3), [V("acsnew", f"int(acsv*{len(SMETERS) - 0.01})"), If("acsnew != acsmeter", [
            V("acsmeter", "acsnew"), If("acsmeter > 0", [V("acmeter", "acsmeter + 2")])])]),
        If(at("FORM", 4), [V("acsatm", f"int(acsv*{len(SATMS) - 0.01})"), If("acsatm > 0", [
            V("acatmcur", "acsatm - 1"), V("acfade", "3000"), Call("ac-layers")])]),
        # SECTIONS / SECTION MIX: editing a section turns the form to custom (from the piece's plan, the first
        # time); it applies to the piece at once (sections to come; the current one's layers now)
        # the section: turned fully down = now (follows the playing section), then sections 1-12
        If(at("SECTIONS", 1) + " || " + at("SECTION MIX", 1), [V("acsnew", "int(acsv*12.99)"), V("acsecfol", "acsnew == 0"),
                                             V("acsecsel", "if(acsnew == 0, min(11, acsec), acsnew - 1)")]),
        If(at("SECTION MIX", 2), [V("acslay", "int(acsv*7.99)")]),
    ] + [If(it, [Call("ac-customcopy"), V("acsform", "6"), act, Call("ac-customapply"),
                                Call("ac-secovr"), V("acfade", "1000"), Call("ac-layers")] + extra)
         for it, act, extra in (
             (at("SECTIONS", 2), T("acsroles", "acsecsel", f"int(acsv*{len(SROLES) - 0.01})"), []),
             (at("SECTIONS", 3), T("acslens", "acsecsel", f"int(acsv*{len(SLENS) - 0.01})"), []),
             (at("SECTIONS", 4), T("acssp", "acsecsel", f"int(acsv*{len(SPADS) - 0.01})"), [If("acsecsel == acsec", [Call("ac-padpick")])]),
             (at("SECTION MIX", 3), T("acsst", "acsecsel*8 + acslay", f"int(acsv*{len(SPLAY) - 0.01})"), []),
             (at("SECTION MIX", 4), T("acslv", "acsecsel*8 + acslay", "2*acsv"), []))
    ] + [
        # SAVES: knob 1 the slot, knob 2 up past 90 % saves, knob 3 loads (each re-arms below 90 %; a page change
        # re-arms only after the knob has gone down, so arriving with a knob up does nothing)
        If(at("SAVES", 1), [V("acslot", f"int(acsv*{NSLOTS - 0.01})"), Call("ac-slotcheck")]),
        If(at("SAVES", 2), [If("acsv > 0.9 && acsvp49 <= 0.9", [Call("ac-savepiece")]), V("acsvp49", "acsv")]),
        If(at("SAVES", 3), [If("acsv > 0.9 && acsvp50 <= 0.9", [Call("ac-loadpiece")]), V("acsvp50", "acsv")]),
        # LIVE
        If(at("LIVE", 1), [V("acmixcc", f"int(acsv*{len(SMIXCC) - 0.01})")]),
        If(at("LIVE", 2), [V("acpgm", f"int(acsv*{len(SPGM) - 0.01})")]),
        If(at("LIVE", 3), [V("aclfd", f"int(acsv*{len(SLFADE) - 0.01})")]),
        If(at("LIVE", 4), [V("acsfd", f"int(acsv*{len(SSFADE) - 0.01})")]),
        # RECALL
        If(at("RECALL", 1), [V("acmorph", f"int(acsv*{len(SMORPH) - 0.01})")]),
        If(at("RECALL", 2), [V("acrecall", "acsv > 0.5")]),
        If(at("RECALL", 3), [V("acancg", f"int(acsv*{len(SANCG) - 0.01})")]),
        If(at("RECALL", 4), [If("(acsv > 0.5) != accmp", [If("acsv > 0.5", [Call("ac-cmpon")], [Call("ac-cmpoff")])])]),
        # GROOVE
        If(at("GROOVE", 1), [V("acpump", f"int(acsv*{len(SPUMP) - 0.01})")]),
        If(at("GROOVE", 2), [V("acpumpd", "acsv")]),
        If(at("GROOVE", 3), [V("acduck", "acsv")]),
        If(at("GROOVE", 4), [V("acduckr", f"int(acsv*{len(SDUCKR) - 0.01})")]),
        # MACRO A / B
        If(at("MACRO A", 1) + " || " + at("MACRO B", 1), [V("acmcsel", "int(acsv*3.99)")]),
        If(at("MACRO A", 2), [If("acmcsel == 0", [V("acmc0mode", "acsv > 0.5")]), If("acmcsel == 1", [V("acmc1mode", "acsv > 0.5")]), If("acmcsel == 2", [V("acmc2mode", "acsv > 0.5")]), If("acmcsel == 3", [V("acmc3mode", "acsv > 0.5")])]),
        If(at("MACRO A", 3), [If("acmcsel == 0", [V("acmc0ta", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 1", [V("acmc1ta", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 2", [V("acmc2ta", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 3", [V("acmc3ta", f"int(acsv*{len(MTARGETS) - 0.01})")])]),
        If(at("MACRO A", 4), [If("acmcsel == 0", [V("acmc0da", "acsv")]), If("acmcsel == 1", [V("acmc1da", "acsv")]), If("acmcsel == 2", [V("acmc2da", "acsv")]), If("acmcsel == 3", [V("acmc3da", "acsv")])]),
        If(at("MACRO B", 2), [If("acmcsel == 0", [V("acmc0tb", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 1", [V("acmc1tb", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 2", [V("acmc2tb", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 3", [V("acmc3tb", f"int(acsv*{len(MTARGETS) - 0.01})")])]),
        If(at("MACRO B", 3), [If("acmcsel == 0", [V("acmc0db", "acsv")]), If("acmcsel == 1", [V("acmc1db", "acsv")]), If("acmcsel == 2", [V("acmc2db", "acsv")]), If("acmcsel == 3", [V("acmc3db", "acsv")])]),
        If(at("MACRO B", 4), [V("acmcn", "acmcsel"), V("acmcin", "acsv"), Call("ac-macro")]),
        # JOURNEY
        If(at("JOURNEY", 1), [V("acjour", f"int(acsv*{len(SJOUR) - 0.01})"), Call("ac-jourupd")]),
        If(at("JOURNEY", 2), [V("acjpad", f"int(acsv*{len(JPAD_SETS) - 0.01})"), Call("ac-jourupd")]),
        If(at("JOURNEY", 3), [V("acjdrone", "acsv > 0.5"), Call("ac-jourupd")]),
        If(at("JOURNEY", 4), [V("acjstrike", "int(acsv*3.99)"), Call("ac-jourupd")]),
        # COLOUR (the reverbs; GLINT below)
        If(at("COLOUR", 1), [V("acrvpre", f"int(acsv*{len(SPRE) - 0.01})"), Call("ac-rvcolour")]),
        If(at("COLOUR", 2), [V("acrvera", "int(acsv*3.99)"), Call("ac-rvcolour")]),
        If(at("COLOUR", 3), [V("acspark", "acsv"), Call("ac-sparkupd")]),
        If(at("COLOUR", 4), [V("acsparko", f"int(acsv*{len(SSPARKO) - 0.01})")]),
        If(at("SAVES", 4), [V("acsname", f"int(acsv*{len(NAME_WORDS) - 0.01})")]),
        # CC OUT
        If(at("CC OUT", 1), [V("acccout", "acsv > 0.5")]),
        If(at("CC OUT", 2), [V("acccch", "1 + int(acsv*15.99)")]),
        If(at("CC OUT", 3), [V("acccbase", "int(acsv*3.99)")]),
        If(at("CC OUT", 4), [V("acccrate", f"int(acsv*{len(SCCRATE) - 0.01})")]),
    ] + [
        Call("ac-oledsetup"), Send("ac-dirty"),
    ])
    c.col()
    proc(c, "ac-oledsetup", [
        Fill(0, 0, 128, 64, 0),
        Call("ac-setl0"), Call("ac-setl1"), Call("ac-setl2"), Call("ac-setl3"), Call("ac-setl4"),
        FLIP,
    ])
    Line("ac-setl0", "list SETUP $1 $2", [("f", "acsetpg + 1"), ("s", "acsetpg", SETUP_NAMES)], "ac-sett0")(c)
    # page-dependent rows: two Lines per row, chosen by the page
    defs = setup_rows()
    for k, *rows in defs:
        s = c.ch(c.recv(f"ac-setl{k}"), "expr acsetpg", "sel " + " ".join(str(j) for j in range(NSET)))
        for j, (ln, parts) in enumerate(rows):
            c.c(c.to((s, j), "t b"), 0, c.obj(f"s ac-setl{k}{'abcdefghijklmnopqrstuvwxyz'[j]}"), 0)
            if parts:
                Line(f"ac-setl{k}{'abcdefghijklmnopqrstuvwxyz'[j]}", ln, parts, f"ac-sett{k}")(c)
            else:
                c.c(c.m(c.recv(f"ac-setl{k}{'abcdefghijklmnopqrstuvwxyz'[j]}"), ln), 0, c.obj(f"s ac-sett{k}"), 0)
    for k in range(5):
        gated_text(c, f"ac-sett{k}", "acsetup", 0, 2 + k * 12)
    # aux tap in SETUP: the other page
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

