"""The composer's control logic: seed, piece, form (sections), harmony (changes), event players.

Conventions: global state lives in [value]s named ac<word> (no dash, so [expr] can read them);
every [send]/[receive] name has a dash (ac-<word>), so values and sends never share a symbol."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Arm, Toast, RNG
from data import *
from data import DRONES, CHARACTERS, ATMOS_NAMES, ATMOS_ROLE, SCENES, SCENE_DATA, SCENE_ROLE, \
    FLAVOUR_WEIGHTS, FM_RATIO_WEIGHTS, PARTIAL_WEIGHTS, pick_table

NF = len(FAMILIES)
NS = len(SCALES)

GLOBALS = dict(
    acseed=1, account=0, actonic=38, acsci=0, acn=7, acfamA=0, acfamB=1, acfam=0, acdeg=0, acpend=-1,
    acmode=1, acrun=1, acended=0, acsec=0, acnsec=8, acenergy=0.5, acdeff=0.5, acsecdur=60000, acchsec=20,
    acpage=0, acinmode=0, acfreeze=0, accapt=0, acvfreeze=0,
    acmdrone=1, acmpad=1, acmtex=1, acmcloud=1, acmbell=1, acmmotion=1,
    acfdrone=1, acfpad=1, acftex=1, acfcloud=1, acfbell=1, acfmotion=0, actex1=0, actex2=1, actexA=0, actexB=1,
    acpal1=0, acpal2=1, acpal3=3, acpartI=0, acbellI=0, acsecbright=0.8, actidef=1, acpow=1,
    acpsum=1, acfirst=1, acmodflag=0, acD=0, acp0=0, acp1=0, acnewt=38, aci=0, acchg=0, acfade=8000,
    actime=1, acgdrone=0, acgpad=0, acgtex=0, acgcloud=0, acgbell=0, acgmotion=0,
    acgt0=0, acgt1=0, acgt2=0, acgt3=0,
    acbi=0, acbc=0, acdropi=0, acbright=0.5, acbp=0, acgdurv=300, acr1=0.5, acr2=0.5, acr3=0.5, acr4=0.5,
    acknown0=0, acknown1=0, acknown2=0, acknown3=0, acinprev=0, acghost=0,
    # form
    acarch=0, acpk=3, acpkv=0, acrecap=-1, achome=38, acaway1=7, acaway2=5, acrole=2, acprogn=0, acprogi=0,
    acmtr=2, acbld=1, acblp=0.5, acvauto=1, acvsec=1, acvtype=1, acrvsize=1,
    # rhythm
    acbpm0=56, acbpm=56, actpos=0.5, acmeter=4, actick=0, acstep=0, acms=0, acmk=5, acmn=8, acmei=0, acmrot=0, acmdiv=1,
    acmarp=0, acmai=0, acmoct=12, acmswing=0, acgdlock=0, acmp=60, acdtype=0, acdtype2=1, acdcur=0, acsubm=0, acchar=0, acchamt=0.5, acavoc=0, acgvoc=0, acdb=0, acgt4=0, acgt5=0, acgt6=0, acgsub=0, acatm=0, acatmT=0, acatmT2=1, acfatm=0, acatmcur=0, acgatm=0, acscene=0, acmono=0, acwidth=1, acpanmot=0.8, acfd=-1, acgbands=0, acgres=0, ackn=0, ackv=0,
)
for page in PAGES:
    for _, name, d in page:
        GLOBALS[name] = d

ARRAYS = dict(acscale=16, acfamt=NF * 5, acch=4, acnew=4, acplan=16, acpdur=16, acmotif=8, acmotif0=8,
              acmrhy=8, acmoves=12, acmods=12, acgrt=12, acfmrt=8, acpartt=24, acbellt=12, acdintt=5, acrhyt=5,
              acparams=12, acraw=4, acflav=4, acroles=16, acflpick=40, acfmrpick=40, acpapick=40, acscn=50,
              acscrole=24, acatmrole=8, ackeyp=16, acprog=8, acrmask=48, acrtide=8,
              acrtempo=8, acrpulse=8, acaway=8, aceuk=10, aceun=10, acmeters=6, acmratios=6, acbreath=4, actlo=5, acthi=5)

# the piece tempo: its place (actpos) in the tempo range chosen in SETUP
TEMPO0 = "actlo[int(actrange)] + int(actpos*(acthi[int(actrange)] - actlo[int(actrange)] + 1))"
# the beat the slow layers feel: half speed above HALFTIME
BPMH = f"(acbpm/(1 + (acbpm > {HALFTIME})))"

import gen_live as _L
import gen_oled as _O
import gen_setup as _S
for _m in (_L, _O, _S):
    GLOBALS.update(_m.GLOBALS)
    ARRAYS.update(_m.ARRAYS)

DATA_TABLES = dict(
    acflpick=pick_table(FLAVOUR_WEIGHTS), acfmrpick=pick_table(FM_RATIO_WEIGHTS), acpapick=pick_table(PARTIAL_WEIGHTS),
    acscn=sum(SCENE_DATA, []), acscrole=sum(SCENE_ROLE, []), acatmrole=ATMOS_ROLE,
    acmoves=MOVES, acmods=MODS, acgrt=GRAIN_RATIOS, acfmrt=FM_RATIOS,
    acpartt=sum(PARTIAL_SETS, []), acbellt=sum(BELL_SETS, []), acdintt=DRONE_INTERVALS, acrhyt=RHYTHMS,
    acparams=[d for p in PAGES for _, _, d in p], acraw=[0.5] * 4, aclvn=[-1] * 4, acrmask=sum(ROLE_MASK, []),
    acrtide=ROLE_TIDE, acrtempo=ROLE_TEMPO, acrpulse=ROLE_PULSE, acaway=AWAY, aceuk=[k for k, n in EUCLID],
    aceun=[n for k, n in EUCLID], acmeters=METERS, acmratios=MOTION_RATIOS, acbreath=BREATH_PERIODS,
    actlo=[lo for _, lo, _ in TEMPOS], acthi=[hi for _, _, hi in TEMPOS],
)

# the form archetypes: energy at x (0..1 through the piece)
ARCH_EXPR = ("if(acarch==0, pow(sin(3.14159*X), acpow), if(acarch==1, if(X<0.78, pow(X/0.78, 1.5), (1-X)/0.22), "
             "if(acarch==2, (0.55 - 0.45*cos(12.566*X))*(0.4 + 0.6*sin(3.14159*X)), "
             "if(acarch==3, max(exp(-pow((X-0.33)/0.13, 2)), 0.9*exp(-pow((X-0.75)/0.12, 2))), "
             "min(1, 1.3*pow(sin(3.14159*X), 0.6))))))")


def deg2p(d):
    """scale degree (may be negative) -> pitch above the tonic"""
    return (f"(actonic + 12*floor(({d})/acn) + "
            f"acscale[(int({d}) % int(acn) + int(acn)) % int(acn)])")


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
    tables = dict(acfamt=fam, **DATA_TABLES)
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
        h = c.to((ts, k), f"expr int(fmod(abs(sin(fmod($f1, 100000)*12.9898 + {k + 1}*78.233))*43758.5453, 1)*16777000) + {k + 1}")
        tw = c.to(h, "t b b b b b f")
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
    c = Canvas("piece", w=3000)
    c.comment("A new piece: tonic, scale, voicings, timbre palette, ratios, tempo and meter, reverb, form")
    steps = [
        RNG,
        V("actonic", "36 + int(acr1*12)"),
        V("acsci", "int(acr2*%d)" % NS), Call("ac-loadscale"),
        V("acfamA", f"int(acr3*{NF})"), V("acfamB", f"int(acr4*{NF})"),
        RNG,
        # the palette leans to the electronic and bell-like types (weights in data.py)
        X("acflpick[int(acr1*40)]; acflpick[int(acr2*40)]; acflpick[int(acr3*40)]", "v acpal1", "v acpal2",
          "v acpal3"),
        SendL("ac-fmr", ["acfmrt[int(acfmrpick[int(acr4*40)])]"]),
        RNG,
        X("acpapick[int(acr1*40)]; int(acr2*%d); int(acr3*%d); int(acr4*%d)" % (len(TEXTURES), len(TEXTURES),
                                                                                   len(BELL_SETS)),
          "v acpartI", "v actexA", "v actexB", "v acbellI"),
        SendL("ac-partials", ["acpartt[int(acpartI)*4+1]", "acpartt[int(acpartI)*4+2]", "acpartt[int(acpartI)*4+3]"]),
        SendL("ac-bellset", ["acbellt[int(acbellI)*3]", "acbellt[int(acbellI)*3+1]", "acbellt[int(acbellI)*3+2]"]),
        RNG,
        SendL("ac-dint", ["acdintt[int(acr1*5)]"]),
        SendL("ac-lvtype", ["acpal1"]),
        # the piece's drone design (and one for its break), sub mode, character on the pads, auto-vocode
        RNG,
        X(f"int(acr1*{len(DRONES)}); int(acr2*{len(DRONES)}); int(acr3*3); if(acr4 < 0.22, 0, 1 + int(acr4*4.99) % 4)",
          "v acdtype", "v acdtype2", "v acsubm", "v acchar"),
        RNG,
        X("0.35 + acr1*0.45; acr2 < 0.5", "v acchamt", "v acavoc"),
        RNG,
        X(f"acr1 < 0.55; int(acr2*{len(ATMOS_NAMES)}); int(acr3*{len(ATMOS_NAMES)})", "v acatm", "v acatmT", "v acatmT2"),
        # tempo, meter, motion timbre
        X("acr2; acmeters[int(acr3*6)]", "v actpos", "v acmeter"),
        V("acbpm0", TEMPO0),
        SendL("ac-mtimbre", ["acmratios[int(acr4*6)]"]),
        RNG,
        SendL("ac-mtimbre2", ["1 + acr1*4", "250 + acr2*700"]),
        # the reverb this piece likes (Auto): Bloom 1, Bloom 2, Hall, Shimmer
        X("if(acr3<0.42, 1, if(acr3<0.74, 2, if(acr3<0.9, 3, 4))); 0.8 + acr4*0.45", "v acvauto", "v acrvsize"),
        SendL("ac-rvsize", ["acrvsize"]),
        # key areas away from home
        RNG,
        X("actonic; acaway[int(acr1*8)]; acaway[int(acr2*8)]", "v achome", "v acaway1", "v acaway2"),
    ]
    for k in range(4):
        # pad breathing: cycles of 7, 9, 11, 13 half-bars, so the voices phase against each other
        steps += [RNG, SendL(f"ac-v{k}-lfo", [f"1/(30/(acbpm0/(1 + (acbpm0 > {HALFTIME})))*acmeter*acbreath[{k}]*(0.97+acr1*0.06))",
                                              "0.03+acr2*0.15", "0.04+acr3*0.25", "0.03+acr4*0.2"])]
    steps += [
        X("0; -1; 0; 1; 0; 0; 1; 0; 0", "v acdeg", "v acpend", "v acchg", "v acfirst", "v acended", "v accapt",
          "v acrun", "v acsec", "v acprogn"),
        Send("ac-master", "1 3000"),
        V("acel", "0"), Call("ac-clockstop"),
        Call("ac-motif0"),
        Call("ac-plan"),
        Call("ac-section"),
        Call("ac-change"),
        Call("ac-brightupd"), Call("ac-inputupd"),
        SendL("ac-weird", ["acweird"]), SendL("ac-motion", ["acmotion"]),
        V("actick", "-1"), Call("ac-clockstart"),
        Call("ac-scr"), Send("ac-oledall"),
    ]
    proc(c, "ac-newpiece", steps)
    # the form: an archetype's energy curve over 6-12 sections, then a role for each section
    arch = ARCH_EXPR.replace("X", "((aci+0.5)/acnsec)")
    proc(c, "ac-plan", [
        RNG,
        X("min(12, max(6, int((5 + 25*aclen)/2.6 + acr1*2))); int(acr2*%d); 0.6 + acr3*0.9; 0; 0; 1"
          % len(ARCHETYPES), "v acnsec", "v acarch", "v acpow", "v acpsum", "v acpkv", "v acpk"),
        Loop("acnsec", "aci", [
            RNG,
            T("acplan", "aci", f"if(aci==0, 0.1+acr2*0.1, if(aci==acnsec-1, 0.2, min(1, max(0.12, 0.12 + 0.85*{arch}"
                               " + (acr1-0.5)*0.16))))"),
            T("acpdur", "aci", "0.7 + acr3*0.6"),
            V("acpsum", "acpsum + acpdur[int(aci)]"),
            If("acplan[int(aci)] > acpkv && aci > 1 && aci < acnsec-1", [V("acpkv", "acplan[int(aci)]"),
                                                                       V("acpk", "aci")]),
        ]),
        V("acrecap", "if(max(acpk+1, int(acnsec*0.72)) <= acnsec-2, max(acpk+1, int(acnsec*0.72)), -1)"),
        Loop("acnsec", "aci", [
            RNG,
            T("acroles", "aci", "if(aci==0, 0, if(aci==acnsec-1, 7, if(aci==acpk, 4, if(aci==acrecap, 6, "
                                "if(aci==1, 1, if(aci>acpk, if(acplan[int(aci)] < acplan[int(aci)-1]-0.15, 5, 2), "
                                "if(acplan[int(aci)] > acplan[int(aci)-1], 3, 2)))))))"),
            T("ackeyp", "aci", "if(acroles[int(aci)]<=1 || acroles[int(aci)]>=6, 0, if(acroles[int(aci)]==4, "
                               "if(acr1<0.5, acaway2, acaway1), if(acroles[int(aci)]==5, if(acr2<0.5, acaway2, 0), "
                               "if(acroles[int(aci)]==2, if(acr3<0.6, acaway1, 0), acaway1))))"),
        ]),
    ])
    # the piece's motif (5 scale degrees, a random walk) and its rhythm
    proc(c, "ac-motif0", [Loop("5", "aci", [
        RNG,
        T("acmotif0", "aci", "if(aci==0, int(acr1*3)*2, acmotif0[int(aci)-1] + int(acr1*5) - 2)"),
        T("acmotif", "aci", "acmotif0[int(aci)]"),
        T("acmrhy", "aci", "acrhyt[int(acr2*5)]"),
    ])])
    # each section transforms it by role: inverted (develop), raised and faster (intensify, climax),
    # as it was (establish, return), varied otherwise
    proc(c, "ac-motifgen", [
        RNG, V("acmtr", "2 + 2*int(acr1*2)"),
        Loop("5", "aci", [
            RNG,
            T("acmotif", "aci", "if(acrole==2 && acr1<0.5, -acmotif0[int(aci)], if(acrole==3 || acrole==4, "
                                "acmotif0[int(aci)] + acmtr, if(acrole==6 || acrole<=1, acmotif0[int(aci)], "
                                "acmotif0[int(aci)] + int(acr1*3) - 1)))"),
            T("acmrhy", "aci", "acrhyt[int(acr2*5)] * if(acrole==3 || acrole==4, 0.5, 1)"),
        ]),
    ])
    return c


def section():
    c = Canvas("section", w=3600)
    c.comment("A section: its role (from the plan, or chosen when drifting) sets layers, key, tempo, "
              "harmonic pace, motif, rhythm and reverb")
    rest = [
        RNG,
        V("acrole", "if(acmode==1, acroles[int(acsec)], if(acr1<0.25, 1, if(acr1<0.55, 2, "
                    "if(acr1<0.8, 3, 5))))"),
        V("acenergy", "if(acmode==1, acplan[int(acsec)], 0.3 + acr2*0.7)"),
        V("acfam", f"if(acrole==6, acfamA, if(acr3<0.55, acfamA, if(acr3<0.88, acfamB, int(acr4*{NF}))))"),
        RNG,
        V("actidef", "acrtide[int(acrole)] * (0.85 + acr1*0.3)"),
        V("acdcur", "if(acrole == 5 && acr2 < 0.6, acdtype2, acdtype)"),
        V("acsecbright", "min(1, max(0.3, 0.55 + 0.45*acenergy + (acr2-0.5)*0.25))"),
    ]
    for k in range(4):
        rest += [RNG, X(f"if(acr1<0.4, acpal1, if(acr1<0.72, acpal2, if(acr1<0.9, acpal3, int(acr2*{len(FLAVOURS)}))))",
                        lambda c, src, k=k: _flav(c, src, k))]
    for i, lay in enumerate(LAYERS):
        extra = {"drone": " || acdens < 0.3", "cloud": " || accapt"}.get(lay, "")
        rest += [RNG, V("acf" + lay, f"acr1 < acrmask[int(acrole)*6+{i}]{extra}")]
    rest += [
        RNG,
        X("if(acr1<0.5, actexA, actexB); if(acr2<0.5, actexB, int(acr3*%d))" % len(TEXTURES), "v actex1", "v actex2"),
        # rhythm of the motion layer: a Euclidean pattern, its rotation, 16ths or 8ths, arpeggio shape
        RNG,
        X("int(acr1*10); int(acr2*8); 1 + (acr3<0.35); int(acr4*4)", "v acmei", "v acmrot", "v acmdiv", "v acmarp"),
        V("acmdiv", f"acmdiv * (1 + (acbpm0 > {HALFTIME}))"),
        X("aceuk[int(acmei)]; aceun[int(acmei)]", "v acmk", "v acmn"),
        RNG,
        X("12*(1 + int(acr1*2)); (0.08 + acr2*0.25)*acrhythm; (acrole==3 || acrole==4) && acr3 < 0.6",
          "v acmoct", "v acmswing", "v acgdlock"),
        # key plan: move to this section's key area at the next chord change
        If("acmode==1", [V("acpend", "if(((int(actonic)-36) % 12) != ((int(achome)-36 + int(ackeyp[int(acsec)])) "
                                     "% 12 + 12) % 12, ((int(achome)-36 + int(ackeyp[int(acsec)])) % 12 + 12) % 12, "
                                     "acpend)")]),
        V("acprogi", "0"),
        # tempo and the drone's pulse on the bar
        Call("ac-settempo"),
        SendL("ac-pulse", ["acrpulse[int(acrole)] * (0.3 + 1.4*acrhythm)"]),
        # the stereo scene: where the pads live, where bells and motion play, how far the cloud spreads
        RNG,
        V("acscene", "acscrole[int(acrole)*3 + int(acr1*3)]"),
    ] + [SendL(f"ac-v{k}-home", [f"acscn[int(acscene)*10 + {k}]", "6000"]) for k in range(4)] + [
        SendL("ac-cloudspread", ["acscn[int(acscene)*10 + 8]*0.5"]),
        Call("ac-stereo"),
        # an atmosphere in some sections of pieces that have one (the break may use the second kind)
        RNG,
        X("acatm && acr1 < acatmrole[int(acrole)]; if(acrole == 5 && acr2 < 0.5, acatmT2, acatmT)", "v acfatm",
          "v acatmcur"),
        # reverb: Auto takes the piece's own, and sometimes Shimmer at the climax
        RNG,
        V("acvsec", "if(acrole==4 && acr1 < 0.4, 4, acvauto)"),
        Call("ac-verbsel"),
        Send("ac-rvin", "1.8 1500"), Arm("ac-rvback", "3500"),
        V("acsecel", "0"),
        V("acsecdur", "if(acmode==1, (5 + 25*aclen)*60000*acpdur[int(acsec)]/acpsum, "
                      "(1.5 + 6*aclen)*60000*(0.7 + acr4*0.6))"),
        Arm("ac-nextsec", "acsecdur*actime", stop="ac-secstop"),
        V("acfade", "9000*actime + 500"),
        SendL("ac-master", ["0.62 + 0.38*acenergy", "acfade"]),
        Call("ac-layers"),
        Call("ac-brightupd"),
        Call("ac-motifgen"),
        Call("ac-memsec"),
        Call("ac-scr"),
        Send("ac-led"),
    ]
    proc(c, "ac-section", [If("acmode==1 && acsec>=acnsec", [Call("ac-fin")], rest)])
    # while you play (breath, or notes held), a section waits for you, up to 3 times 30 s
    proc(c, "ac-nextsec", [If("acmode==1 && acsechold < 3 && (acnow - acbreatht < 4000 || acheld > 0)", [
        V("acsechold", "acsechold + 1"), Arm("ac-nextsec", "30000*actime"), Toast("holding - you are playing")],
        [V("acsechold", "0"), V("acsec", "acsec+1"), Call("ac-section")])])
    proc(c, "ac-rvback", [Send("ac-rvin", "1 5000")])
    # the end of a composition: fade out, then switch the layers off
    fin_off = c.obj("delay")
    proc(c, "ac-fin", [
        V("acrun", "0"),
        Send("ac-master", "0 30000"),
        Send("ac-chgstop"), Send("ac-secstop"), Call("ac-clockstop"),
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
    c = Canvas("layers", w=2600)
    c.comment("Layer levels from density (knob x section energy), the section's layers, mutes, input mode")
    th = lambda t: f"min(1, max(0, (acdeff-{t})/0.15))"
    lay = [
        ("drone", "acfdrone*acmdrone*(1-acended)*(0.55+0.45*min(1, acdeff*3))"),
        ("pad", f"acfpad*acmpad*(1-acended)*{th(0.06)}"),
        ("tex", f"acftex*acmtex*(1-acended)*{th(0.28)}"),
        ("cloud", f"acmcloud*(1-acended)*max(acfcloud*{th(0.42)}, ((acinmode==2) || (acinmode==0)*(acinclass>=1))"
                  f"*min(1, acinput*2)*0.8)"),
        ("bell", f"acmbell*(1-acended)*max(acfbell*{th(0.45)}, (acinmode==4)*min(1, acinput*2))"),
        ("motion", f"acfmotion*acmmotion*(1-acended)*{th(0.3)}*min(1, acrhythm*2.5)"),
    ]
    steps = [V("acdeff", "min(1, if(acmode==1, acenergy*(0.35+1.3*acdens), acdens*(0.8+0.4*acenergy)) + 0.35*acbreath)")]
    for name, e in lay:
        steps += [V("acg" + name, e)]
        if name == "drone":
            steps += [SendL("ac-g-drone", ["acgdrone*(acdcur==0)", "acfade"])]
            steps += [SendL(f"ac-g-drone{i}", [f"acgdrone*(acdcur=={i})", "acfade"]) for i in range(1, len(DRONES))]
            steps += [V("acgsub", "acgdrone*acmdrone*(1-acended)"), SendL("ac-g-sub", ["acgsub", "acfade"])]
        elif name != "tex":
            steps += [SendL("ac-g-" + name, ["acg" + name, "acfade"])]
    steps += [V("acgatm", "acfatm*acmtex*(1-acended)*(0.55 + 0.45*min(1, acdeff*2))")]
    steps += [SendL(f"ac-g-atm{i}", [f"acgatm*(acatmcur=={i})", "acfade*1.5"]) for i in range(len(ATMOS_NAMES))]
    steps += [SendL(f"ac-g-ch{i}", [f"(acchar=={i})*min(1, acchamt*if(acrole==4, 1.3, 1))*min(1, acgpad*4)", "acfade"])
              for i in range(1, len(CHARACTERS))]
    steps += [SendL("ac-chdry", ["1 - (acchar==2)*0.9*acchamt - (acchar==4)*0.6*acchamt", "acfade"])]
    for i in range(len(TEXTURES)):
        steps += [V(f"acgt{i}", f"acgtex*((actex1=={i}) || (actex2=={i}))"),
                  SendL(f"ac-g-tex{i}", [f"acgt{i}", "acfade"])]
    proc(c, "ac-layers", steps)
    d = c.to(c.recv("ac-densch"), "delay 150")
    run_steps(c, (d, 0), [V("acfade", "1500"), Call("ac-layers")])
    c.col()
    proc(c, "ac-brightupd", [
        V("acbright", "min(1, accolor*acsecbright*1.25)"),
        SendL("ac-bright", ["acbright", "4000"]),
        # grains: free, or locked to the beat (rhythmic grain streams in intense sections)
        V("acgdurv", "if(acgdlock, 60000/acbpm/(2 + 2*(acrhythm>0.6)), 70 + 480*(1-acbright)*(0.4+acweird))"),
        SendL("ac-gdur", ["acgdurv"]),
        SendL("ac-resfb", ["0.93 + 0.066*accolor"]),
        SendL("ac-resdamp", ["1200 + 5000*accolor"]),
    ])
    A = "(acinmode==0)"
    proc(c, "ac-inputupd", [
        V("acgres", f"acinput * if(acinmode==1, 1, {A}*if(acinclass==1, if(acavoc, 0.3, 0.8), if(acinclass==2, 0.4, 0)))"),
        V("acgvoc", f"acinput * ((acinmode==6) || (acinmode==7) || {A}*(acinclass==1)*acavoc)"),
        SendL("ac-g-voc", ["acgvoc", "1500"]),
        SendL("ac-vcsyn", [f"(acinmode==6) || {A}", "800"]),
        SendL("ac-vcpad", ["acinmode==7", "800"]),
        V("acgbands", f"acinput * ((acinmode==5) || {A}*(acinclass==3))"),
        V("acharm", f"((acinmode==2) || {A}) && acinclass==1 && acinput > 0.05"),
        V("acgdry", "acinput * if(acinmode==4 || acinmode >= 6, 0.15*(acinmode >= 6), if(acinmode==2 || acinmode==5, 0.3, "
                    f"if({A} && acinclass==3, 0.3, 0.6)))"),
        SendL("ac-g-res", ["acgres", "1500"]),
        SendL("ac-g-bands", ["acgbands", "1500"]),
        SendL("ac-g-tape", ["(acinmode==3)*acinput", "1500"]),
        SendL("ac-g-dry", ["acgdry", "300"]),
        SendL("ac-incl", [f"if(accapt, 1, ((acinmode==2) || {A}*(acinclass>=1))*min(1, acinput*3))", "500"]),
        SendL("ac-inclr", [f"1 - if(accapt, 1, ((acinmode==2) || {A}*(acinclass>=1))*min(1, acinput*3))", "500"]),
        SendL("ac-ghost", ["(acinmode==4)*acinput"]),
        V("acfade", "1500"), Call("ac-layers"), Call("ac-grains"),
    ])
    return c


ROLE_WIDTH = [0.95, 1.05, 1.1, 1.15, 1.25, 1.2, 1.05, 1.1]


def stereo():
    c = Canvas("stereo")
    c.comment("Width (mid/side at the master) by section role x SETUP Width, 0 in mono; pad orbit depth")
    proc(c, "ac-stereo", [
        SendL("ac-width", [f"(1 - acmono) * acwidth * if(acrole==0, {ROLE_WIDTH[0]}, " +
                           "".join(f"if(acrole=={i}, {w}, " for i, w in enumerate(ROLE_WIDTH[1:], 1)) + "1"
                           + ")" * 8, "3000"]),
        SendL("ac-pandepth", ["acpanmot * 0.5 * (0.5 + acmotion) * acscn[int(acscene)*10 + 9]"]),
    ])
    return c


def verb():
    c = Canvas("verb-ctl", w=2400)
    c.comment("Reverb choice and settings. Verb knob: Auto, Bloom 1, Bloom 2, Hall, Shimmer. Time 1.5-30 s.")
    tsec = "((1.5 + 28.5*pow(acrvtime, 1.5)) * if(acrole==4, 1.5, if(acrole==7, 1.4, 1)))"
    proc(c, "ac-verbsel", [
        V("acvtype", "if(acrvtype < 0.2, acvsec, 1 + min(3, int((acrvtype-0.2)/0.2)))"),
        SendL("ac-g-rvb", ["acvtype==1 || acvtype==2", "2500"]),
        SendL("ac-g-rvh", ["acvtype>=3", "2500"]),
        SendL("ac-bltype", ["acvtype==2"]),
        SendL("ac-shim", ["(acvtype==4)*0.3", "3000"]),
        Call("ac-revupd"),
    ])
    proc(c, "ac-revupd", [
        # Bloom: loop gain exp(-4.2*size/T), as Conduit's; damping = the loop low-pass pole (0.5 = the unit)
        V("acbld", f"if(acvfreeze, 1/0.75, exp(-4.2*acrvsize/{tsec})/0.75)"),
        V("acblp", "if(acvfreeze, 0.2, min(0.9, 0.05 + 0.9*(1-acrvtone)*if(acrole==7, 1.15, 1)))"),
        SendL("ac-blk1", ["0.5*acbld*(1-acblp)"]), SendL("ac-blpole", ["acblp"]),
        SendL("ac-blsize", ["acrvsize"]), SendL("ac-blpre", ["if(acvtype==2, 85.33, 0)"]),
    ] + [SendL(f"ac-rg{i}", [f"if(acvfreeze, 1, pow(10, -3*{ms}*acrvsize/(1000*{tsec})))"])
         for i, ms in enumerate(HALL_MS)] + [
        SendL("ac-hdamp", ["1500 + 9000*pow(acrvtone, 1.5)*if(acrole==7, 0.7, 1)"]),
        SendL("ac-rwet", ["0.06 + 0.9*acrvmix", "400"]),
        SendL("ac-rvfz", ["1 - acvfreeze", "300"]),
    ])
    return c


def rhythm():
    c = Canvas("rhythm", w=3000)
    c.comment("Clock at 24 ticks a beat (MIDI clock rate): steps (16ths), beats, bars. "
              "The motion layer plays a Euclidean pattern over the chord.")
    met = c.obj("metro 40")
    c.c(c.to(c.recv("ac-init"), "delay 50"), 0, met, 0)
    c.c(c.to(c.recv("ac-bpm"), "expr 60000/max(20, $f1)/24"), 0, met, 1)
    c.c(met, 0, c.obj("s ac-mtick"), 0)
    proc(c, "ac-mtick", [If("acsync == 0", [Send("ac-tick")])])
    # the tempo of this section: the piece's place in the tempo range, x the role's tempo
    proc(c, "ac-settempo", [V("acbpm0", TEMPO0), V("acbpm", "acbpm0 * acrtempo[int(acrole)]"), SendL("ac-bpm", ["acbpm"])])
    c.col()
    proc(c, "ac-tick", [
        V("actick", "(actick + 1) % (24*acmeter*64)"),
        If("actick % 6 == 0", [
            V("acstep", "int(actick/6)"), Call("ac-step"),
            If("actick % 24 == 0", [Call("ac-beat"), If("actick % (24*acmeter) == 0", [Call("ac-bar")])]),
        ]),
    ])
    proc(c, "ac-bar", [SendL("ac-dpulse", [f"60000/{BPMH}*acmeter"]), If("acgdlock && acgcloud > 0", [Send("ac-cloud-on")])])
    proc(c, "ac-step", [If("acgmotion > 0.01 && acrun && int(acstep) % int(acmdiv) == 0", [
        V("acms", "int(acstep/acmdiv)"),
        If("((int(acms + acmrot) % int(acmn)) * int(acmk)) % int(acmn) < acmk", [
            RNG,
            V("acmai", "((int(if(acmarp==0, acmai+1, if(acmarp==1, acmai-1, if(acmarp==2, acr1*4, "
                       "acmai + if(acr1<0.5, 1, -1))))) % 4) + 4) % 4"),
            V("acmp", "acnew[int(acmai)] + acmoct"),
            SendL("ac-mnote", ["if(acmp>100, acmp-12, acmp)",
                               "if(int(acms) % int(acmn) == 0, 1, 0.5 + acr2*0.3)",
                               "(int(acms) % 2 == 1)*acmswing*15000/acbpm*acmdiv + acr3*14*acrhythm",
                               "min(0.97, max(0.03, acscn[int(acscene)*10 + 6] + acscn[int(acscene)*10 + 7]*(acmai/3 - 0.5)"
                               " + (acr4 - 0.5)*0.12))"]),
        ]),
    ])])
    return c


def change():
    c = Canvas("change", w=3600)
    c.comment("A chord change: maybe modulate (key plan or by chance), move the chord root (or replay the "
              "opening progression in a return section), voice-lead the 4 pad voices, retune everything")
    steps = [
        RNG,
        V("acchsec", "(6 + 84*pow(actide, 2)) * actidef * (0.75+acr3*0.5)"),
        V("acnewt", "if(acpend>=0, 36 + acpend, if(acmode==0 && acr1 < 0.03 + acweird*0.15 && acfirst==0, "
                    "36 + ((int(actonic) - 36 + int(acmods[int(acr2*12)])) % 12 + 12) % 12, actonic))"),
        X("acnewt != actonic; acnewt; -1", "v acmodflag", "v actonic", "v acpend"),
        If("acr3 < acweird*0.12 && acfirst==0", [RNG, V("acsci", f"int(acr4*{NS})"), Call("ac-loadscale")]),
        RNG,
        V("acdeg", "if(acmodflag || acfirst, 0, if(acrole==6 && acprogi < acprogn, acprog[int(acprogi)], "
                   "if(acr1 < 0.1 + 0.15*(1-acweird) && acdeg != 0, 0, "
                   "((int(acdeg) + int(acmoves[int(acr2*12)])) % int(acn) + int(acn)) % int(acn))))"),
        V("acprogi", "acprogi + (acrole==6)"),
        # listening: what you hold (or sing) pulls the chord - pick a root whose triad contains it
        If("acfocus >= 0 && acr3 < acfollow && acfirst == 0 && acmodflag == 0", [
            V("acfd", "-1"),
            Loop("acn", "aci", [If("abs(fmod(actonic + acscale[int(aci)] - acfocus + 1200, 12)) < 0.6 || "
                                   "abs(fmod(actonic + acscale[int(aci)] - acfocus + 1200, 12)) > 11.4",
                                   [V("acfd", "aci")])]),
            If("acfd >= 0", [RNG, V("acdeg", "((int(acfd) - 2*int(acr1*3)) % int(acn) + int(acn)) % int(acn)")]),
        ]),
        # remember the opening progression (for the return)
        If("acmode==1 && acsec <= 1 && acprogn < 8", [T("acprog", "acprogn", "acdeg"), V("acprogn", "acprogn+1")]),
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
    steps += [Call("ac-grains")]
    steps += [SendL(f"ac-band{k}", [f"mtof(min(120, acnew[{k % 4}] + {12 * (k // 4) + 12}))", "3000"]) for k in range(8)]
    steps += [
        SendL("ac-dronep", ["actonic", "if(acfirst, 0, if(acmodflag, 9000, 200))"]),
        SendL("ac-subp", ["mtof(if(acsubm==0 || (acsubm==2 && int(acsec) % 2 == 0), actonic - 12, "
                          "acnew[0] - 12*ceil((acnew[0] - 42)/12)))", "if(acfirst, 0, if(acmodflag, 9000, 1800))"]),
        SendL("ac-ringf", ["mtof(acnew[1] + 12)", "3000"]),
        SendL("ac-radio", ["mtof(min(115, acnew[2] + 36))", "4000"]),
    ] + [SendL(f"ac-atmf{k}", [f"mtof(min(112, acnew[{k % 4}] + {24 + 12 * (k // 4)}))", "6000"]) for k in range(6)] + [
        SendL("ac-atmc0", ["1000/mtof(40 + fmod(acnew[0] - 40, 12))", "5000"]),
        SendL("ac-atmc1", ["1000/mtof(40 + fmod(acnew[0] - 40 + 7, 12))", "5000"]),
    ] + [SendL(f"ac-atmn{k}", [f"mtof(min(119, acnew[{k % 4}] + {48 + 12 * (k % 2)}))", "3000"]) for k in range(6)] + [
    ] + [SendL(f"ac-voccar{k}", [f"mtof(acnew[{k}])", "600"]) for k in range(4)] + [
        RNG,
        SendL("ac-dharm", ["2 + int(acr1*5)", "6000"]),
        SendL("ac-wind", ["mtof(acnew[1]+24)", "mtof(acnew[3]+12)", "5000"]),
        X("acchg + 1; 0", "v acchg", "v acfirst"),
        Arm("ac-change", "acchsec*1000*actime", stop="ac-chgstop"),
        Call("ac-scr2"), Call("ac-scr3"), Send("ac-flash"), Call("ac-outchord"),
    ]
    proc(c, "ac-change", [If("acrun", steps)])
    gs = []
    for i in range(4):
        gs += [RNG, SendL(f"ac-gr{i}", [f"if(acharm && acinp > 0, pow(2, (acnew[{i}] + 12*floor((acinp - acnew[{i}])/12 + 0.5)"
                                        f" - acinp)/12), acgrt[int(acr1*12)] * if(acr2 < acweird*0.3, -1, 1))"])]
    proc(c, "ac-grains", gs)
    return c


def players():
    c = Canvas("players", w=2400)
    c.comment("Event players: bell motif, rain drops, creature chirps, input onsets")
    bellp = f"{deg2p('acdeg + acmotif[int(acbi)]')} + 24"
    play = [V("acbp", bellp), V("acbp", "if(acbp<67, acbp+12, if(acbp>96, acbp-12, acbp))"),
            SendL("ac-bell", ["acbp", "0.35+0.65*acr2", "min(0.97, max(0.03, acscn[int(acscene)*10 + 4] + "
                                                     "acscn[int(acscene)*10 + 5]*(acr3 - 0.5)))"])]
    proc(c, "ac-btick", [
        If("acgbell > 0.01 && acrun", [
            RNG,
            If("acr1 > 0.18", play),
            V("acbi", "(acbi+1) % 5"),
            If("acbi==0 && acr3<0.6", [RNG, T("acmotif", "int(acr1*5)", "acmotif[int(acr1*5)] + int(acr2*5) - 2")]),
        ]),
        RNG,
        Arm("ac-btick", f"(60000/{BPMH}) * acmrhy[int(acbi)] * (1 + int(acr4*3)) * (1.6 - 0.7*acdeff) * (0.9 + acr1*0.2)"),
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
    # data texture: bursts of blips on chord tones
    proc(c, "ac-ttick", [RNG, If("acgatm > 0.01 && acatmcur == 1 && acr1 < 0.4", [Send("ac-thunder")]),
                         Arm("ac-ttick", "9000 + acr2*20000")])
    proc(c, "ac-dtick", [
        If("acgt5 > 0.01", [If("acdb > 0", [
            RNG, SendL("ac-data", ["min(110, acnew[int(acr1*4)] + 36 + 12*int(acr2*2))", "25 + acr3*50"]),
            V("acdb", "acdb - 1")], [RNG, V("acdb", "4 + int(acr1*10)")])]),
        RNG,
        Arm("ac-dtick", "if(acdb > 0, 45 + acr2*80, 1200 + acr3*6000)"),
    ])
    # input onsets: counted for the class; in ghost mode (and for plucked sounds in auto) they ring a bell
    proc(c, "ac-inonset", [Call("ac-inonset2"),
                           If("(acinmode==4 || (acinmode==0 && acinclass==2)) && acinput > 0.05",
                              [Call("ac-bellnow"), RNG, If("acr1 < 0.08 && acinmode==4", [Call("ac-change")])])])
    return c


def capture():
    c = Canvas("capture")
    c.comment("Capture: 8 s of the input into the cloud buffer, then freeze it there")
    proc(c, "ac-capture", [
        X("1; 0; 1", "v accapt", "v acfreeze", "v acfcloud"),
        Call("ac-freezeupd"), Call("ac-inputupd"), Send("ac-cwstart"), Call("ac-memrec"),
        Toast("capturing 8 s"),
        Arm("ac-capdone", "8100"),
    ])
    proc(c, "ac-capdone", [X("0; 1", "v accapt", "v acfreeze"), Call("ac-freezeupd"), Call("ac-inputupd"),
                           Toast("captured - frozen")])
    return c
