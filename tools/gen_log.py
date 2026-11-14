"""The performance log (SETUP 4, CPU guard "... log"): what Amble did and what it cost, every 5 s, into
logs/perf-BBBBPP.txt in the patch folder (BBBB the start-up count, PP the part), to copy off the card and read with
tools/perf_report.py.

Each line: the fields of FIELDS, in order (the file's first line names them). The load is measured as the guard
does (CPU time over logical time), over 100 ms windows: the average and the worst window of each 5 s. A part holds
10 minutes (120 lines) and is written once a minute (and when the piece stops), so a write stays small: Pd writes
files on its audio thread, and a big write on the Organelle's SD card could itself make the audio drop out."""
from pdlib import Canvas, proc, V, T, X, Send, SendL, Call, If, Loop, Arm, Toast, Later, run_steps

# (name, expression): one line every 5 s
FIELDS = [
    ("t", "int(acnow/1000)"), ("load", "int(100*aclgsum/max(1, aclgn))"), ("peak", "int(100*aclgmax)"),
    ("guard", "acshed"), ("run", "acrun + 2*acstopped"), ("sec", "acsec"), ("role", "acrole"),
    ("layers", " + ".join(f"{1 << i}*(acg{n} > 0.01)" for i, n in enumerate(
        ("drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud")))),
    ("pad0", "acflav[0]"), ("pad1", "acflav[1]"), ("pad2", "acflav[2]"), ("pad3", "acflav[3]"), ("drone", "acdcur"),
    ("bells", "if(acjbi >= 0, acjbi, if(acsbell > 0, acsbell - 1, acbela))"),
    ("motion", "if(acjmi >= 0, acjmi, if(acsmot > 0, acsmot - 1, acmota))"),
    ("journey", "acjour*1000 + acjpad*100 + acjdrone*10 + acjstrike"),
    ("sink", "int(100*acsink)"), ("blur", "int(100*acblur)"), ("swell", "int(100*acswell)"), ("harm", "int(100*acharmx)"),
    ("pump", "acpump"), ("duck", "int(100*acduck)"), ("spark", "int(100*acspark)"), ("ccout", "acccout"),
    ("input", "int(100*acinput)"), ("inmode", "acinmode"), ("held", "acheld"), ("verb", "acvtype"), ("page", "acpage"),
    ("setup", "acsetup*100 + acsetpg"), ("morph", "acmph"),
]
# the profile run (SETUP 4, knob 3 turned fully up): every part alone for a few seconds, its load measured
def _parts():
    from data import FLAVOURS, DRONES, STRIKES, TEXTURES, ATMOS_NAMES, CHARACTERS
    on = lambda g: SendL(g, ["1"], "$1 30")
    inp = [SendL("ac-insw", ["1"]), SendL("ac-trk", ["1"])]
    pads = lambda t: [on("ac-g-pad")] + [SendL(f"ac-v{k}-flav", [str(t)]) for k in range(4)]
    parts = [("baseline", [])]
    parts += [(f"pad-{n}", pads(i)) for i, n in enumerate(FLAVOURS)]
    parts += [("pad-crossfade", pads(FLAVOURS.index("sine")) + [Later("ac-profxf", 1500)])]
    parts += [(f"drone-{n}", [on("ac-g-drone" if i == 0 else f"ac-g-drone{i}")]) for i, n in enumerate(DRONES)]
    parts += [("sub", [on("ac-g-sub")])]
    parts += [(f"bells-{n}", [on(f"ac-g-bel{i}")]) for i, n in enumerate(STRIKES)]
    parts += [(f"motion-{n}", [on("ac-g-motion"), on(f"ac-g-mot{i}")]) for i, n in enumerate(STRIKES)]
    parts += [(f"texture-{n}", [on(f"ac-g-tex{i}")]) for i, n in enumerate(TEXTURES)]
    parts += [(f"atmos-{n}", [on(f"ac-g-atm{i}")]) for i, n in enumerate(ATMOS_NAMES)]
    parts += [("cloud", [on("ac-g-cloud")])]
    parts += [(f"character-{n}", [on(f"ac-g-ch{i}")]) for i, n in enumerate(CHARACTERS) if i > 0]
    parts += [("reverb-bloom", [on("ac-g-rvb")]), ("reverb-hall", [on("ac-g-rvh")]),
              ("reverb-shimmer", [on("ac-g-rvh"), SendL("ac-shim", ["0.3"], "$1 30")])]
    parts += [("input-stage", inp), ("input-reso", inp + [on("ac-g-res")]), ("input-tape", inp + [on("ac-g-tape")]),
              ("input-bands", inp + [on("ac-g-bands")]), ("input-vocoder", inp + [on("ac-g-voc")]),
              ("memory-play", [on("ac-g-mem")])]
    parts += [("glint", [on("ac-g-glint")]), ("sink", [on("ac-g-sink")])]
    parts += [("live-voices-4", [SendL("ac-livenote", [str(2 + k), str(55 + 5 * k), "100"]) for k in range(4)])]
    return parts


