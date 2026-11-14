"""Performing: the morph engine (knob values gliding to a target, your hand taking any of them back), ANCHOR (a
place to come back to), MORPH on load, COMPARE (the slot as saved), the changed check, the four macros, SINK,
SWELL, DUCK, PUMP, the JOURNEY of the layers through their engines, and CC OUT.

Ideas from Frasil (Styves Goupil, MPL-2.0): ANCHOR, MORPH, COMPARE, SINK / BLUR / SWELL, PUMP, the drone's
layers; and from TrimFX: the macros (one control moving two settings, offset or latch), ducking under the player.
Nothing of their code is used here."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, Toast, Later
from data import NK, DRONES, STRIKES, FLAVOURS
import gen_setup as S

IN = S.IN_IDX                    # (In always stays where it is)
VERB = S.KNOBS.index("acrvtype")  # (a choice: switches at the start of a glide)
L8 = ["acmdrone", "acmsub", "acmpad", "acmbell", "acmmotion", "acmtex", "acmatm", "acmcloud"]

GLOBALS = dict(acmph=0, acmt0=0, acmdur=0, acmtt=0, acmorphing=0, acancs=0, acbases=0, acchanged=0, acchd=0,
               acmk=0, acmdd=0, acplay=0, acdgt=1, acdgl=1, acpb=0, acjk=0, acjnext=0, acjall=0, acjdi=-1, acjbi=-1,
               acjmi=-1, acjt=0, acjpadw=0, acjon=0, acccnext=0, acccv=0, acchk=0, acslotcur=-1)
ARRAYS = dict(acmfrom=NK, acmto=NK, acmtouch=NK, acanc=NK, acbase=NK, accur=NK, acancm=8, acbasem=8, accurm=8,
              acmtk=len(S.MTARGETS), acjpi=4, acjpt=12 * len(S.JPAD_SETS), acjpn=len(S.JPAD_SETS), acccl=16)
DATA_TABLES = dict(acmtk=[-1] + S.MT_KNOBS,
                   acjpt=sum([[FLAVOURS.index(n) for n in names] + [0] * (12 - len(names)) for _, names in S.JPAD_SETS], []),
                   acjpn=[max(1, len(names)) for _, names in S.JPAD_SETS],
                   acccl=[-1] * 16)

MORPH_MS = S._pick("acmorph", S.SMORPH)
ANCG_MS = S._pick("acancg", S.SANCG)
DUCKR_MS = S._pick("acduckr", S.SDUCKR)
JOUR_MS = S._pick("acjour", S.SJOUR)
CCRATE_MS = S._pick("acccrate", S.SCCRATE)
CCBASE = S._pick("acccbase", list(enumerate(S.SCCBASE)))


def layers_from(arr):
    """the layer keys' states (off / auto / on) from an array, faded in"""
    return [V(n, f"{arr}[{j}]") for j, n in enumerate(L8)] + [V("acfade", "3000"), Call("ac-layers")]


def apply_cut(arr):
    """every knob (but In) to an array's values at once, as no hand"""
    return [V("acmph", "0"), V("acmorphing", "1"),
            Loop(str(NK), "aci", [If(f"aci != {IN}", [T("acparams", "aci", f"{arr}[int(aci)]"),
                                                      SendL("ac-param", ["aci", "acparams[int(aci)]"])])]),
            V("acmorphing", "0")]


def sink():
    """SINK's filter (both sides): a gently resonant low-pass whose cutoff glides (ac-sink, Hz); on only while
    SINK is up"""
    from gen_dsp import switched
    s, ln = switched("sink", "ac-g-sink")
    s.comment("Sink: everything under a gently resonant low-pass, 12 kHz down to 120 Hz")
    cf = s.ch(s.m(s.recv("ac-sink"), "$1 150"), "line~")
    for j in (0, 1):
        i = s.obj("inlet~", 20 + 200 * j, 5)
        v = s.obj("vcf~ 1.3")
        s.c(i, 0, v, 0)
        s.c(cf, 0, v, 1)
        s.c((v, 1), 0, s.obj("outlet~", 20 + 200 * j, 300), 0)
    return s


