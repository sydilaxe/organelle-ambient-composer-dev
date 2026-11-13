"""Build the PDF manual from the same data the patch is generated from:
    python3 tools/manual.py [VERSION] [OUT.pdf]          (default: dev, dist/Amble-manual.pdf)

Every list of controls and choices (knob pages, function keys, SETUP items, scales, pad types, input modes,
tempo ranges, MIDI channels...) is read from the generator modules, and every one of them must have a
description here: a control added to the patch without one stops the build (see the checks at the end)."""
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import data as DT
import gen_brain
import gen_live
import gen_setup as S
import gen_ui as U

VERSION = sys.argv[1] if len(sys.argv) > 1 else "dev"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "dist", "Amble-manual.pdf")
SHOTS = os.path.join(HERE, "..", "docs", "shots")

# ---------------------------------------------------------------- descriptions (checked against the patch)
KNOBS = {   # value name -> (range, what it does)
    "acdens": ("0-100 %", "How much plays. With the section's energy it decides which layers sound and how full "
                          "they are; low values leave the drone and a few voices, high values bring in textures, "
                          "cloud, bells and motion."),
    "actide": ("0-100 %", "Harmonic pace: the time between chord changes (the section's role scales it further)."),
    "accolor": ("0-100 %", "Brightness of the pads, filters and resonators."),
    "acinput": ("0-100 %", "External audio amount. At 0 the input is ignored completely (no dry signal, no "
                           "processing, no listening, the pitch tracker off). It always starts at 0 when Amble "
                           "loads, whatever was saved: turn it up when something is plugged in."),
    "acrvmix": ("0-100 %", "Reverb mix."),
    "acrvtype": ("5 steps", "Reverb: Auto (the piece chooses), Bloom 1, Bloom 2, Hall, Shimmer."),
    "acrvtime": ("1.5-30 s", "Reverb decay time."),
    "acrvtone": ("0-100 %", "Reverb damping: low = dark, high = bright."),
    "aclen": ("5-30 min", "Length of a composed piece (COMPOSE). In DRIFT it sets how long sections last."),
    "acweird": ("0-100 %", "Strangeness: FM depth, wavefolding, unusual scales, key changes, reversed grains."),
    "acmotion": ("0-100 %", "Movement: pad breathing, pitch drift and how far voices travel in the stereo field."),
    "acrhythm": ("0-100 %", "Rhythm: the Euclidean motion layer, swing, the drone's bar pulse, locked grains."),
    "acsndd": ("off-full", "Reverb send of the drone and sub. 0 = dry, 50 % = the designed balance, 100 % = twice."),
    "acsndp": ("off-full", "Reverb send of the pads (and the notes you play, which use the pad synthesis types)."),
    "acsndb": ("off-full", "Reverb send of the bells."),
    "acsndm": ("off-full", "Reverb send of the motion layer (the Euclidean arpeggio)."),
    "acsndt": ("off-full", "Reverb send of the textures."),
    "acsndc": ("off-full", "Reverb send of the granular cloud."),
    "acsnda": ("off-full", "Reverb send of the atmosphere."),
    "acsndi": ("off-full", "Reverb send of the audio input: its dry signal and the input modes (resonators, "
                           "bands, tape, vocoder, memories)."),
}

FKEY_DESC = {
    "COMPOSE / DRIFT": "Switch between a composed piece (5-30 min, with a form and an end) and endless DRIFT.",
    "chord change now | aux: Resolve": "Move to the next chord at once. Aux + C# = Resolve: the harmony moves "
                                       "to the tonic as open fifths (root, 5th, octave, 12th) and stays there - no "
                                       "modulation, no dissonant chords - until you release it the same way "
                                       "(standalone: aux + C# twice quickly). A CC mapped to resolve does it too.",
    "next section": "Jump to the next section of the form.",
    "drone on/off": "Mute or unmute the drone (and sub).",
    "pads on/off": "Mute or unmute the 4 pad voices.",
    "textures on/off": "Mute or unmute the textures and atmosphere.",
    "cloud on/off | aux: Freeze": "Mute or unmute the granular cloud. Aux + F# = Freeze: the reverb tail and "
                                  "the cloud hold still; again to release (standalone: aux + F# twice quickly).",
    "bells on/off": "Mute or unmute the bell motif.",
    "capture 8 s of input": "Record 8 s of the input into the cloud and keep it as a memory.",
    "input mode": "Step through the input modes (see Audio input).",
    "start / stop": "Stop fades out over 8 s and freezes the piece where it is (section, chord, time left; "
                    "MIDI clock Stop and notes off). Start fades back in and goes on from there. After FIN it "
                    "starts a new piece.",
    "new piece": "Start a new piece with a new seed.",
}