# every gain a part switches on, back to 0 before the next part
OFF = (["ac-g-pad", "ac-g-drone", "ac-g-sub", "ac-g-motion", "ac-g-cloud", "ac-g-rvb", "ac-g-rvh", "ac-shim", "ac-g-res",
        "ac-g-tape", "ac-g-bands", "ac-g-voc", "ac-g-mem", "ac-g-glint", "ac-g-sink", "ac-insw", "ac-trk"]
       + [f"ac-g-drone{i}" for i in range(1, 5)] + [f"ac-g-bel{i}" for i in range(6)] + [f"ac-g-mot{i}" for i in range(6)]
       + [f"ac-g-tex{i}" for i in range(12)] + [f"ac-g-atm{i}" for i in range(5)] + [f"ac-g-ch{i}" for i in range(1, 5)])

GLOBALS = dict(acprof=0, acprst=0, acprsum=0, acprn=0, acprmax=0, aclogwas=0, aclogon=0, aclgsum=0, aclgn=0, aclgmax=0, aclgw=0, aclgpart=0, aclgfile=0, aclgl=0)
ARRAYS = dict(aclogbuf=len(FIELDS), acprfl=4)


def perflog():
    c = Canvas("perf-log", w=2400)
    c.comment("Performance log (SETUP 4 CPU guard ... log): a line every 5 s into logs/perf-BBBBPP.txt")
    td = c.obj("text define aclog")
    # every 100 ms while logging: the load of that window (CPU time / logical time)
    met = c.obj("metro 100")
    c.c(c.recv("ac-logrun"), 0, met, 0)
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
    c.c(up, 1, c.obj("v aclgw"), 0)
    run_steps(c, (up, 0), [If("acprof", [V("acprsum", "acprsum + aclgw"), V("acprn", "acprn + 1"),
                                         V("acprmax", "max(acprmax, aclgw)")],
                              [V("aclgsum", "aclgsum + aclgw"), V("aclgn", "aclgn + 1"), V("aclgmax", "max(aclgmax, aclgw)"),
                               If("aclgn >= 50", [Call("ac-logline")])])])
    c.col()
    # a line: the fields into the buffer, the buffer appended to the text
    line = c.obj("t b b")
    c.c(c.recv("ac-logline"), 0, line, 0)
    run_steps(c, (line, 1), [T("aclogbuf", i, e) for i, (_, e) in enumerate(FIELDS)])
    add = c.obj("text set aclog 1e+06")
    c.c(c.to((line, 0), "array get aclogbuf"), 0, add, 0)
    c.c(c.to(c.recv("ac-logline"), "t b"), 0, c.obj("s ac-logafter"), 0)
    proc(c, "ac-logafter", [V("aclgsum", "0"), V("aclgn", "0"), V("aclgmax", "0"), V("aclgl", "aclgl + 1"),
                            If("aclgl % 12 == 0", [Send("ac-logwrite")]),
                            If("aclgl >= 120", [Send("ac-logwrite"), Call("ac-lognew")])])
    c.col()
    # the file: logs/perf-BBBBPP.txt; a new part every 120 lines (10 minutes)
    proc(c, "ac-lognew", [V("aclgpart", "aclgpart + 1"), V("aclgl", "0"), V("aclgfile", "(account % 10000)*100 + aclgpart % 100"),
                          Send("ac-logclear")])
    clr = c.obj("t b b")
    c.c(c.recv("ac-logclear"), 0, clr, 0)
    hdr = c.m((clr, 0), "list " + " ".join(n for n, _ in FIELDS))
    c.c(hdr, 0, c.obj("text set aclog 1e+06"), 0)
    c.c(c.m((clr, 1), "clear"), 0, td, 0)
    fn = c.ch(c.recv("ac-logwrite"), "expr aclgfile", "makefilename logs/perf-%06d.txt")
    c.c(c.m(fn, "write $1"), 0, td, 0)
    c.col()
    # ---- the profile run: the piece stops, the output is silent (the parts still compute); then every part alone:
    #      2 s to settle, 4 s measured; a line each (name, average %, worst 100 ms %) into logs/profile-BBBB.txt
    parts = _parts()
    pt = c.obj("text define acprofile")
    base = [SendL(g, ["0"], "$1 20") for g in OFF] + \
           [SendL("ac-livenote", [str(2 + k), str(55 + 5 * k), "0"]) for k in range(4)]
    proc(c, "ac-profile", [If("acprof == 0", [
        If("acstopped == 0", [Call("ac-stop")]), Send("ac-master", "0 300"),
        Send("ac-chgstop"), Send("ac-secstop"), V("acsetup", "0"), Call("ac-oledall"),
        X("1; 0; aclogon", "v acprof", "v acprst", "v aclogwas"), Send("ac-logrun", "1"), V("acflxf", "50"),
        Loop("4", "aci", [T("acprfl", "aci", "acflav[int(aci)]")]),
        Send("ac-profclear"), Later("ac-profgo", 9000)])])     # (after the stop's fade)
    pc = c.obj("t b b")
    c.c(c.recv("ac-profclear"), 0, pc, 0)
    c.c(c.m((pc, 0), "list part load peak"), 0, c.obj("text set acprofile 1e+06"), 0)
    c.c(c.m((pc, 1), "clear"), 0, pt, 0)
    steps = []
    for i, (name, act) in enumerate(parts):
        steps += [If(f"acprst == {i}", act + [Toast(f"profile {i + 1}/{len(parts)} {name}")])]
    proc(c, "ac-profgo", base + steps + [Arm("ac-profmeasure", "2000", stop="ac-profstop")])
    proc(c, "ac-profmeasure", [X("0; 0; 0", "v acprsum", "v acprn", "v acprmax"), Arm("ac-profrecord", "4000", stop="ac-profstop")])
    # (the crossfade part: the voices fade from sine to glass over 10 s, so two types compute in each)
    proc(c, "ac-profxf", [V("acflxf", "10000")] + [SendL(f"ac-v{k}-flav", ["12"]) for k in range(4)])
    # (right to left: the part's values into the list's right inlet, its name out through the left, then on)
    rec = c.obj("t b b b")
    c.c(c.recv("ac-profrecord"), 0, rec, 0)
    names = c.obj("expr acprst")
    c.c((rec, 1), 0, names, 0)
    sel = c.to(names, "sel " + " ".join(str(i) for i in range(len(parts))))
    lst = c.obj("list append")
    for i, (name, _) in enumerate(parts):
        c.c(c.m((sel, i), f"symbol {name}"), 0, lst, 0)
    c.c(c.to(c.recv("ac-profvals"), "t l"), 0, lst, 1)
    c.c(lst, 0, c.obj("text set acprofile 1e+06"), 0)
    run_steps(c, (rec, 0), [V("acflxf", "50"), V("acprst", "acprst + 1"),
                            If(f"acprst < {len(parts)}", [Later("ac-profgo", 10)], [Call("ac-profend")])])
    proc(c, "ac-profvalsq", [SendL("ac-profvals", ["int(1000*acprsum/max(1, acprn))/10", "int(1000*acprmax)/10"])])
    c.c((rec, 2), 0, c.obj("s ac-profvalsq"), 0)
    pf = c.ch(c.recv("ac-profwrite"), "expr account % 10000", "makefilename logs/profile-%04d.txt")
    c.c(c.m(pf, "write $1"), 0, pt, 0)
    # the end: written; everything back as the piece had it, stopped (A# starts it again)
    proc(c, "ac-profend", base + [Send("ac-profwrite"), V("acprof", "0"), V("acflxf", "4000"),
                                  Loop("4", "aci", [T("acflav", "aci", "acprfl[int(aci)]")])]
         + [SendL(f"ac-v{k}-flav", [f"acprfl[{k}]"]) for k in range(4)]
         + [V("acfade", "500"), Call("ac-layers"), Call("ac-verbsel"), Call("ac-inputupd"), Call("ac-sinkupd"),
            Call("ac-sparkupd"), If("aclogwas == 0", [Send("ac-logrun", "0")]),
            Toast("profile written - A# to start")])
    c.col()
    # on, off (SETUP 4); when the piece stops, the part so far is written
    proc(c, "ac-logupd", [If("acguard >= 2", [If("aclogon == 0", [V("aclogon", "1"), Call("ac-lognew"),
                                                                  Send("ac-logrun", "1")])],
                             [If("aclogon", [V("aclogon", "0"), Send("ac-logrun", "0"), Send("ac-logwrite")])])])
    return c
