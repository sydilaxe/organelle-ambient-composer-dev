"""Live input, control side: MIDI (MPE notes, bend, breath), the Organelle keys as notes, voice allocation,
listening (focus pitch, key from a held note, breath raising the energy and holding a section),
audio analysis into a class (quiet / pitched / plucked / textural), and memories."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Line, Arm, Toast, RNG
from data import INMODES, NOTE_NAMES, SEND_BUS, FLAVOURS

NV = 4                                    # live voices

GLOBALS = dict(
    acmcix=-1, acmck=0, acmcb=0, acpgn=0,
    acnow=0, acext=0, acextt=-1e+06, acforce=-1, acroothold=0, acrootn=0, acsecfz=0, acauxheld=0, acauxused=0, acauxt=0,
    aclch=0, aclnote=0, aclvel=0, aclage=0, acvi=0, acheld=0, acfocus=-1, acfocust=0, acfkdone=0,
    acbreath=0, acbreatht=-1e+06, acbrmode=0, acbrt=-1e+06, acbrlast=0, acsechold=0, acfollow=0.7,
    acgbr=2, acnbr=48, aclbv=0, aclbs=0,
    acinlvl=0, acinp=-1, acinpp=-1, acinclr=0, acpconf=0, acnoisy=0, acons=0, acact=0, acinclass=0,
    acinhf=-40, acpst=0, acharm=0, acharmp=0, acgdry=0,
    acclt=0, aci2=40, aclnt=-1e+06, acyn=0, acbrfx=-1,
    acctlch=1, acctlv=0, acctlv127=0, acccn=0, actg=0, acvtsel=-1, achold=0, acwi=0, acmemn=0, acmemw=0, acmemt=-1e+06, acmemr=0, acmems=0, acmemrate=1, acgmem=0, acrec=0,
)
ARRAYS = dict(acyh=NV, actim=17, aclev=17, aclsus=NV, acbrch=17, aclvn=NV, aclvc=NV, aclva=NV, acbendt=17, achpc=12, acmemp=4, acmcp=8)
CLASSES = ["quiet", "pitched", "plucked", "texture"]


def midi_in():
    c = Canvas("midi-in", w=2400)
    c.comment("External MIDI -> ac-livenote 'ch note vel', ac-livebend 'ch semitones', ac-livebreath 'ch 0..1'. "
              "Channels fold to 1..16 (all ports).")
    n = c.obj("notein")
    pk = c.obj("pack f f f")
    for i in (2, 1, 0):
        c.c(n, i, pk, i)
    nm = c.to(pk, "expr ($f3-1) % 16 + 1; $f1; $f2")
    pk2 = c.obj("pack f f f")
    for i in (2, 1, 0):
        c.c(nm, i, pk2, i)
    t = c.to(pk2, "t l l")
    c.c(t, 1, c.obj("s ac-livenote"), 0)
    on = c.ch((t, 0), "unpack f f f", ao=0)
    c.c(c.ch((on, 2), "sel 0"), 1, c.obj("s ac-extnote"), 0)
    c.col()
    b = c.obj("bendin")
    bp = c.obj("pack f f")
    c.c(b, 1, bp, 1)
    c.c(b, 0, bp, 0)
    bx = c.to(bp, "expr ($f2-1) % 16 + 1; ($f1-8192)/8192 * if(($f2-1) % 16 == 0, acgbr, acnbr)")
    bp2 = c.obj("pack f f")
    c.c(bx, 1, bp2, 1)
    c.c(bx, 0, bp2, 0)
    c.c(bp2, 0, c.obj("s ac-livebend"), 0)
    c.col()
    # channel and poly pressure -> ac-pressin "ch value127" (SETUP Pressure to)
    br = c.obj("s ac-pressin")
    tch = c.obj("touchin")
    tp = c.obj("pack f f")
    c.c(tch, 1, tp, 1)
    c.c(tch, 0, tp, 0)
    c.c(c.m(tp, "$2 $1"), 0, br, 0)
    pt = c.obj("polytouchin")
    pp = c.obj("pack f f")
    c.c(pt, 2, pp, 1)
    c.c(pt, 0, pp, 0)
    c.c(c.m(pp, "$2 $1"), 0, br, 0)
    cc = c.obj("ctlin")
    cp = c.obj("pack f f f")
    for i in (2, 1, 0):
        c.c(cc, i, cp, i)
    rt = c.ch(c.m(cp, "$2 $3 $1"), "route 123 120")
    for o in (0, 1):
        c.c(c.to((rt, o), "t b"), 0, c.obj("s ac-allnotesoff"), 0)
    # every other CC -> ac-ccin "cc value ch" (SETUP CC MAP)
    c.c(c.m((rt, 2), "$1 $2 $3"), 0, c.obj("s ac-ccin"), 0)
    # a program change (1-16) loads that save slot, if SETUP LIVE allows it
    pg = c.obj("pgmin")
    c.c(pg, 0, c.obj("s ac-pgmin"), 0)
    c.col()
    tpg = c.to(c.recv("ac-pgmin"), "t b f")
    c.c(tpg, 1, c.obj("v acpgn"), 0)
    run_steps(c, (tpg, 0), [If("acpgm && acpgn >= 1 && acpgn <= 16", [V("acslot", "acpgn - 1"),
                                                                        Call("ac-slotcheck"), Call("ac-loadpiece")])])
    return c


def cc_map():
    """SETUP CC MAP and Pressure to: a CC or pressure goes to one target (gen_setup.TARGETS)."""
    import gen_setup as _S
    c = Canvas("cc-map", w=2400)
    c.comment("CCs and pressure -> their target: breath, the live voices (per channel; channel 1 = all), hold, "
              "or a knob of the piece")
    up = c.to(c.recv("ac-ccin"), "unpack f f f")
    c.c(up, 2, c.obj("v acctlch"), 0)
    c.c(up, 1, c.obj("v acctlv127"), 0)
    tb = c.to(up, "t b f")
    c.c(tb, 1, c.obj("v acccn"), 0)
    look = "-1"
    for j, n in reversed(list(enumerate(_S.CCS))):
        look = f"if(acccn == {n}, acmap{j}, {look})"
    # SETUP LIVE Mix CCs: 16 CCs from the base - 8 layer levels (the MIX knobs), then 8 in/out buttons
    mixknob = _S.SEND_KNOBS
    order = [0, 1, 2, 3, 4, 5, 7, 6]   # level CCs in layer-key order (drone .. atmosphere, cloud) -> MIX knob
    lvl = "if(acmcix == 0, 0" + "".join(f", if(acmcix == {i}, {o}" for i, o in enumerate(order) if i) + ", 0" + ")" * 8
    run_steps(c, (tb, 0), [X("acccn; acctlv127", "v aclastcc", "v aclastv"),
                           V("acmcix", f"if(acmixcc > 0, acccn - {_S.MIXCC_BASE}, -1)"),
                           If("acmcix >= 0 && acmcix < 16", [Call("ac-mixcc")], [
                               V("actg", look), If("actg >= 0", [Call("ac-ctl")])])])
    proc(c, "ac-mixcc", [
        If("acmcix < 8", [V("acmck", f"{mixknob} + {lvl}"), T("acparams", "acmck", "acctlv127/127"),
                          SendL("ac-param", ["acmck", "acctlv127/127"])],
           [V("acmcb", "acmcix - 8"),
            If("acctlv127 >= 64 && acmcp[int(acmcb)] < 64", [If(f"acmcb == {i}", [Call(f"ac-laykey{i}")]) for i in range(8)]),
            T("acmcp", "acmcb", "acctlv127")])])
    c.col()
    up = c.to(c.recv("ac-pressin"), "unpack f f")
    c.c(up, 1, c.obj("v acctlv127"), 0)
    tb = c.to(up, "t b f")
    c.c(tb, 1, c.obj("v acctlch"), 0)
    run_steps(c, (tb, 0), [V("actg", "acpressto"), Call("ac-ctl")])
    c.col()
    vch = lambda i: f"aclvc[{i}]"
    tone = lambda i: f"0.5 + actim[int({vch(i)})] + ({vch(i)} != 1)*actim[1]"
    lev = lambda i: f"(1 - aclev[int({vch(i)})])*(1 - ({vch(i)} != 1)*aclev[1])"
    mine = lambda i: f"aclvn[{i}] >= 0 && (aclvc[{i}] == acctlch || acctlch == 1)"
    knobs = [n for p in _S.PAGES for _, n, _ in p]
    proc(c, "ac-ctl", [
        V("acctlch", "(acctlch - 1) % 16 + 1"), V("acctlv", "acctlv127/127"),
        If("actg == 1", [SendL("ac-livebreath", ["acctlch", "acctlv127"])]),
        If("actg == 2", [SendL("ac-lvvib", ["acctlv"])]),
        If("actg == 3", [T("actim", "acctlch", "acctlv - 0.5")]
           + [If(mine(i), [SendL("ac-lvtim", [str(i), tone(i)])]) for i in range(NV)]),
        If("actg == 4", [T("aclev", "acctlch", "1 - acctlv")]
           + [If(mine(i), [SendL("ac-lvlev", [str(i), lev(i)])]) for i in range(NV)]),
        If("actg == 5", [V("acvtsel", f"int(acctlv*{len(FLAVOURS) - 0.01})"), SendL("ac-lvtype", ["acvtsel"])]),
        If("actg == 6", [If("(acctlv >= 0.5) != achold", [V("achold", "acctlv >= 0.5"),
                                                          If("achold == 0", [Call("ac-holdoff")])])]),
        If("actg == 10", [SendL("ac-brsw", ["acctlv", "30"])]),
        # resolve: held while the CC is 64 or more (a pedal), released below
        If("actg == 12", [If("(acctlv >= 0.5) != acres", [V("acres", "acctlv >= 0.5"), Call("ac-resolveupd")])]),
        # root: the CC's range spread over the 12 keys (an encoder or a slider); next section / chord now: on a
        # press (64 and up); glide: its 6 steps
        If("actg == 13", [V("acrootn", "int(acctlv*11.99)"), If("acrootn != acpend", [Call("ac-rootset")])]),
        If("actg == 14", [If("acctlv >= 0.5 && acnsx == 0", [V("acsec", "acsec+1"), Call("ac-section"),
                                                             Toast("next section")]), V("acnsx", "acctlv >= 0.5")]),
        If("actg == 15", [If("acctlv >= 0.5 && acchx == 0", [Call("ac-chordnow")]), V("acchx", "acctlv >= 0.5")]),
        If("actg == 16", [V("acglide", "int(acctlv*5.99)")]),
    ] + [If(f"actg == {t}", [T("acparams", knobs.index(n), "acctlv"), SendL("ac-param", [str(knobs.index(n)), "acctlv"])])
         for t, n in _S.TARGET_KNOB.items()])
    # a new note takes its channel's tone and level
    proc(c, "ac-lvctl", [SendL("ac-lvtim", ["acvi", "0.5 + actim[int(aclch)] + (aclch != 1)*actim[1]"]),
                         SendL("ac-lvlev", ["acvi", "(1 - aclev[int(aclch)])*(1 - (aclch != 1)*aclev[1])"])])
    return c


def live():
    c = Canvas("live", w=3600)
    c.comment("Live notes: allocate 4 voices (oldest stolen), MPE bend and breath per channel, listening")
    # a coarse clock for timeouts (ms)
    met = c.obj("metro 100")
    c.c(c.to(c.recv("ac-init"), "delay 60"), 0, met, 0)
    c.c(met, 0, c.obj("s ac-now"), 0)
    c.col()
    proc(c, "ac-now", [V("acnow", "acnow + 100"), If("acrun", [V("acel", "acel + 100/actime"),
                                                               V("acsecel", "acsecel + 100")]), If("int(acnow) % 500 == 0", [Call("ac-listen")]), Call("ac-ana"),
                            # a custom section's layers coming in or going out at 1/4, 1/2, 3/4 of it
                            If("acrun && acsecc", [V("acsecqn", "min(3, int(4*acsecel/max(1, acsecdur*actime)))"),
                                                   If("acsecqn != acsecq", [V("acsecq", "acsecqn"), Call("ac-secovr"),
                                                                            V("acfade", __import__("gen_setup").SFADE), Call("ac-layers")])]),
                            # SETUP page 7 shows the breath level as it comes in
                            If("acsetup && acsetpg >= 6 && int(acnow) % 300 == 0", [Call("ac-oledsetup")])])
    # ---- notes
    up = c.to(c.recv("ac-livenote"), "unpack f f f")
    for i, n in ((2, "aclvel"), (1, "aclnote")):
        c.c(up, i, c.obj("v " + n), 0)
    tb = c.to(up, "t b f")
    c.c(tb, 1, c.obj("v aclch"), 0)
    c.col()
    oldest = ("if(aclva[0]<=aclva[1] && aclva[0]<=aclva[2] && aclva[0]<=aclva[3], 0, "
              "if(aclva[1]<=aclva[2] && aclva[1]<=aclva[3], 1, if(aclva[2]<=aclva[3], 2, 3)))")
    on = [
        V("acvi", f"if(aclvn[0]<0, 0, if(aclvn[1]<0, 1, if(aclvn[2]<0, 2, if(aclvn[3]<0, 3, {oldest}))))"),
        V("acheld", "min(4, acheld + (aclvn[int(acvi)] < 0))"),
        V("aclage", "aclage + 1"),
        T("aclvn", "acvi", "aclnote"), T("aclvc", "acvi", "aclch"), T("aclva", "acvi", "aclage"), T("aclsus", "acvi", "0"),
        Call("ac-lvctl"),
        SendL("ac-lvbr", ["acvi", "if(acbrmode, max(acbrch[int(aclch)], acbrch[1]), 1)"]),
        If("acroute == 0", [SendL("ac-lvon", ["acvi", "aclnote + acbendt[int(aclch)]", "aclvel/127"])]),
        V("aclnt", "acnow"),
        T("achpc", "int(aclnote) % 12", "achpc[int(aclnote) % 12] + 1"),
        X("int(aclnote) % 12; acnow; 0", "v acfocus", "v acfocust", "v acfkdone"),
        # SETUP Notes to: chords / drone / bells / cloud
        If("acroute == 1", [Call("ac-youchord")]),
        If("acroute == 2", [SendL("ac-dronep", ["36 + int(aclnote) % 12", "150"]),
                            SendL("ac-subp", ["mtof(24 + int(aclnote) % 12)", "150"])]),
        If("acroute == 3", [SendL("ac-bell", ["aclnote + 12*(aclnote < 60)", "0.25 + 0.75*aclvel/127", "0.5"])]),
        If("acroute == 4", [If(f"acvi == {i}", [SendL(f"ac-gr{i}", [
            "pow(2, (aclnote - actonic - 12*floor((aclnote - actonic)/12))/12)"])]) for i in range(NV)]),
    ]
    off = [
        V("acvi", " + ".join(f"if(aclvn[{i}]==aclnote && aclvc[{i}]==aclch, {i + 1}, 0)" for i in range(NV)) + " - 1"),
        If("acvi >= 0", [T("aclvn", "acvi", "-1"), SendL("ac-lvoff", ["acvi"]), V("acheld", "max(0, acheld - 1)"),
                         T("achpc", "int(aclnote) % 12", "max(0, achpc[int(aclnote) % 12] - 1)")]),
        If("acheld == 0", [V("acfocus", "-1")]),
        If("acroute == 1 && acheld > 0", [Call("ac-youchord")]),
        If("acroute == 4 && acvi >= 0", [If(f"acvi == {i}", [SendL(f"ac-gr{i}", ["1"])]) for i in range(NV)]),
        If("acroute >= 2 && acheld == 0", [Call("ac-routehome")]),
    ]
    proc(c, "ac-noteoff", off)
    # hold (a CC mapped to hold, e.g. 64): a released note keeps sounding until hold lets go
    held_i = V("acvi", " + ".join(f"if(aclvn[{i}]==aclnote && aclvc[{i}]==aclch, {i + 1}, 0)" for i in range(NV)) + " - 1")
    # while the Root key (low C#) is held, a note picks the next key instead of playing
    run_steps(c, (tb, 0), [If("aclvel > 0 && acroothold", [V("acrootn", "int(aclnote) % 12"), Call("ac-rootset")],
                              [If("aclvel > 0", on, [If("achold", [held_i, If("acvi >= 0", [T("aclsus", "acvi", "1")])],
                                                     [Call("ac-noteoff")])])])])
    proc(c, "ac-holdoff", [If(f"aclsus[{i}] && aclvn[{i}] >= 0", [V("aclnote", f"aclvn[{i}]"), V("aclch", f"aclvc[{i}]"),
                                                                 T("aclsus", i, "0"), Call("ac-noteoff")])
                           for i in range(NV)])
    c.col()
    # Notes to chords: the held notes become the pad chord (doubled an octave up when fewer than 4)
    steps = [V("acyn", "0")] + [If(f"aclvn[{i}] >= 0", [T("acyh", "acyn", f"aclvn[{i}]"), V("acyn", "acyn + 1")])
                                for i in range(NV)]
    ch = []
    for k in range(4):
        ch += [V("acp1", f"acyh[int({k} % int(acyn))] + 12*int({k}/acyn)"),
               V("acp1", "if(acp1<43, acp1+12, if(acp1>86, acp1-12, acp1))"),
               V("acp1", "if(acp1<43, acp1+12, if(acp1>86, acp1-12, acp1))"),
               T("acnew", k, "acp1"), T("acch", k, "acp1"),
               SendL(f"ac-v{k}-pitch", [f"acnew[{k}]", "300*(acglide > 0)", "0"])]
    proc(c, "ac-youchord", steps + [If("acyn > 0", ch + [Call("ac-change2")])])
    # back to the composer's drone and grains when the notes stop (or Notes to changes)
    proc(c, "ac-routehome", [SendL("ac-dronep", ["actonic", "1500"]), SendL("ac-subp", ["mtof(actonic - 12)", "1500"]),
                             Call("ac-grains")])
    proc(c, "ac-allnotesoff", [Loop(str(NV), "aci", [T("aclvn", "aci", "-1"), SendL("ac-lvoff", ["aci"])]),
                               V("acheld", "0"), V("acfocus", "-1")])
    proc(c, "ac-extnote", [V("acext", "1"), V("acextt", "acnow")])
    # ---- bend: remember per channel, retune the voices on that channel
    ub = c.to(c.recv("ac-livebend"), "unpack f f")
    c.c(ub, 1, c.obj("v aclbs"), 0)
    tbb = c.to(ub, "t b f")
    c.c(tbb, 1, c.obj("v aclch"), 0)
    run_steps(c, (tbb, 0), [T("acbendt", "aclch", "aclbs")] +
              [If(f"aclvc[{i}]==aclch && aclvn[{i}]>=0", [SendL("ac-lvbend", [str(i), "aclbs"])]) for i in range(NV)])
    c.col()
    # ---- breath: per channel (MPE) or all voices (channel 1); a breath controller switches voices to breath
    # control for as long as it keeps sending
    ubr = c.to(c.recv("ac-livebreath"), "unpack f f")
    c.c(c.to((ubr, 1), "expr pow($f1/127, accurve)"), 0, c.obj("v aclbv"), 0)
    tch = c.to(ubr, "t b f")
    c.c(c.to((tch, 1), "expr ($f1-1) % 16 + 1"), 0, c.obj("v aclch"), 0)
    tbr = c.to(tch, "t b")
    run_steps(c, (tbr, 0), [
        If("acbrmode == 0 && acbrto <= 1", [V("acbrmode", "1"), SendL("ac-brmode", ["1"]), Toast("breath control")]),
        V("acbrt", "acnow"), T("acbrch", "aclch", "aclbv"),
        V("acbreath", "max(aclbv, acbreath*0.7)"),
        If("aclbv > 0.1", [V("acbreatht", "acnow")]),
        # SETUP Breath to: one thing of the piece (sent when it moves)
        If("acbrto >= 3 && abs(aclbv - acbrfx) > 0.015", [
            V("acbrfx", "aclbv"),
            If("acbrto == 3", [SendL("ac-bright", ["min(1, acbright*(0.25 + 1.5*aclbv))", "40"])]),
            If("acbrto == 4", [SendL("ac-sg-" + n, [f"3.6*{n}*aclbv", "40"]) for n in SEND_BUS]),
            If("acbrto == 5", [SendL("ac-brsw", ["aclbv", "40"])]),
        ]),
    ] + [If(f"acbrto <= 1 && (aclvc[{i}]==aclch || aclch==1) && aclvn[{i}]>=0", [SendL("ac-lvbr", [str(i), "aclbv"])])
         for i in range(NV)])
    proc(c, "ac-brfxoff", [V("acbrfx", "-1"), SendL("ac-brsw", ["1", "1500"]), Call("ac-sendupd"), Call("ac-brightupd"),
                           If("acbrmode && acbrto > 1", [V("acbrmode", "0"), SendL("ac-brmode", ["0"])])])
    c.col()
    # ---- listening, every 500 ms
    proc(c, "ac-listen", [
        V("acbreath", "acbreath*0.85"),
        # breath raises the density (and so the energy) of the piece
        If("abs(acbreath - acbrlast) > 0.08", [V("acbrlast", "acbreath"), V("acfade", "1500"), Call("ac-layers")]),
        If("acbrmode && acnow - acbrt > 10000", [V("acbrmode", "0"), SendL("ac-brmode", ["0"])]),
        If("acbrto >= 3 && acbrfx >= 0 && acnow - acbrt > 10000", [Call("ac-brfxoff")]),
        # a held note for 6 s becomes the key centre (once per note)
        If("acfocus >= 0 && acnow - acfocust > 6000 && acfkdone == 0 && acfollow > 0.3 && ackeyc == 0 && "
           "acfocus != int(actonic) % 12 && acpend < 0", [
            V("acpend", "acfocus"), V("acfkdone", "1"), Call("ac-keyfromyou")]),
        # memories: capture what you play now and then, while the piece develops
        If("acrec == 0 && acact > 0.6 && (acpconf > 0.4 || acons > 0.6) && acnow - acmemt > 45000 && "
           "acrole >= 1 && acrole <= 4 && acinput > 0.05", [Call("ac-memrec")]),
    ])
    Line("ac-keyfromyou", "list key from you $1", [("s", "acfocus", NOTE_NAMES)], "ac-toast")(c)
    c.col()
    # ---- audio analysis, every 100 ms: pitchedness, onset rate, noisiness -> class
    proc(c, "ac-ana", [
        V("acact", "0.9*acact + 0.1*((acinlvl > 48) || acons > 0.5)"),
        V("acpst", "(acinp > 0 && abs(acinp - acinpp) < 0.6 && acinclr > 0.55)"),
        X("0.9*acpconf + 0.1*acpst*(acinlvl > 48); 0.95*acons; 0.9*acnoisy + 0.1*(acinhf > -14)*(acinlvl > 48); acinp",
          "v acpconf", "v acons", "v acnoisy", "v acinpp"),
        V("acclt", "if(acact < 0.3, 0, if(acpconf > 0.45, 1, if(acons > 0.9, 2, 3)))"),
        If("acclt != acinclass", [V("acinclass", "acclt"), If("acinmode == 0", [Call("ac-inputupd")]),
                                   Call("ac-scr5")]),
        # a sung or played pitch steers the harmony like a held MIDI note (MIDI has priority)
        If("acinclass == 1 && acpst && acheld == 0 && acinput > 0.05", [
            If("int(acinp + 0.5) % 12 != acfocus", [X("int(acinp + 0.5) % 12; acnow; 0", "v acfocus", "v acfocust",
                                                      "v acfkdone")]),
            # harmonised grains: retune the cloud to the chord around the sung pitch
            If("acharm && abs(acinp - acharmp) > 1", [V("acharmp", "acinp"), Call("ac-grains")]),
        ]),
        If("acinclass != 1 && acheld == 0 && acfocus >= 0 && acnow - acfocust > 3000", [V("acfocus", "-1")]),
    ])
    proc(c, "ac-inonset2", [V("acons", "acons + 0.3"), V("acinon", "1")])
    return c


def memories():
    c = Canvas("memories", w=2400)
    c.comment("4 memory slots of 8 s from the input. The piece brings them back, transformed, in break, return "
              "and dissolve sections (and sometimes the climax).")
    proc(c, "ac-memrec", [
        X("1; acnow; acmemw", "v acrec", "v acmemt", "v acmemr"),
        T("acmemp", "acmemw", "if(acinclass == 1, acinp, -1)"),
        SendL("ac-memrecslot", ["acmemw"]),
        V("acmemw", "(acmemw + 1) % 4"), V("acmemn", "min(4, acmemn + 1)"),
        Call("ac-memtoast"),
        Arm("ac-memrecdone", "8100"),
    ])
    Line("ac-memtoast", "list memory $1 recording", [("f", "acmemr + 1")], "ac-toast")(c)
    proc(c, "ac-memrecdone", [V("acrec", "0")])
    # at a section start: maybe recall a memory
    proc(c, "ac-memsec", [
        RNG,
        If("acmemn > 0 && ((acrole >= 5 && acr1 < 0.8) || (acrole == 4 && acr1 < 0.4))", [
            V("acmems", "int(acr2*acmemn)"),
            # return: retuned to the chord; break: reversed and half speed; dissolve: half speed; climax: as is
            V("acmemrate", "if(acrole == 6 && acmemp[int(acmems)] > 0, pow(2, (acnew[0] + 12*floor((acmemp["
                           "int(acmems)] - acnew[0])/12 + 0.5) - acmemp[int(acmems)])/12), if(acrole == 5, -0.5, "
                           "if(acrole == 7, 0.5, 1)))"),
            SendL("ac-memplay", ["acmems", "acmemrate"]),
            SendL("ac-g-mem", ["0.9", "6000"]),
        ], [SendL("ac-g-mem", ["0", "8000"])]),
    ])
    return c


def tables():
    c = Canvas("live-tables")
    c.comment("Arrays for the pitch tracker and the memories; the analysis window is built at start-up")
    for n in ("acacf 2048", "achann 2048") + tuple(f"acmem{i} 352800" for i in range(4)):
        c.obj("array define " + n)
    proc(c, "ac-init", [Loop("2048", "acwi", [T("achann", "acwi",
                                                 "if(acwi < 1024, 0.5 - 0.5*cos(6.283185*acwi/1024), 0)")])])
    return c


def setup_values():
    return GLOBALS, ARRAYS