SETUP_DESC = {   # label as it appears on the screen -> (choices, what it does)
    "MIDI out": (", ".join(S.MOUT), "Tempo = MIDI clock (24 per beat) following the piece's tempo, with Start and "
                                    "Stop. Notes = the parts listed under MIDI out."),
    "Sync": ("internal, follow clock", "Follow clock: an incoming MIDI clock drives Amble's rhythm; Start restarts "
                                       "the bar and starts a stopped piece, Stop stops the piece."),
    "Keys": ("auto, play notes, functions", "Auto: the Organelle keys play notes until an external controller plays, "
                                            "then they become function keys (and play again after 2 minutes "
                                            "without external notes)."),
    "Bloom": ("clean, vintage", "Vintage adds the MidiVerb II's 13-bit grain to the Bloom reverbs."),
    "Follow you": ("0-100 %", "How strongly the chords follow what you play or sing."),
    "MPE bend": (", ".join(str(b) for b in S.BENDS), "Per-note pitch-bend range in semitones (channel 1 uses 2)."),
    "MIDI out ch": ("1-16", "Base channel for MIDI notes out; the other parts count up from it."),
    "Breath curve": ("50-200 %", "Response of breath (CC 2, CC 11, aftertouch): below 100 softer, above harder."),
    "Output": (", ".join(S.OUTPUTS), "Stereo wide: the composed stereo image. Mono: both outputs the same, for "
                                     "mono rigs and external effects. Split: two mono stems - left the harmony bed "
                                     "(pads with their character, drone, sub), right everything else (bells, "
                                     "motion, textures, cloud, atmosphere, live voices, input); each side carries "
                                     "one side of the reverb."),
    "Width": ("50-150 %", "Overall stereo width."),
    "Pan motion": ("0-100 %", "How far the voices travel in the stereo field."),
    "Tempo": (", ".join(f"{n} {lo}-{hi}" for n, lo, hi in DT.TEMPOS), "The range a piece picks its tempo from. "
              f"Above {DT.HALFTIME} BPM the slow layers move at half time."),
    "MIDI notes": (", ".join(S.PARTS), "Which notes go out: all; harmony (chords, tonic, bass); or the arp chord "
                                       "only."),
    "Arp octave": ("C1-C5", "Where the arp chord starts (MIDI out, base channel + 5)."),
    "CPU": ("shown only", "Amble's CPU load now, and the CPU guard's level (lite 0-3)."),
    "CPU guard": ("off, on", "When on, Amble gets lighter under overload (see CPU)."),
    "Pads": ("auto, raw, " + ", ".join(DT.FLAVOURS), "The pad types. auto: the piece's palette, new picks each "
             "section. raw: the dry, buzzy types of the first demos (vox, part, fold, pulsr), no character effect. "
             "A type name: all four pad voices (and the notes you play) use it. Applies at once, crossfaded."),
    "Drone": ("auto, " + ", ".join(DT.DRONES), "The drone's design; auto = the piece's (and its break's)."),
    "Texture": ("auto, " + ", ".join(DT.TEXTURES), "The texture layer; auto = the section's two."),
    "Character": ("auto, " + ", ".join(DT.CHARACTERS), "The effect on the pads; auto = the piece's."),
    "Key": ("auto, C-B", "The home key. A fixed key stays: no modulation, no key plan, no key from you (a top-octave "
            "key still moves it). Applies at once with a chord change."),
    "Scale": ("auto, " + ", ".join(n for n, _ in DT.SCALES), "The scale. A fixed scale stays (no chance scale "
              "changes). Applies at once."),
    "Chords": ("auto, " + ", ".join(n for n, _, _ in DT.FAMILIES), "How the 4 pad voices stack the chord "
               "(see Voicings). Applies at once."),
    "Pulse": (", ".join(S.PULSES), "How much the drone and sub swell on every bar (normal = as designed; its "
              "depth also follows the section and the Rhy knob)."),
    "Notes to": (", ".join(S.ROUTES), "What MIDI notes and the Organelle keys play: voice = the live voice; chords "
                 "= the notes you hold are the pad chord; drone = the drone and sub on your note; bells = a bell per "
                 "note; cloud = each note tunes a grain stream. The notes still steer the harmony (Follow you)."),
    "Breath to": (", ".join(S.BRTOS), "What breath does: voice+piece = the live voice's level and tone and the "
                  "piece's density; voice or density alone; brightness, reverb (the sends) or swell (the whole "
                  "level, like an expression pedal). After 10 s without breath it lets go."),
    "Pressure to": ("a target (see CC)", "What channel and poly pressure do (default breath)."),
    "CC": (", ".join(str(n) for n in S.CCS), "Knob 1 picks a CC to set; row 2 shows what it does. Defaults: 1 vibrato, "
           "2 / 7 / 11 breath, 64 hold, 71 off, 74 voice tone."),
    "to": (", ".join(S.TARGETS), "off; breath (into the breath path, see Breath to); vibrato (the live voices' vibrato depth); voice tone and voice level (per note: the voice on the CC's channel, channel 1 = all, so MPE controllers shape each note); voice type (the live voices' synthesis type, across the 12 pad types); hold (a sustain pedal: released notes keep sounding until it lets go); density, colour, reverb, motion (move that knob); swell (the whole level); resolve (held at 64 and up: the tonic as open fifths, see C#)."),
    "Last CC": ("shown only", "The last CC that arrived and its value (0-127), to find what your controller sends."),
    "Vib rate": ("3-8 Hz", "The speed of the live voices' vibrato (its depth comes from a CC mapped to vibrato)."),
    "Breath in": ("shown only", "The breath level arriving now (after the Breath curve)."),
}

