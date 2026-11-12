"""The composer's control logic: seed, piece, form (sections), harmony (changes), event players.

Conventions: global state lives in [value]s named ac<word> (no dash, so [expr] can read them);
every [send]/[receive] name has a dash (ac-<word>), so values and sends never share a symbol."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps
from data import *

NF = len(FAMILIES)
NS = len(SCALES)

GLOBALS = dict(
    acseed=1, account=0, actonic=38, acsci=0, acn=7, acfamA=0, acfamB=1, acfam=0, acdeg=0, acpend=-1,
    acmode=0, acrun=1, acended=0, acsec=0, acnsec=6, acenergy=0.5, acdeff=0.5, acsecdur=60000, acchsec=20,
    acpage=0, acinmode=0, acfreeze=0, accapt=0,
    acmdrone=1, acmpad=1, acmtex=1, acmcloud=1, acmbell=1,
    acfdrone=1, acftex=1, acfcloud=1, acfbell=1, actex1=0, actex2=1, actexA=0, actexB=1,
    acpal1=0, acpal2=1, acpal3=3, acpartI=0, acbellI=0, acsecbright=0.8, actidef=1, acskew=1, acpow=1,
    acpsum=1, acfirst=1, acmodflag=0, acD=0, acp0=0, acp1=0, acnewt=38, aci=0, acchg=0, acfade=8000,
    actime=1, acgdrone=0, acgpad=0, acgtex=0, acgcloud=0, acgbell=0, acgt0=0, acgt1=0, acgt2=0, acgt3=0,
    acbi=0, acbc=0, acdropi=0, acbright=0.5, acbp=0, acgdurv=300, acr1=0.5, acr2=0.5, acr3=0.5, acr4=0.5,
    acknown0=0, acknown1=0, acknown2=0, acknown3=0, acinprev=0, acghost=0,
)
for page in PAGES:
    for _, name, d in page:
        GLOBALS[name] = d

ARRAYS = dict(acscale=16, acfamt=NF * 5, acch=4, acnew=4, acplan=16, acpdur=16, acmotif=8, acmoves=12,
              acmods=12, acgrt=12, acfmrt=8, acpartt=24, acbellt=12, acdintt=5, acrhyt=5, acparams=8,
              acraw=4, acflav=4)


def deg2p(d):
    """scale degree (may be negative) -> pitch above the tonic"""
    return (f"(actonic + 12*floor(({d})/acn) + "
            f"acscale[(int({d}) % int(acn) + int(acn)) % int(acn)])")


def Arm(tick, expr, stop=None):
    """(re)start a [delay] of expr ms that then bangs [s tick]; [s stop] cancels it."""
    def st(c, src):
        e = c.obj("expr " + expr)
        c.c(*src, e, 0)
        d = c.obj("delay")
        c.c(e, 0, d, 0)
        c.c(d, 0, c.obj("s " + tick), 0)
        if stop:
            c.c(c.m(c.recv(stop), "stop"), 0, d, 0)
    return st


def Toast(text):
    return Send("ac-toast", "list " + text)


RNG = Call("ac-rng")


def globals_():
    g = Canvas("globals")
    g.comment("Every global value, its default, and the data tables")
    for name in GLOBALS:
        g.obj("v " + name)
    g.col()
    for name, n in ARRAYS.items():
        g.obj(f"array define {name} {n}")
    g.col()
    r = g.recv("ac-init")
    t = g.to(r, "t b b")
    # defaults
    for name, val in GLOBALS.items():
        g.c(g.m((t, 1), str(val)), 0, g.obj("v " + name), 0)
    g.col()
    fam = []
    for _, typ, offs in FAMILIES:
        fam += [typ] + offs
    tables = dict(acfamt=fam, acmoves=MOVES, acmods=MODS, acgrt=GRAIN_RATIOS, acfmrt=FM_RATIOS,
                  acpartt=sum(PARTIAL_SETS, []), acbellt=sum(BELL_SETS, []), acdintt=DRONE_INTERVALS,
                  acrhyt=RHYTHMS, acparams=[d for p in PAGES for _, _, d in p], acraw=[0.5] * 4)
    for name, vals in tables.items():
        m = g.m((t, 0), " ".join(f"{v:g}" for v in vals))
        g.c(m, 0, g.obj("array set " + name), 0)
    g.col()
    # scale loader
    r = g.recv("ac-loadscale")
    e = g.to(r, "expr acsci")
    tl = g.obj("t l l")
    s = g.to(e, "sel " + " ".join(str(i) for i in range(NS)))
    for i, (_, iv) in enumerate(SCALES):
        g.c(g.m((s, i), " ".join(f"{v:g}" for v in iv)), 0, tl, 0)
    g.c(g.to((tl, 1), "list length"), 0, g.obj("v acn"), 0)
    g.c(tl, 0, g.obj("array set acscale"), 0)
    return g


def rng():
    c = Canvas("rng")
    c.comment("ac-rng: refresh acr1..acr4 (0..1). Seeded per piece, so a seed replays its piece.")
    r = c.recv("ac-rng")
    t = c.to(r, "t b b b b")
    rs = c.recv("ac-seedrng")
    ts = c.to(rs, "t f f f f")
    c.col()
    for k in range(4):
        rnd = c.to((t, k), "random 1000000")
        c.ch(rnd, "/ 1e+06", f"v acr{k + 1}")
        # the first draws after a seed are close for some seeds (Pd's LCG): seed, then discard 5 draws
        tw = c.to(c.to((ts, k), f"+ {k * 7919 + 1}"), "t b b b b b f")
        c.c(c.m((tw, 5), "seed $1"), 0, rnd, 0)
        for j in range(5):
            c.c(tw, j, rnd, 0)
    return c


def seed():
    c = Canvas("seed")
    c.comment("A counter in seed.txt goes up at every start-up; with timing jitter it seeds the first piece.")
    td = c.obj("text define acseedf")
    rt = c.obj("realtime")
    r = c.recv("ac-seedinit")
    t = c.to(r, "t b b b")
    c.c(t, 2, rt, 0)
    c.c(c.m((t, 1), "read seed.txt"), 0, td, 0)
    mo = c.ch((t, 0), "text size acseedf", "moses 1")
    cnt = c.obj("+ 1")
    c.c(c.m((mo, 0), "0"), 0, cnt, 0)
    c.c(c.ch(c.m((mo, 1), "0"), "text get acseedf"), 0, cnt, 0)
    tf = c.to(cnt, "t f f")
    c.c(c.m((tf, 1), "set $1, write seed.txt"), 0, td, 0)
    c.c(tf, 0, c.obj("v account"), 0)
    tb = c.to(tf, "t b")
    c.c(tb, 0, rt, 1)
    c.ch(rt, "expr int(fmod(account*7919 + $f1*1000003, 9999991))", "s ac-setseed")
    c.col()
    # explicit seed (tests, or to replay a piece) and the new-piece key (seeded by how long the patch ran)
    st = c.to(c.recv("ac-setseed"), "t b f f")
    c.c(st, 2, c.obj("v acseed"), 0)
    c.c(st, 1, c.obj("s ac-seedrng"), 0)
    c.c(st, 0, c.obj("s ac-newpiece"), 0)
    rt2 = c.obj("realtime")
    c.c(c.recv("ac-init"), 0, rt2, 0)
    c.c(c.recv("ac-reseed"), 0, rt2, 1)
    c.ch(rt2, "expr int(fmod(acseed*31 + $f1*977, 9999991)) + 1", "s ac-setseed")
    return c


def piece():
    c = Canvas("piece", w=2600)
    c.comment("A new piece: tonic, scale, two voicing families, a timbre palette, partial and FM ratios, LFOs")
    steps = [
        RNG,
        V("actonic", "36 + int(acr1*12)"),
        V("acsci", "int(acr2*%d)" % NS), Call("ac-loadscale"),
        V("acfamA", f"int(acr3*{NF})"), V("acfamB", f"int(acr4*{NF})"),
        RNG,
        X("int(acr1*%d); int(acr2*%d); int(acr3*%d)" % ((len(FLAVOURS),) * 3), "v acpal1", "v acpal2", "v acpal3"),
        SendL("ac-fmr", ["acfmrt[int(acr4*8)]"]),
        RNG,
        X("int(acr1*%d); int(acr2*4); int(acr3*4); int(acr4*%d)" % (len(PARTIAL_SETS), len(BELL_SETS)),
          "v acpartI", "v actexA", "v actexB", "v acbellI"),
        SendL("ac-partials", ["acpartt[int(acpartI)*4+1]", "acpartt[int(acpartI)*4+2]", "acpartt[int(acpartI)*4+3]"]),
        SendL("ac-bellset", ["acbellt[int(acbellI)*3]", "acbellt[int(acbellI)*3+1]", "acbellt[int(acbellI)*3+2]"]),
        RNG,
        SendL("ac-dint", ["acdintt[int(acr1*5)]"]),
    ]
    for k in range(4):
        steps += [RNG, SendL(f"ac-v{k}-lfo", ["0.02+acr1*0.1", "0.03+acr2*0.15", "0.04+acr3*0.25", "0.03+acr4*0.2"])]
    steps += [
        X("0; -1; 0; 1; 0; 0; 1; 0", "v acdeg", "v acpend", "v acchg", "v acfirst", "v acended", "v accapt", "v acrun",
          "v acsec"),
        Send("ac-master", "1 3000"),
        Call("ac-plan"),
        Call("ac-section"),
        Call("ac-change"),
        Call("ac-motifgen"),
        Call("ac-brightupd"), Call("ac-revupd"), Call("ac-inputupd"),
        SendL("ac-weird", ["acweird"]), SendL("ac-motion", ["acmotion"]),
        Call("ac-scr"),
    ]
    proc(c, "ac-newpiece", steps)
    # the form of a composition: 5-8 sections whose energies rise to a peak and fall away
    proc(c, "ac-plan", [
        RNG,
        X("5 + int(acr1*4); 0.7 + acr2*0.8; 0.6 + acr3*0.9; 0", "v acnsec", "v acskew", "v acpow", "v acpsum"),
        Loop("acnsec", "aci", [
            RNG,
            T("acplan", "aci",
              "if(aci==0, 0.1+acr2*0.12, if(aci==acnsec-1, 0.22, min(1, max(0.12, 0.15 + 0.85*pow(sin(3.14159*"
              "pow((aci+0.5)/acnsec, acskew)), acpow) + (acr1-0.5)*0.24))))"),
            T("acpdur", "aci", "0.7 + acr3*0.6"),
            V("acpsum", "acpsum + acpdur[int(aci)]"),
        ]),
    ])
    # a 5-note motif for the bells: a random walk in scale degrees, with its own rhythm
    proc(c, "ac-motifgen", [
        Loop("5", "aci", [
            RNG,
            T("acmotif", "aci", "if(aci==0, int(acr1*3)*2, acmotif[int(aci)-1] + int(acr1*5) - 2)"),
            T("acmrhy", "aci", "acrhyt[int(acr2*5)]"),
        ]),
    ])
    c.obj("array define acmrhy 8")
    return c


def section():
    c = Canvas("section", w=2600)
    c.comment("A section: energy (from the plan, or random when drifting), voicing, timbres, layers, length")
    rest = [
        RNG,
        V("acenergy", "if(acmode==1, acplan[int(acsec)], 0.3 + acr1*0.7)"),
        V("acfam", f"if(acr2<0.55, acfamA, if(acr2<0.88, acfamB, int(acr3*{NF})))"),
        V("actidef", "0.7 + acr4*0.6"),
        RNG,
        V("acsecbright", "min(1, max(0.3, 0.55 + 0.45*acenergy + (acr1-0.5)*0.25))"),
    ]
    for k in range(4):
        rest += [RNG, X(f"if(acr1<0.4, acpal1, if(acr1<0.72, acpal2, if(acr1<0.9, acpal3, int(acr2*%d))))" % len(FLAVOURS),
                        lambda c, src, k=k: _flav(c, src, k))]
    rest += [
        RNG,
        X("acr1<0.85 || acsec==0 || (acmode==1 && acsec>=acnsec-1) || acdens < 0.3; acr2<0.75; acr3<0.7 || accapt; acr4<0.65",
          "v acfdrone", "v acftex", "v acfcloud", "v acfbell"),
        RNG,
        X("if(acr1<0.5, actexA, actexB); if(acr2<0.5, actexB, int(acr3*4))", "v actex1", "v actex2"),
        V("acsecdur", "if(acmode==1, (3 + 37*pow(aclen, 1.6))*60000*acpdur[int(acsec)]/acpsum, "
                      "(1 + 9*aclen)*60000*(0.7 + acr4*0.6))"),
        Arm("ac-nextsec", "acsecdur*actime", stop="ac-secstop"),
        V("acfade", "9000*actime + 500"),
        Call("ac-layers"),
        Call("ac-brightupd"),
        Call("ac-motifgen"),
        Call("ac-scr"),
        Send("ac-led"),
    ]
    proc(c, "ac-section", [If("acmode==1 && acsec>=acnsec", [Call("ac-fin")], rest)])
    proc(c, "ac-nextsec", [V("acsec", "acsec+1"), Call("ac-section")])
    # the end of a composition: fade out, then switch the layers off
    fin_off = c.obj("delay")
    proc(c, "ac-fin", [
        V("acrun", "0"),
        Send("ac-master", "0 30000"),
        Send("ac-chgstop"), Send("ac-secstop"),
        X("30500*actime + 500", (fin_off, 0)),
        Call("ac-scr"),
    ])
    c.c(fin_off, 0, c.obj("s ac-finoff"), 0)
    proc(c, "ac-finoff", [If("acrun==0", [V("acended", "1"), V("acfade", "2000"), Call("ac-layers"),
                                          Call("ac-scr"), Send("ac-led")])])
    return c


def _flav(c, src, k):
    t = c.obj("t f f")
    c.c(*src, t, 0)
    c.c(t, 1, c.obj(f"s ac-v{k}-flav"), 0)
    tw = c.obj("tabwrite acflav")
    ex = c.to(t, f"expr $f1; {k}")
    c.c(ex, 1, tw, 1)
    c.c(ex, 0, tw, 0)


def layers():
    c = Canvas("layers", w=2400)
    c.comment("Layer levels from density (knob x section energy), section flags, mutes, input mode")
    lay = [
        ("drone", "acfdrone*acmdrone*(1-acended)*(0.55+0.45*min(1, acdeff*3))"),
        ("pad", "acmpad*(1-acended)*min(1, max(0, (acdeff-0.06)/0.15))"),
        ("tex", "acftex*acmtex*(1-acended)*min(1, max(0, (acdeff-0.28)/0.15))"),
        ("cloud", "acmcloud*(1-acended)*max(acfcloud*min(1, max(0, (acdeff-0.42)/0.15)), "
                  "(acinmode==1)*min(1, acinput*2)*0.8)"),
        ("bell", "acmbell*(1-acended)*max(acfbell*min(1, max(0, (acdeff-0.5)/0.15)), (acinmode==3)*min(1, acinput*2))"),
    ]
    steps = [V("acdeff", "if(acmode==1, min(1, acenergy*(0.35+1.3*acdens)), min(1, acdens*(0.8+0.4*acenergy)))")]
    for name, e in lay:
        steps += [V("acg" + name, e)]
        if name != "tex":
            steps += [SendL("ac-g-" + name, ["acg" + name, "acfade"])]
    for i in range(4):
        steps += [V(f"acgt{i}", f"acgtex*((actex1=={i}) || (actex2=={i}))"),
                  SendL(f"ac-g-tex{i}", [f"acgt{i}", "acfade"])]
    proc(c, "ac-layers", steps)
    # density knob: follow it, at most every 150 ms
    d = c.to(c.recv("ac-densch"), "delay 150")
    run_steps(c, (d, 0), [V("acfade", "1500"), Call("ac-layers")])
    c.col()
    proc(c, "ac-brightupd", [
        V("acbright", "min(1, accolor*acsecbright*1.25)"),
        SendL("ac-bright", ["acbright", "4000"]),
        V("acgdurv", "70 + 480*(1-acbright)*(0.4+acweird)"),
        SendL("ac-gdur", ["acgdurv"]),
        SendL("ac-resfb", ["0.93 + 0.066*accolor"]),
        SendL("ac-resdamp", ["1200 + 5000*accolor"]),
    ])
    proc(c, "ac-revupd", [SendL(f"ac-rg{i}", [f"pow(10, -3*{ms}/(1000*(2.5+26*pow(acspace, 1.5))))"])
                          for i, ms in enumerate(REVERB_MS)] + [SendL("ac-rwet", ["0.1 + 0.62*acspace", "400"])])
    proc(c, "ac-inputupd", [
        SendL("ac-g-res", ["(acinmode==0)*acinput", "1500"]),
        SendL("ac-g-tape", ["(acinmode==2)*acinput", "1500"]),
        SendL("ac-g-dry", ["acinput*if(acinmode==3, 0, if(acinmode==1, 0.35, 0.6))", "300"]),
        SendL("ac-incl", ["if(accapt, 1, (acinmode==1)*min(1, acinput*3))", "500"]),
        SendL("ac-inclr", ["1 - if(accapt, 1, (acinmode==1)*min(1, acinput*3))", "500"]),
        SendL("ac-ghost", ["(acinmode==3)*acinput"]),
        V("acfade", "1500"), Call("ac-layers"),
    ])
    return c


def change():
    c = Canvas("change", w=3600)
    c.comment("A chord change: maybe modulate, move the chord root, voice-lead the 4 pad voices, retune "
              "drone, resonators, grains and wind")
    steps = [
        RNG,
        V("acchsec", "(6 + 84*pow(actide, 2)) * actidef * if(acmode==1, 1.3-0.6*acenergy, 1) * (0.75+acr3*0.5)"),
        V("acnewt", "if(acpend>=0, 36 + acpend, if(acr1 < 0.03 + acweird*0.15 && acfirst==0, "
                    "36 + ((int(actonic) - 36 + int(acmods[int(acr2*12)])) % 12 + 12) % 12, actonic))"),
        X("acnewt != actonic; acnewt; -1", "v acmodflag", "v actonic", "v acpend"),
        If("acr3 < acweird*0.12 && acfirst==0", [RNG, V("acsci", f"int(acr4*{NS})"), Call("ac-loadscale")]),
        RNG,
        V("acdeg", "if(acmodflag || acfirst, 0, if(acr1 < 0.1 + 0.15*(1-acweird) && acdeg != 0, 0, "
                   "((int(acdeg) + int(acmoves[int(acr2*12)])) % int(acn) + int(acn)) % int(acn)))"),
    ]
    for k in range(4):
        steps += [
            V("acD", f"acdeg + acfamt[int(acfam)*5+{1 + k}]"),
            V("acp0", f"if(acfamt[int(acfam)*5]==0, {deg2p('acD')} + 12, "
                      f"actonic + 12 + acscale[int(acdeg)] + acfamt[int(acfam)*5+{1 + k}])"),
            RNG,
            V("acp1", f"if(acfirst || acfamt[int(acfam)*5]==1 || acr1>0.7, acp0, "
                      f"acp0 + 12*floor((acch[{k}]-acp0)/12 + 0.5))"),
            V("acp1", "if(acp1<43, acp1+12, if(acp1>86, acp1-12, acp1))"),
            V("acp1", "if(acp1<43, acp1+12, if(acp1>86, acp1-12, acp1))"),
            T("acnew", k, "acp1"),
        ]
    for k in range(4):
        steps += [RNG,
                  SendL(f"ac-v{k}-pitch", [f"acnew[{k}]",
                                           "if(acfirst, 0, max(1500, (0.25+0.5*acr1)*acchsec*1000*actime))",
                                           "if(acfirst, 0, acr2*0.35*acchsec*1000*actime)"]),
                  T("acch", k, f"acnew[{k}]")]
        steps += [SendL(f"ac-res{k}", [f"1000/mtof(43 + fmod(acnew[{k}]-43, 24))", "2500"])]
    for i in range(4):
        steps += [RNG, SendL(f"ac-gr{i}", ["acgrt[int(acr1*12)] * if(acr2 < acweird*0.3, -1, 1)"])]
    steps += [
        SendL("ac-dronep", ["actonic", "if(acfirst, 0, if(acmodflag, 9000, 200))"]),
        RNG,
        SendL("ac-dharm", ["2 + int(acr1*5)", "6000"]),
        SendL("ac-wind", ["mtof(acnew[1]+24)", "mtof(acnew[3]+12)", "5000"]),
        X("acchg + 1; 0", "v acchg", "v acfirst"),
        Arm("ac-change", "acchsec*1000*actime", stop="ac-chgstop"),
        Call("ac-scr2"), Call("ac-scr3"), Send("ac-flash"),
    ]
    proc(c, "ac-change", [If("acrun", steps)])
    return c


def players():
    c = Canvas("players", w=2400)
    c.comment("Event players: bell motif, rain drops, creature chirps, input onsets")
    bellp = f"{deg2p('acdeg + acmotif[int(acbi)]')} + 24"
    play = [V("acbp", bellp), V("acbp", "if(acbp<67, acbp+12, if(acbp>96, acbp-12, acbp))"),
            SendL("ac-bell", ["acbp", "0.35+0.65*acr2"])]
    proc(c, "ac-btick", [
        If("acgbell > 0.01 && acrun", [
            RNG,
            If("acr1 > 0.18", play),
            V("acbi", "(acbi+1) % 5"),
            If("acbi==0 && acr3<0.6", [RNG, T("acmotif", "int(acr1*5)", "acmotif[int(acr1*5)] + int(acr2*5) - 2")]),
        ]),
        RNG,
        Arm("ac-btick", "(500 + 3500*actide) * acmrhy[int(acbi)] * (0.7+acr4*0.6) * (1.5 - 0.7*acdeff)"),
    ])
    proc(c, "ac-bellnow", [If("acmbell && acrun", [RNG] + play + [V("acbi", "(acbi+1) % 5")])])
    proc(c, "ac-rtick", [
        RNG,
        If("acgt0 > 0.01", [
            V("acdropi", "(acdropi+1) % 3"),
            SendL("ac-drop", ["acdropi", "min(100, acch[int(acr1*4)] + 24 + 12*int(acr2*2))", "acr3"]),
        ]),
        RNG,
        Arm("ac-rtick", "(90 + 2200*(1-acdeff)) * (0.15 + 1.7*acr4)"),
    ])
    proc(c, "ac-ctick", [
        If("acgt3 > 0.01", [
            If("acbc > 0", [
                RNG,
                SendL("ac-chirp", ["mtof(min(110, acch[int(acr1*4)] + 36))", "0.55+acr2*0.9", "40+acr3*130", "acr4"]),
                V("acbc", "acbc - 1"),
            ], [RNG, V("acbc", "2 + int(acr1*5)")]),
        ]),
        RNG,
        Arm("ac-ctick", "if(acbc>0, 80 + acr2*240, 1500 + acr3*9000)"),
    ])
    # ghost input mode: a played onset rings the next bell note
    proc(c, "ac-inonset", [If("acinmode==3 && acinput > 0.05", [Call("ac-bellnow"), RNG,
                                                                If("acr1 < 0.08", [Call("ac-change")])])])
    return c


def capture():
    c = Canvas("capture")
    c.comment("Capture: 8 s of the input into the cloud buffer, then freeze it there")
    proc(c, "ac-capture", [
        X("1; 0; 1", "v accapt", "v acfreeze", "v acfcloud"),
        Call("ac-freezeupd"), Call("ac-inputupd"), Send("ac-cwstart"),
        Toast("capturing 8 s"),
        Arm("ac-capdone", "8100"),
    ])
    proc(c, "ac-capdone", [X("0; 1", "v accapt", "v acfreeze"), Call("ac-freezeupd"), Call("ac-inputupd"),
                           Toast("captured - frozen")])
    return c
