"""MIDI out (clock, notes) and MIDI clock in (SETUP page 1 MIDI out / Sync; page 4 what goes out)."""
from pdlib import Canvas, proc, V, T, Send, Call, SendL, If, Loop, run_steps, Toast


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