INMODE_DESC = {
    "auto": "Amble decides from what it hears: pitched sound rings chord strings and retunes the grains, and your "
            "pitch steers the harmony; plucked sound rings bells; texture plays tuned bands.",
    "reso": "4 comb strings tuned to the chord ring with your sound.",
    "cloud": "Your sound feeds the granular cloud.",
    "tape": "Long wobbling echoes that darken as they repeat.",
    "ghost": "Unheard: your loudness brightens the pads and your attacks ring bells.",
    "bands": "8 narrow bands on the chord tones - field recordings sing the harmony.",
    "vocode": "A 10-band vocoder: your sound speaks through a synth choir singing the chord.",
    "morph": "The vocoder with the pads as carrier: your sound speaks through the pads themselves.",
}

FLAV_DESC = {
    "fm": "two-operator FM, index following brightness", "vox": "a saw through drifting vowel formants",
    "bow": "a bowed string (Karplus-Strong with breath)", "part": "drifting additive partials",
    "fold": "a wavefolder", "pulsr": "pulsar synthesis: grains of a pulse train",
    "saws": "detuned analog saw ensemble through a tracking low-pass", "pwm": "Juno-like pulse-width modulation",
    "digi": "ring modulation, bit crush and sample-rate reduction", "sync": "a hard-sync sweep",
    "tine": "an electric-piano bell that strikes itself",
    "sine": "a harmonic sine pad: the fundamental and five harmonics, brightness tilting the upper ones in",
}
TEX_DESC = {"rain": "rain: a soft hiss, a dense patter of tiny drops and a few heavier plops",
            "wind": "filtered air", "ember": "crackling embers", "chirp": "bird-like chirps",
            "radio": "static on both sides, swelling in and out, with a heterodyne whistle tuning near a chord tone",
            "data": "bursts of tiny blips on chord tones", "buzz": "an electric hum on the tonic",
            "murmur": "ghostly murmurs: two distant voices, vowels drifting, in syllables and phrases",
            "echoes": "alien blips on chord tones in ping-pong echoes that bend in pitch as they repeat",
            "whisper": "whispers: breath shaped into fast syllables, one each side",
            "leaves": "leaves rustling in the trees, swelling with gusts",
            "brook": "a rippling, babbling brook"}
DRONE_DESC = {"pure": "tonic, a beating twin, an interval and breath tubes",
              "analog": "saws and a square through a slow resonant sweep",
              "organ": "drawbars with a rotary shimmer", "fm": "an electric growl"}
CHAR_DESC = {"clean": "no effect", "chorus": "a wide chorus", "tape": "wow, flutter, saturation and a little hiss",
             "ring": "ring modulation on the chord", "crush": "bit and sample-rate crush"}
ATMOS_DESC = {"haze": "air shimmering on the chord", "deep": "low rumble with distant thunder",
              "space": "air ringing in combs tuned to the chord", "night": "distant insects",
              "tides": "waves washing across the stereo field"}