def perform():
    c = Canvas("perform", w=3600)
    c.comment("Morph, ANCHOR, COMPARE, macros, SINK / SWELL / DUCK, PUMP, JOURNEY, CC OUT")
    # ---- the morph engine: from where the knobs are (acmfrom) to acmto over acmdur ms, a step each 100 ms (from
    #      ac-now); a knob your hand turns meanwhile leaves the glide (acmtouch)
    proc(c, "ac-morphgo", [Loop(str(NK), "aci", [T("acmfrom", "aci", "acparams[int(aci)]"), T("acmtouch", "aci", "0")]),
                           X("acnow; 1", "v acmt0", "v acmph"), Call("ac-morphstep")])
    proc(c, "ac-morphstep", [
        V("acmtt", "if(acmdur <= 0, 1, min(1, (acnow - acmt0)/acmdur))"), V("acmorphing", "1"),
        Loop(str(NK), "aci", [If(f"acmtouch[int(aci)] == 0 && aci != {IN} && acmto[int(aci)] != acparams[int(aci)]", [
            T("acparams", "aci", "acmfrom[int(aci)] + (acmto[int(aci)] - acmfrom[int(aci)])*acmtt"),
            SendL("ac-param", ["aci", "acparams[int(aci)]"])])]),
        V("acmorphing", "0"),
        If("acmtt >= 1", [V("acmph", "0")]),
    ])
    # a choice among the knobs (the reverb type) switches at the start
    verb_cut = lambda arr: [If(f"{arr}[{VERB}] != acparams[{VERB}]", [
        T("acparams", VERB, f"{arr}[{VERB}]"), V("acmorphing", "1"),
        SendL("ac-param", [str(VERB), f"acparams[{VERB}]"]), V("acmorphing", "0")])]
    proc(c, "ac-verbcut", verb_cut("acmto"))
    # ---- ANCHOR (aux + top A): set, then glide back over Anchor glide; held: anchored here anew
    proc(c, "ac-anchorset", [Loop(str(NK), "aci", [T("acanc", "aci", "acparams[int(aci)]")])]
         + [T("acancm", j, n) for j, n in enumerate(L8)]
         + [V("acancs", "1"), Toast("anchor set"), Call("ac-oledbottom")])
    proc(c, "ac-anchortap", [If("acancs", [Call("ac-anchorgo")], [Call("ac-anchorset")])])
    proc(c, "ac-anchorgo", [Loop(str(NK), "aci", [T("acmto", "aci", "acanc[int(aci)]")]), Call("ac-verbcut")]
         + layers_from("acancm") + [V("acmdur", ANCG_MS), Call("ac-morphgo"), Toast("back to anchor")])
    # ---- the slot as loaded or saved (COMPARE's, and the changed dot's)
    proc(c, "ac-basesetto", [Loop(str(NK), "aci", [T("acbase", "aci", "acmto[int(aci)]")])]
         + [T("acbasem", j, n) for j, n in enumerate(L8)] + [X("1; 0", "v acbases", "v acchanged")])
    proc(c, "ac-basesetnow", [Loop(str(NK), "aci", [T("acbase", "aci", "acparams[int(aci)]")])]
         + [T("acbasem", j, n) for j, n in enumerate(L8)] + [X("1; 0", "v acbases", "v acchanged")])
    proc(c, "ac-cmpon", [If("acbases == 0", [V("accmp", "0"), Toast("nothing saved to compare")], [
        Loop(str(NK), "aci", [T("accur", "aci", "acparams[int(aci)]")])] + [T("accurm", j, n) for j, n in enumerate(L8)]
        + apply_cut("acbase") + layers_from("acbasem") + [V("accmp", "1"), Toast("compare - as saved"),
                                                           Send("ac-oledsetupq")])])
    proc(c, "ac-cmpoff", [If("accmp", apply_cut("accur") + layers_from("accurm") + [
        V("accmp", "0"), Toast("compare - yours"), Send("ac-oledsetupq")])])
    proc(c, "ac-chgcheck", [If("acbases && accmp == 0", [
        V("acchd", "0"),
        Loop(str(NK), "aci", [If(f"aci != {IN} && abs(acparams[int(aci)] - acbase[int(aci)]) > 0.004", [V("acchd", "1")])]),
    ] + [If(f"{n} != acbasem[{j}]", [V("acchd", "1")]) for j, n in enumerate(L8)] + [V("acchanged", "acchd")])])
    # ---- the macros (CC targets macro 1-4; SETUP MACRO B Value): acmcn the macro, acmcin its new value
    steps = []
    for m in range(4):
        one = []
        for t, d in (("ta", "da"), ("tb", "db")):
            one += [If(f"acmc{m}{t} > 0", [
                V("acmk", f"acmtk[int(acmc{m}{t})]"), V("acmdd", f"2*acmc{m}{d} - 1"),
                If(f"acmc{m}mode == 0", [
                    # offset: away from the stored value while the macro is up
                    V("acmorphing", "1"),
                    SendL("ac-param", ["acmk", "max(0, min(1, acparams[int(acmk)] + acmdd*acmcin))"]),
                    V("acmorphing", "0")], [
                    # latch: drags the stored value, which stays
                    T("acparams", "acmk", f"max(0, min(1, acparams[int(acmk)] + acmdd*(acmcin - acmc{m}p)))"),
                    SendL("ac-param", ["acmk", "acparams[int(acmk)]"])])])]
        steps += [If(f"acmcn == {m}", one + [X("acmcin; acmcin", f"v acmc{m}v", f"v acmc{m}p")])]
    proc(c, "ac-macro", steps + [Send("ac-oledsetupq")])
    # ---- SINK, SWELL, DUCK
    proc(c, "ac-sinkupd", [SendL("ac-g-sink", ["acsink > 0.001", "200"]), SendL("ac-sink", ["12000*pow(0.01, acsink)"])])
    proc(c, "ac-swellupd", [Call("ac-dgainupd")])
    proc(c, "ac-dgainupd", [
        V("acplay", "(acheld > 0 || acnow - acbreatht < 400)"),
        V("acdgt", "(1 - 0.75*acduck*acplay)*(1 + 0.3*acswell)"),
        If("acdgt != acdgl", [V("acdgl", "acdgt"), SendL("ac-dgain", ["acdgt", f"if(acplay, 80, {DUCKR_MS})"])])])
    # ---- PUMP: on the first beat of each period, the bed drops and comes back over 70 % of the period
    proc(c, "ac-pumpbeat", [If(f"int(actick/24) % int({S.PUMP_BEATS}) == 0", [
        SendL("ac-pumpenv", ["1 - 0.85*acpumpd", f"0.7*60000/acbpm*{S.PUMP_BEATS}"], "$1 8, 1 $2 8")])])
    proc(c, "ac-pumpupd", [If("acpump == 0", [SendL("ac-pumpenv", ["1"], "$1 50")])])
    # ---- JOURNEY: a step (each Speed / 4, or a CC's press): one pad voice on to its next engine (all four on a
    #      press), and with the first voice the drone and the struck engines; the crossfades take 60 % of a turn
    jt = f"if(acjour > 0, {JOUR_MS}, 30000)"
    jsteps = []
    for k in range(4):
        jsteps += [If(f"acjpad > 0 && (acjall || acjk == {k})", [
            T("acjpi", k, f"(acjpi[{k}] + 1) % acjpn[int(acjpad)]"),
            V("acjt", f"acjpt[int(acjpad*12 + acjpi[{k}])]"), T("acflav", k, "acjt"),
            SendL(f"ac-v{k}-flav", ["acjt"])])]
    jsteps += [If("acjall || acjk == 0", [
        If("acjdrone", [V("acjdi", f"(acjdi + 1) % {len(DRONES)}"), V("acdcur", "acjdi")]),
        If("acjstrike == 1 || acjstrike == 3", [V("acjbi", f"(acjbi + 1) % {len(STRIKES)}")]),
        If("acjstrike >= 2", [V("acjmi", f"(acjmi + 1) % {len(STRIKES)}")]),
        If("acjdrone || acjstrike > 0", [V("acfade", f"0.5*{jt}"), Call("ac-layers")])])]
    proc(c, "ac-jstep", [V("acflxf", f"0.6*{jt}")] + jsteps + [V("acjk", "(acjk + 1) % 4"), Later("ac-scr3", 31)])
    proc(c, "ac-jstepall", [V("acjall", "1"), Call("ac-jstep"), V("acjall", "0")])
    # a change of the JOURNEY page: a layer leaving it goes back to its own choice; one joining starts at once
    proc(c, "ac-jourupd", [
        If("acjpad == 0", [V("acflxf", "4000"), If("acjpadw", [Call("ac-padpick")])],
           [Loop("4", "aci", [T("acjpi", "aci", "(aci*3) % acjpn[int(acjpad)]")])]),
        V("acjpadw", "acjpad > 0"),
        If("acjdrone == 0", [V("acjdi", "-1")], [If("acjdi < 0", [V("acjdi", "acdcur")])]),
        If("acjstrike == 0 || acjstrike == 2", [V("acjbi", "-1")]),
        If("acjstrike < 2", [V("acjmi", "-1")]),
        If("acjstrike == 1 || acjstrike == 3", [If("acjbi < 0", [V("acjbi", "if(acsbell > 0, acsbell - 1, acbela)")])]),
        If("acjstrike >= 2", [If("acjmi < 0", [V("acjmi", "if(acsmot > 0, acsmot - 1, acmota)")])]),
        If("acjpad > 0 || acjdrone || acjstrike > 0 || acjon", [Call("ac-sndovr"), V("acfade", "3000"), Call("ac-layers")]),
        V("acjon", "acjpad > 0 || acjdrone || acjstrike > 0"),
        If("acjon", [Call("ac-jstepall"), V("acjnext", f"acnow + {jt}/4")]),
    ])
    # ---- the 100 ms tick (from ac-now): the morph's step, DUCK, the journey, CC OUT, and once a second the check
    lvl = [("drone", "acmxd"), ("sub", "acmxs"), ("pad", "acmxp"), ("bell", "acmxb"), ("motion", "acmxm"),
           ("tex", "acmxt"), ("atm", "acmxa"), ("cloud", "acmxc")]
    vals = [f"acg{n}*acsl{n}*{m}" for n, m in lvl] + [
        "acenergy", "acdeff", "acbright", "(acnow - acchgt)/max(1, acchsec*1000*actime)",
        "acsecel/max(1, acsecdur*actime)", "(acrvlvl - 45)/40", "(acdisp[0] - 36)/60", "max(acbreath, acheld/4)"]
    ve = "0"
    for i in range(len(vals) - 1, -1, -1):
        ve = f"if(aci == {i}, {vals[i]}, {ve})"
    proc(c, "ac-ptick", [
        If("acmph", [Call("ac-morphstep")]),
        Call("ac-dgainupd"),
        If("acjour > 0 && acrun && acnow >= acjnext && (acjpad > 0 || acjdrone || acjstrike > 0)", [
            V("acjnext", f"acnow + {jt}/4"), Call("ac-jstep")]),
        If("acccout && acnow >= acccnext", [
            V("acccnext", f"acnow + {CCRATE_MS}"),
            Loop("16", "aci", [V("acccv", f"int(127*max(0, min(1, {ve})) + 0.5)"),
                               If("acccv != acccl[int(aci)]", [
                                   T("acccl", "aci", "acccv"),
                                   SendL("ac-midibyte", ["175 + acccch"]), SendL("ac-midibyte", [f"{CCBASE} + aci"]),
                                   SendL("ac-midibyte", ["acccv"])])])]),
        V("acchk", "(acchk + 1) % 10"), If("acchk == 0", [Call("ac-chgcheck")]),
    ])
    # ---- the reverbs' pre-delay and era
    proc(c, "ac-rvcolour", [
        SendL("ac-rvpre", [S._pick("acrvpre", list(enumerate(S.SPRE)))]),
        SendL("ac-rvlop", ["if(acrvera == 0, 4500, if(acrvera == 1, 7500, if(acrvera == 2, 11000, 20000)))"]),
        SendL("ac-rvq", ["if(acrvera == 0, 128, if(acrvera == 1, 2048, if(acrvera == 2, 32768, 1e+06)))"])])
    return c