VERB_DESC = {"auto": "the piece chooses (and the climax may shimmer)",
             "bloom1": "MidiVerb II Bloom (program 45): the sound swells for half a second, then rings out",
             "bloom2": "Bloom with an 85 ms pre-delay (program 49)",
             "hall": "an 8-line feedback-delay-network hall", "shimmer": "the Hall with an octave up in its loop"}
ARCH_DESC = {"arch": "rise to a central climax and fall", "build": "a slow build to a late climax",
             "waves": "ebb and flow", "twin": "two peaks", "journey": "a long trip away and home"}
ROLE_DESC = {"emerge": "the piece appears out of the drone", "establish": "the material is stated",
             "develop": "it moves and varies", "intensify": "denser, faster, more motion",
             "climax": "the fullest point", "break": "a sparse contrast, often the second drone and an atmosphere",
             "return": "the opening progression comes back", "dissolve": "it thins out and ends"}
SCENE_DESC = {"spread": "voices across the field", "split": "pads left, bells and motion right",
              "center": "a focused core in a wide halo", "circle": "everything orbits wide",
              "mirror": "pairs mirrored left and right"}
MIDI_CH = [("base", "the chord as Amble voices it (4 notes), held until the next change"),
           ("base + 1", "the tonic, held while the key stays"),
           ("base + 2", "the bells (the motif), short notes"),
           ("base + 3", "the motion layer's Euclidean arpeggio, short notes"),
           ("base + 4", "the bass: the sub's note (pedal or chord root), held"),
           ("base + 5", "the arp chord: the chord in close position from the Arp octave, held - for arpeggiators")]

SHARPS = "C C# D D# E F F# G G# A A# B".split()     # key names as printed on the Organelle

# ---------------------------------------------------------------- styles
ss = getSampleStyleSheet()
INK = colors.HexColor("#1d2330")
ACC = colors.HexColor("#3b6ea8")
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=18, textColor=INK, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13, textColor=ACC, spaceBefore=10, spaceAfter=4)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=9.5, leading=13, textColor=INK, spaceAfter=5)
C = ParagraphStyle("C", parent=P, fontSize=8.5, leading=11, spaceAfter=0)
CB = ParagraphStyle("CB", parent=C, fontName="Helvetica-Bold")
NOTE = ParagraphStyle("NOTE", parent=P, fontSize=8.5, textColor=colors.HexColor("#555b66"))


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table(rows, widths, head=True):
    data = [[Paragraph(esc(c) if not str(c).startswith("<") else c, CB if (head and i == 0) else C) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9ced8")),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6ecf5")))
    t.setStyle(TableStyle(st))
    return t


def para(t):
    return Paragraph(t, P)


def shot(name, w=3.4, caption=None):
    path = os.path.join(SHOTS, name + ".png")
    if not os.path.exists(path):
        return Spacer(1, 1)
    img = Image(path, width=w * inch, height=w * inch / 2)
    if caption:   # a list: usable as a table cell
        return [img, Paragraph(caption, ParagraphStyle("cap", parent=NOTE, alignment=TA_CENTER))]
    return img


def setup_items():
    """[(page, row, label)] from the generator's SETUP rows"""
    out = []
    for row, *pages in S.setup_rows():
        for pg, (text, _) in enumerate(pages):
            label = re.sub(r"\s*C?\$\d.*$", "", text.split(" ", 2)[2]).strip()
            out.append((pg + 1, row, label))
    return out


# ---------------------------------------------------------------- the manual
def story():
    s = []
    today = datetime.date.today().isoformat()
    s += [Spacer(1, 1.2 * inch),
          Paragraph("AMBLE", ParagraphStyle("T", parent=H1, fontSize=40, leading=48, alignment=TA_CENTER,
                                            textColor=INK, spaceAfter=10)),
          Paragraph("generative ambient composer for the Organelle M / S",
                    ParagraphStyle("ST", parent=P, fontSize=13, alignment=TA_CENTER)),
          Spacer(1, 0.25 * inch),
          Paragraph(f"Manual - version {esc(VERSION)} - built {today}",
                    ParagraphStyle("V", parent=NOTE, alignment=TA_CENTER)),
          Spacer(1, 0.4 * inch), shot("score_playing", 4.6), Spacer(1, 0.4 * inch),
          para("Every start, Amble invents a new piece: key and scale, chord voicings, a palette of synthesis types, "
               "tempo and meter, a motif, textures, reverb and a form. It composes a complete 5-30 minute piece or "
               "drifts endlessly as a backing for your playing, and it listens: to MIDI (including MPE and breath "
               "controllers such as the DM48X) and to audio on the line input."),
          para("This manual is generated from the patch's own source at every build, so its lists of controls and "
               "choices always match the patch it ships with."),
          PageBreak()]

    s += [Paragraph("1  Getting started", H1),
          para("<b>Install.</b> Unzip the release and copy the <b>Amble</b> folder into the Organelle's "
               "<b>Patches</b> folder (USB drive or SD card). It needs Organelle OS 5 (Pd 0.53 or later) and uses "
               "vanilla Pd objects only."),
          para("<b>Start.</b> Load Amble from the menu. A new piece begins at once. The screen shows the piece as a "
               "live score; the knobs shape it; the keys play notes (or, with an external controller, run "
               "functions); hold <b>aux</b> for 1 s for SETUP."),
          para("<b>Audio input.</b> Amble uses the Organelle's line input. Set the Organelle's mic/line switch to "
               "<b>Line</b>, plug in, and raise the <b>In</b> knob (SHAPE page). At In 0 the input is ignored, and "
               "In always starts at 0 when Amble loads."),
          para("<b>Settings</b> (knob values and SETUP, except In) are saved in <b>settings.txt</b> in the patch folder. "
               "<b>seed.txt</b> counts start-ups so no two sessions begin the same way.")]

    s += [Paragraph("2  The screen", H1),
          para("The OLED is a live score of the piece."),
          table([["Region", "What it shows"],
                 ["Top strip", "The form: one bar per section (height = energy), the current one inverted, a "
                               "playhead. In DRIFT: the energy and the section's progress."],
                 ["Line 2", "Key and scale; the time left (elapsed in DRIFT); short messages."],
                 ["Left", "The 4 pad voices as dots on a pitch ladder (they glide between chords); your held notes "
                          "as boxes; tonic ticks; a breath bar. A pitch heard on the input is a line across it."],
                 ["Middle", "Meters: drone, pads, textures, cloud, bells, motion, reverb, and the input level."],
                 ["Right", "The motion layer's Euclidean pattern with its cursor, the tempo, the reverb (B1 B2 HALL "
                           "SHIM). While audio comes in: the input panel - 6 s of its level as a waveform with "
                           "onsets ticked, the input mode and what Amble hears (pitch, pluck, textr), a dot while "
                           "a memory records."],
                 ["Bottom", "Section role and voicing; K = keys play, M = external MIDI, E = following an external "
                            "clock; FIN at the end."]], [1.0, 5.7]),
          Spacer(1, 6),
          Table([[shot("score", 3.1, "The score"), shot("input", 3.1, "The input panel")],
                 [shot("knob_popup", 3.1, "Turning a knob shows its page for 6 s"),
                  shot("toast", 3.1, "Messages take line 2 briefly")]],
                colWidths=[3.35 * inch, 3.35 * inch]),
          PageBreak()]

    rows = [["Page", "Knob", "Name", "Range", "Default", "What it does"]]
    for pi, page in enumerate(DT.PAGES):
        for ki, (label, name, default) in enumerate(page):
            rng, desc = KNOBS[name]
            rows.append([DT.PAGE_NAMES[pi] if ki == 0 else "", str(ki + 1), label, rng,
                         f"{int(round(default * 100))} %", desc])
    s += [Paragraph("3  Knobs", H1),
          para(f"The four knobs have {len(DT.PAGES)} pages: " + ", ".join(DT.PAGE_NAMES) + ". A tap on <b>aux</b> "
               "goes to the next page. Knobs pick up smoothly: after a page change a knob moves its value towards "
               "the end it turns to, so nothing jumps."),
          table(rows, [0.6, 0.4, 0.55, 0.75, 0.6, 3.8])]

    frows = [["Key", "Function", "What it does"]]
    for i, name in enumerate(U.FKEYS):
        frows.append([SHARPS[i] + " (top)", name, FKEY_DESC[name]])
    s += [Paragraph("4  Keys, aux and footswitch", H1),
          para("<b>Standalone</b>, the Organelle keys play notes: 4 voices in the piece's own synthesis type. "
               "<b>Functions</b> are aux + key."),
          para("<b>With an external controller</b> (DM48X, any keyboard) playing, it takes over and the Organelle "
               "keys become function keys without aux. After 2 minutes without external notes the keys play "
               "again. SETUP <i>Keys</i> can fix either behaviour."),
          para("<b>Low octave</b> (C to B): choose the next key centre. <b>Top octave</b>: the functions below."),
          para("<b>Combinations.</b> With an external controller (plain keys are functions), <b>aux + F#</b> is "
               "<b>Freeze</b>. Standalone (functions are already aux + key), Freeze is <b>aux + F# twice "
               f"quickly</b> (within {U.TAP2_MS} ms); a single aux + F# toggles the cloud after that short wait."),
          table(frows, [0.9, 1.6, 4.2]),
          Spacer(1, 6),
          table([["Control", "What it does"],
                 ["Aux tap", "Next knob page (in SETUP: next SETUP page)."],
                 ["Aux held 1 s", "Enter SETUP; hold again to leave and save."],
                 ["Footswitch", "Chord change now."]], [1.4, 5.3])]

    items = setup_items()
    srows = [["Page", "Row", "Item", "Choices", "What it does"]]
    for pg, row, label in sorted(items):
        ch, desc = SETUP_DESC[label]
        srows.append([str(pg), str(row), label, ch, desc])
    s += [PageBreak(), Paragraph("5  SETUP", H1),
          para(f"Hold <b>aux</b> for 1 s. A tap on aux turns the {S.NSET} pages; knobs 1-4 set the 4 rows "
               "(absolute positions). Hold aux for 1 s again to leave; settings are saved."),
          table(srows, [0.45, 0.4, 1.0, 1.75, 3.1]),
          Spacer(1, 6),
          Table([[shot("setup", 3.1, "SETUP page 1"), shot("setup_page2", 3.1, "SETUP page 2")],
                 [shot("setup_page3", 3.1, "SETUP page 3"), shot("setup_page4", 3.1, "SETUP page 4")],
                 [shot("setup_page5", 3.1, "SETUP page 5: SOUNDS"), shot("setup_page6", 3.1, "SETUP page 6: MUSIC")],
                 [shot("setup_page7", 3.1, "SETUP page 7: MIDI IN"), shot("setup_page8", 3.1, "SETUP page 8: CC MAP")]],
                colWidths=[3.35 * inch, 3.35 * inch])]

    s += [PageBreak(), Paragraph("6  How a piece is composed", H1),
          para("A seed picks the key and scale, voicing families, the pad palette, tempo and meter, the motif, "
               "textures, drone, character, reverb and a form. <b>COMPOSE</b> plays one piece of 5-30 minutes "
               "(the Len knob) and ends with FIN; <b>B</b> (top) starts a new one. <b>DRIFT</b> plays endless "
               "sections for backing a performance."),
          Paragraph("Forms", H2),
          table([["Form", "Shape"]] + [[a, ARCH_DESC[a]] for a in DT.ARCHETYPES], [1.2, 5.5]),
          Paragraph("Section roles", H2),
          para("Each piece has 6-12 sections. A section's role sets the layers that play, the key area (out from "
               "home and back), the tempo, the harmonic pace, the drone pulse, the motif transformation, the "
               "stereo scene and the reverb."),
          table([["Role", "Character"]] + [[r, ROLE_DESC[r]] for r in DT.ROLES], [1.2, 5.5]),
          Paragraph("Harmony", H2),
          para(f"{len(DT.SCALES)} scales, including just intonation, harmonic-7th, slendro and pelog: "
               + esc(", ".join(n for n, _ in DT.SCALES)) + "."),
          para(f"{len(DT.FAMILIES)} voicing families for the 4 pad voices: "
               + esc(", ".join(n for n, _, _ in DT.FAMILIES)) + ". Voices are led smoothly, change one at a "
               "time, and each breathes in its own cycle so they phase against each other."),
          Paragraph("The composer listens", H2),
          para("What you hold or sing pulls the next chord to contain it (SETUP <i>Follow you</i>). A note held "
               "6 s becomes the new key centre. Breath raises the energy, and while you play a section waits for "
               "you (up to 3 x 30 s). In silence the piece leads.")]

    s += [PageBreak(), Paragraph("7  Sound", H1),
          Paragraph("Layers and their rhythms", H2),
          para("One clock drives everything (meter 3-7 per piece; tempo from the SETUP Tempo range)."),
          table([["Layer", "What it is"],
                 ["Drone", "One of 4 designs per piece (the break may switch); swells on each bar in intense "
                           "sections."],
                 ["Sub", "A sine under everything, softly saturated: the pedal an octave under the tonic, the "
                         "chord root as a bass line, or both."],
                 ["Pads", "4 voices, each one of the synthesis types below; most are stereo inside."],
                 ["Character", "An effect on the pads per piece."],
                 ["Motion", "Euclidean patterns (e.g. 5 in 8, 7 in 16) arpeggiating the chord on FM pings, with "
                            "swing and tempo echoes."],
                 ["Bells", "The motif, phrased in beats with rubato."],
                 ["Textures", "Up to two per section."],
                 ["Cloud", "Grains of the recent sound or your input; locked to the beat in intense sections."],
                 ["Atmosphere", "In about half the pieces, mostly in emerge, break and dissolve sections."]],
                [1.2, 5.5]),
          Paragraph("Pad synthesis types", H2),
          table([["Type", "Sound"]] + [[f, FLAV_DESC[f]] for f in DT.FLAVOURS], [1.2, 5.5]),
          para("The electronic and bell-like types come up most often."),
          Paragraph("Drones, character, textures, atmospheres", H2),
          table([["Drone", "Sound"]] + [[d, DRONE_DESC[d]] for d in DT.DRONES], [1.2, 5.5]),
          Spacer(1, 4),
          table([["Character", "Effect"]] + [[c, CHAR_DESC[c]] for c in DT.CHARACTERS], [1.2, 5.5]),
          Spacer(1, 4),
          table([["Texture", "Sound"]] + [[t, TEX_DESC[t]] for t in DT.TEXTURES], [1.2, 5.5]),
          Spacer(1, 4),
          table([["Atmosphere", "Sound"]] + [[a, ATMOS_DESC[a]] for a in DT.ATMOS_NAMES], [1.2, 5.5]),
          Paragraph("Reverb", H2),
          para("Chosen with the Verb knob (SPACE page). Each section change makes the reverb bloom up."),
          table([["Reverb", "Character"]] + [[v, VERB_DESC[v]] for v in DT.VERBS], [1.2, 5.5]),
          Paragraph("Stereo", H2),
          para("Each section places the voices in a scene. The bass and sub stay centred; the drone's twin and "
               "interval orbit, each pad voice has its own place and orbits around it, grains and bells land "
               "anywhere, the motion arpeggio sweeps across, the reverbs are decorrelated. Width grows with the "
               "form. Summed to mono it loses about 1 dB; SETUP <i>Output</i> can make it mono, or split it into two "
               "mono stems (harmony left, everything else right)."),
          table([["Scene", "Placement"]] + [[sc, SCENE_DESC[sc]] for sc in DT.SCENES], [1.2, 5.5])]

    s += [PageBreak(), Paragraph("8  Audio input", H1),
          para("Use the Organelle's line input (mic/line switch on <b>Line</b>) for samples, guitar, harmonica, "
               "voice or field recordings. The <b>In</b> knob sets the amount; at 0 the input is ignored. A gate "
               "and automatic gain level it, then Amble listens for pitch, attacks and noisiness and calls the "
               "sound pitched, plucked or texture."),
          table([["Mode", "What happens"]] + [[m, INMODE_DESC[m]] for m in DT.INMODES], [1.0, 5.7]),
          para("Change the mode with the <b>input mode</b> function key (A, top)."),
          Paragraph("Memories, capture and hold", H2),
          para("While the piece develops, Amble keeps 8 s of what you played (up to 4 memories). Break, return and "
               "dissolve sections bring them back: reversed, slowed or retuned to the chord. <b>Capture</b> (G#, "
               "top) records 8 s now. <b>Freeze</b> (aux + F#; standalone aux + F# twice) holds the reverb tail "
               "and the cloud still.")]

    s += [Paragraph("9  MIDI", H1),
          Paragraph("MIDI in: notes, MPE and breath", H2),
          para("Any external keyboard or controller plays 4 voices in the piece's synthesis type. MPE: each note on "
               "its own channel with per-note bend (SETUP <i>MPE bend</i>; channel 1 bends 2 semitones). Breath is "
               "read from CC 2, CC 11, channel pressure or poly pressure; with breath, notes follow your breath in "
               "level and brightness (SETUP <i>Breath curve</i>)."),
          Paragraph("MIDI out", H2),
          para("SETUP <i>MIDI out</i>: " + esc(", ".join(S.MOUT)) + ". Tempo is MIDI clock (24 per beat) at the "
               "piece's tempo, following its changes, with Start and Stop. Notes go out on these channels, counted "
               "from SETUP <i>MIDI out ch</i> (wrapping after 16):"),
          table([["Channel", "Part"]] + MIDI_CH, [1.0, 5.7]),
          para("Chord and bass velocities follow the piece's energy. Notes are rounded to the nearest semitone. "
               "SETUP <i>MIDI notes</i> chooses all parts, harmony only, or the arp chord only."),
          Paragraph("Sync", H2),
          para("SETUP <i>Sync</i> = follow clock: an incoming MIDI clock drives the rhythm. MIDI Start restarts the "
               "bar and starts the piece if it was stopped; MIDI Stop stops the piece (as A#). Any tempo then comes "
               "from outside.")]

    s += [Paragraph("10  Tempo", H1),
          table([["Range", "BPM"]] + [[n, f"{lo}-{hi}"] for n, lo, hi in DT.TEMPOS], [1.2, 5.5]),
          para(f"Set in SETUP <i>Tempo</i>; a change applies at once, keeping the piece's place in the range. "
               f"Sections move the tempo within the piece. Above {DT.HALFTIME} BPM the pad breathing, bells and "
               "the drone's bar swell move at half time and the arpeggio counts in 8ths.")]

    s += [Paragraph("11  CPU", H1),
          para("Amble runs on one core. Only what sounds runs; the reverbs, vocoder and pitch tracker run at half "
               "rate; heavy changes are spread over a few milliseconds. The <b>CPU guard</b> measures the load "
               "each second: above 78 % it gets lighter in steps - 1 cloud and atmosphere off, 2 textures and the "
               "pad character off, 3 the automatic vocoder off - and steps back after 20 s below 50 %. The pads, "
               "drone, sub, bells, motion and reverb are never changed. SETUP page 4 shows the load and the "
               "guard's level and can turn the guard off. The CPU reading is an average over a second; short spikes "
               "inside it are absorbed by the audio buffer, which Amble sets to 25 ms in <b>pd-opts.txt</b> "
               "(the Organelle starts Pd with 6 ms).")]

    s += [Paragraph("12  Troubleshooting", H1),
          table([["Symptom", "What to do"],
                 ["The built-in mic is heard", "Set the mic/line switch to Line and the In knob to 0. If you "
                                               "still hear it with no patch loaded, it is the Organelle's own "
                                               "mixer, not Amble."],
                 ["Crackle, even with a low CPU reading", "The audio buffer is too small for brief spikes. Amble's "
                                                          "pd-opts.txt asks for 25 ms (the Organelle's default is "
                                                          "6 ms); raise the number in Patches/Amble/pd-opts.txt, "
                                                          "e.g. to 40. Lower it for less delay when playing live."],
                 ["Crackle when a lot is playing", "Leave the CPU guard on; check the CPU reading on SETUP "
                                                   "page 4; lower Dens or choose Bloom instead of Shimmer."],
                 ["Keys run functions instead of notes", "An external controller took over: wait 2 minutes, or "
                                                         "set SETUP Keys to play notes."],
                 ["Nothing happens at the end", "COMPOSE ended (FIN): press B or A# (top) for a new piece, or "
                                                "switch to DRIFT with C (top)."],
                 ["Silence and STOPPED on the screen", "The piece is stopped: A# (top) starts it again where it "
                                                       "was."]], [2.0, 4.7]),
          Spacer(1, 10),
          Paragraph(f"Amble {esc(VERSION)} is GPL-3. The Bloom reverb follows Conduit's bloom.c, after "
                    "thement's midiverb_emulator analysis of the Alesis MidiVerb II.", NOTE)]
    return s


def checks():
    """every control and choice in the patch has a description here"""
    missing = [n for p in DT.PAGES for _, n, _ in p if n not in KNOBS]
    missing += [k for k in U.FKEYS if k not in FKEY_DESC]
    missing += [lab for _, _, lab in setup_items() if lab not in SETUP_DESC]
    for names, desc in ((DT.INMODES, INMODE_DESC), (DT.FLAVOURS, FLAV_DESC), (DT.TEXTURES, TEX_DESC),
                        (DT.DRONES, DRONE_DESC), (DT.CHARACTERS, CHAR_DESC), (DT.ATMOS_NAMES, ATMOS_DESC),
                        (DT.VERBS, VERB_DESC), (DT.ARCHETYPES, ARCH_DESC), (DT.ROLES, ROLE_DESC),
                        (DT.SCENES, SCENE_DESC)):
        missing += [n for n in names if n not in desc]
    if missing:
        sys.exit("manual.py: no description for: " + ", ".join(missing))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#7a808c"))
    canvas.drawString(0.75 * inch, 0.5 * inch, f"Amble {VERSION} - manual")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, str(doc.page))
    canvas.restoreState()


def main():
    checks()
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.75 * inch, title=f"Amble {VERSION} manual",
                            author="Amble")
    doc.build(story(), onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    main()
