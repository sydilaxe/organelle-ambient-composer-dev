"""Musical data for the composer: scales, chord-voicing families, move tables, timbre sets.
Everything here is loaded into Pd arrays at start-up; a piece picks from it with its own seed."""

# Scales in semitones from the tonic (floats allowed: just and non-western tunings).
SCALES = [
    ("lydian",   [0, 2, 4, 6, 7, 9, 11]),
    ("dorian",   [0, 2, 3, 5, 7, 9, 10]),
    ("aeolian",  [0, 2, 3, 5, 7, 8, 10]),
    ("mixolyd",  [0, 2, 4, 5, 7, 9, 10]),
    ("ionian",   [0, 2, 4, 5, 7, 9, 11]),
    ("phrygian", [0, 1, 3, 5, 7, 8, 10]),
    ("majpent",  [0, 2, 4, 7, 9]),
    ("minpent",  [0, 3, 5, 7, 10]),
    ("hirajosi", [0, 2, 3, 7, 8]),
    ("wholetn",  [0, 2, 4, 6, 8, 10]),
    ("justmaj",  [0, 2.04, 3.86, 4.98, 7.02, 8.84, 10.88]),     # 5-limit just major
    ("harm7",    [0, 2.04, 3.86, 5.51, 7.02, 8.41, 9.69]),      # harmonics 8..14
    ("lyddom",   [0, 2, 4, 6, 7, 9, 10]),
    ("melmin",   [0, 2, 3, 5, 7, 9, 11]),
    ("slendro",  [0, 2.4, 4.8, 7.2, 9.6]),                      # 5-tone equal
    ("pelog",    [0, 1.2, 2.7, 5.4, 6.8, 7.9, 10.4]),
]

# Chord voicing families for the 4 pad voices: (name, type, offsets)
#   type 0: offsets are scale degrees above the chord root (voice-led per voice)
#   type 1: offsets are semitones above the chord root (spectral: kept as a block)
FAMILIES = [
    ("spread",   0, [0, 4, 9, 13]),       # root, 5th, 10th, 14th: wide open
    ("quartal",  0, [0, 3, 6, 9]),        # stacked scale 4ths
    ("cluster",  0, [0, 8, 9, 11]),       # root low, a tight cluster an octave up
    ("fifths",   0, [0, 4, 8, 12]),       # stacked scale 5ths
    ("ninths",   0, [0, 6, 8, 11]),       # root, 7th, 9th, 11th(+8va)
    ("spectral", 1, [0, 19.02, 27.86, 33.69]),  # partials 1, 3, 5, 7 of the root
    ("mirror",   0, [-3, 0, 3, 6]),       # 4ths around the root
    ("sus",      0, [0, 3, 4, 8]),        # root, 4th, 5th, 9th
    # after Frasil's chords in the scale (in scale steps) and its voicings: plain tertian shapes, warm and open
    ("triad",    0, [0, 2, 4, 7]),        # close triad and the root's octave
    ("open",     0, [0, 4, 9, 11]),       # root, 5th, 10th, 12th: the second note an octave up
    ("wide",     0, [-7, 0, 2, 4]),       # the root an octave under a close triad
    ("seventh",  0, [0, 2, 4, 6]),        # the scale's own seventh chord
    ("add9",     0, [0, 4, 8, 9]),        # root, 5th, 9th, 10th
    ("sus2",     0, [0, 1, 4, 7]),        # root, 2nd, 5th, octave
]
# Harm (PERFORM page) at 0: the pleasing palette only - these voicings, diatonic and pentatonic scales, roots by
# 4ths / 5ths and 3rds (shared tones), keys moving by 5ths; turned up, more and more from the whole palette
PLEASING_FAMS = ["spread", "fifths", "sus", "triad", "open", "wide", "seventh", "add9", "sus2"]
PLEASING_SCALES = ["lydian", "dorian", "aeolian", "mixolyd", "ionian", "majpent", "minpent"]
MOVES_P = [3, -3, 4, -4, 3, -4, 2, -2, 2, -2, 5, -1]
MODS_P = [7, -7, 5, -5, 7, -5, 7, -7, 5, -5, 7, -7]

FLAVOURS = ["fm", "vox", "bow", "part", "fold", "pulsr", "saws", "pwm", "digi", "sync", "tine", "sine", "glass", "beat"]          # pad synthesis types
# texture output gains (calibrated so each texture sits near the others, see tools/ci_check.py)
TEXG = dict(RAIN_PAT=1.4, RAIN_PLOP=30.0, RAIN_G=1.0, MURMUR_G=1.5, MURMUR_X=0.3, ECHO_G=1.1, WHISPER_G=0.26,
            LEAVES_G=0.2, BROOK_G=0.5)
TEXTURES = ["rain", "wind", "ember", "chirp", "radio", "data", "buzz", "murmur", "echoes", "whisper",
            "leaves", "brook"]
DRONES = ["pure", "analog", "organ", "fm", "frost"]
CHARACTERS = ["clean", "chorus", "tape", "ring", "crush"]
# SETUP SOUNDS "raw": the pad types of the first demos (vox, partials, fold, pulsar), with no character effect
RAW_FLAVOURS = [FLAVOURS.index(n) for n in ("vox", "part", "fold", "pulsr")]
RAW_EXPR = "if(acr1<0.25, %d, if(acr1<0.5, %d, if(acr1<0.75, %d, %d)))" % tuple(RAW_FLAVOURS)
SUBMODES = ["pedal", "bassline", "both"]
INMODES = ["auto", "reso", "cloud", "tape", "ghost", "bands", "vocode", "morph"]
NOTE_NAMES = "C Db D Eb E F Gb G Ab A Bb B".split()
# chord names on the screen: the root and the triad the scale gives it (+ = augmented, 5 = Resolve's open fifths)
CHORD_SUFFIXES = ["", "m", "dim", "+", "sus", "5"]
CHORD_NAMES = [r + q for r in NOTE_NAMES for q in CHORD_SUFFIXES]

# chord-root moves in scale degrees (weighted by repetition): 4ths/5ths, steps, 3rds
MOVES = [3, -3, 1, -1, 2, 4, -2, 5, 3, -3, -4, 1]
# key changes in semitones (when the piece modulates by itself)
MODS = [7, -7, 5, -5, 3, -3, 4, -4, 2, -2, 8, -1]
# grain transpositions (cloud), consonant ratios
GRAIN_RATIOS = [1, 1, 0.5, 2, 1.5, 0.75, 1.3348, 2, 0.5, 1.25, 3, 0.6667]
FM_RATIOS = [1, 2, 3.5, 1.4142, 0.5, 2.7183, 1.5, 7]
PARTIAL_SETS = [
    [1, 2, 3, 4],             # harmonic
    [1, 3, 5, 7],             # odd (hollow, clarinet-ish)
    [1, 2.756, 5.404, 8.933],  # free bar
    [1, 2.03, 3.09, 4.17],    # stretched (piano-like)
    [1, 1.5, 2, 3],           # organ fifths
    [1, 2.414, 3.12, 4.6],    # bell-ish
]
BELL_SETS = [[1, 2.76, 5.40], [1, 2.0, 4.17], [1, 3.0, 6.2], [1, 1.5, 2.33]]
DRONE_INTERVALS = [1.5, 1.3333, 2.0, 1.75, 1.2]          # 5th, 4th, octave, harmonic 7th, just minor 3rd
RHYTHMS = [1, 1, 2, 0.5, 1.5]

# knob pages (aux cycles them): (label, value name, default)
PAGES = [
    [("Dens", "acdens", 0.5), ("Tide", "actide", 0.45), ("Colr", "accolor", 0.5), ("In", "acinput", 0.0)],
    [("Mix", "acrvmix", 0.45), ("Verb", "acrvtype", 0.0), ("Time", "acrvtime", 0.45), ("Tone", "acrvtone", 0.5)],
    [("Len", "aclen", 0.3), ("Weird", "acweird", 0.3), ("Mot", "acmotion", 0.5), ("Rhy", "acrhythm", 0.5)],
    # reverb sends per group, off .. full (50 % = the designed balance, 100 % = twice that)
    [("Drone", "acsndd", 0.5), ("Pads", "acsndp", 0.5), ("Bells", "acsndb", 0.5), ("Motn", "acsndm", 0.5)],
    [("Tex", "acsndt", 0.5), ("Cloud", "acsndc", 0.5), ("Atmo", "acsnda", 0.5), ("Inp", "acsndi", 0.5)],
    # layer levels, off .. +6 dB (50 % = the designed balance)
    [("Drone", "acmxd", 0.5), ("Sub", "acmxs", 0.5), ("Pads", "acmxp", 0.5), ("Bells", "acmxb", 0.5)],
    [("Motn", "acmxm", 0.5), ("Tex", "acmxt", 0.5), ("Cloud", "acmxc", 0.5), ("Atmo", "acmxa", 0.5)],
    # PERFORM: the whole sound at once - Sink (a low-pass over everything), Blur (into the reverb), Swell (fuller,
    # brighter, a little louder), Harm (0 = the pleasing harmony only; up = more adventurous relationships)
    [("Sink", "acsink", 0.0), ("Blur", "acblur", 0.0), ("Swell", "acswell", 0.0), ("Harm", "acharmx", 0.0)],
]
PAGE_NAMES = ["SHAPE", "SPACE", "PIECE", "SENDS 1", "SENDS 2", "MIX 1", "MIX 2", "PERFORM"]
MIX_KNOBS = 28       # knobs up to the end of the MIX pages (the PERFORM page is saved after the newer SETUP values)
NK = 32              # all the knobs (acparams)
SEND_KNOBS = 20      # knobs up to the end of the SENDS pages (the MIX pages are saved at the end of settings.txt)
# the send groups: knob value name -> the reverb send bus its sources throw to (pads are sent from the master)
#   (the notes you play use the pad synthesis types and share the Pads send)
SEND_BUS = {"acsndd": "ac-sendd", "acsndp": "ac-sendp", "acsndb": "ac-sendb", "acsndm": "ac-sendm",
            "acsndt": "ac-send", "acsndc": "ac-sendc", "acsnda": "ac-senda", "acsndi": "ac-sendi"}
FILE_KNOBS = 12      # knob values at the front of settings.txt (the SENDS page is stored after the SETUP values)

CLOUD_LEN = 352800        # 8 s at 44.1 kHz

# ---- form
ARCHETYPES = ["arch", "build", "waves", "twin", "journey"]
ROLES = ["emerge", "establish", "develop", "intensify", "climax", "break", "return", "dissolve"]
LAYERS = ["drone", "pad", "tex", "cloud", "bell", "motion"]
# chance that a layer plays in a section of each role
ROLE_MASK = [
    # drone pad  tex  cloud bell motion
    [1.0, 0.35, 0.8, 0.5, 0.3, 0.0],     # emerge
    [1.0, 1.0, 0.6, 0.4, 0.55, 0.2],     # establish
    [0.9, 1.0, 0.6, 0.6, 0.85, 0.6],     # develop
    [0.9, 1.0, 0.7, 0.7, 0.85, 0.9],     # intensify
    [1.0, 1.0, 0.8, 0.9, 0.8, 1.0],      # climax
    [0.4, 0.2, 0.9, 0.8, 0.6, 0.4],      # break
    [1.0, 1.0, 0.5, 0.5, 0.9, 0.4],      # return
    [1.0, 0.6, 0.7, 0.8, 0.45, 0.0],     # dissolve
]
ROLE_TIDE = [1.6, 1.2, 1.0, 0.75, 0.6, 1.5, 1.0, 2.0]      # x the time between chord changes
ROLE_TEMPO = [0.92, 1.0, 1.0, 1.06, 1.1, 0.95, 1.0, 0.85]  # x the piece tempo
ROLE_PULSE = [0.0, 0.1, 0.15, 0.3, 0.35, 0.1, 0.15, 0.0]   # drone pulse depth on the bar
AWAY = [5, 7, -3, 2, 4, -4, -5, 3]                         # key areas away from home (semitones)
EUCLID = [(3, 8), (5, 8), (5, 12), (7, 16), (5, 13), (4, 11), (7, 12), (3, 7), (5, 16), (9, 16)]
METERS = [4, 4, 3, 5, 6, 7]
# tempo ranges (SETUP page 3): name, lowest and highest piece tempo in BPM. Above HALFTIME the slow layers
# (pad breathing, bells, the drone's bar swell) feel the beat at half speed and the arpeggio counts in 8ths.
TEMPOS = [("ambient", 40, 72), ("slow", 24, 48), ("wide", 30, 110), ("pulse", 60, 100), ("fast", 90, 140)]
HALFTIME = 84
MOTION_RATIOS = [1, 2, 3, 4.5, 0.5, 1.5]
BREATH_PERIODS = [7, 9, 11, 13]       # pad breathing cycles, in half-bars: they phase against each other

# ---- reverb
VERBS = ["auto", "bloom1", "bloom2", "hall", "shimmer"]
# Bloom (after the Alesis MidiVerb II Bloom programs, via Conduit's bloom.c): delays at the unit's 23437.5 Hz
BLOOM_RATE = 23437.5
BLOOM_CHAIN = [13, 83, 116, 239, 339, 481, 555, 823, 999, 1100, 1347, 1563, 1841, 2001, 2083]
BLOOM_LEFT = [249, 48, 21]
BLOOM_RIGHT = [147, 43, 55]
BLOOM_PRE = 2000                       # Bloom 2's pre-delay (85 ms)
HALL_MS = [43.7, 53.9, 61.3, 71.1, 83.9, 97.3, 109.7, 127.1]

# ---- atmospheres, stereo scenes, preferences
ATMOS_NAMES = ["haze", "deep", "space", "night", "tides"]
ATMOS_ROLE = [0.85, 0.4, 0.3, 0.4, 0.5, 0.85, 0.45, 0.9]     # chance per section role, in pieces that have one
SCENES = ["spread", "split", "center", "circle", "mirror"]
# per scene: 4 pad homes, bells centre / spread, motion centre / spread, cloud spread, orbit depth x
SCENE_DATA = [
    [0.08, 0.36, 0.64, 0.92, 0.5, 0.8, 0.5, 0.76, 0.96, 1.0],
    [0.08, 0.18, 0.28, 0.38, 0.8, 0.3, 0.8, 0.3, 0.6, 0.6],
    [0.38, 0.46, 0.54, 0.62, 0.5, 0.95, 0.5, 0.9, 0.96, 0.35],
    [0.2, 0.4, 0.6, 0.8, 0.5, 0.9, 0.5, 0.9, 0.96, 2.0],
    [0.12, 0.32, 0.68, 0.88, 0.5, 0.85, 0.5, 0.85, 0.8, 0.5],
]
# the scenes each section role chooses from (3 picks)
SCENE_ROLE = [[2, 0, 2], [0, 4, 0], [1, 4, 0], [3, 1, 3], [3, 0, 4], [1, 2, 1], [0, 4, 0], [2, 3, 2]]
# preferences: the electronic and bell-like sounds come up more often
FLAVOUR_WEIGHTS = [1.6, 0.5, 0.5, 1.3, 0.6, 1.0, 1.3, 1.3, 1.2, 1.1, 1.8, 1.3, 1.3]
# the engines that play the bells (the motif) and the motion (the arpeggio), selectable in SETUP page 9 for each:
# bars = the struck 3-partial bars (the bells' own), fm = the FM pings (the motion's own), blip = a filtered analog
# blip, wood = a wooden bar (marimba / woodblock), wave = a glassy wavetable, metal = a vibraphone-like metallophone
STRIKES = ["bars", "fm", "blip", "wood", "wave", "metal"]
# auto: what a piece picks (bells lean to bars and metal, motion to the FM pings and blips)
BELL_ENGINE_WEIGHTS = [2.2, 0.4, 0.5, 0.8, 0.9, 1.4]
MOTION_ENGINE_WEIGHTS = [0.4, 2.0, 1.5, 0.9, 0.9, 0.5]
# per engine and layer: output gain, calibrated against the layer's own engine (bars, fm) halfway between equal
# level and equal peaks (the short, spiky wood and blip would be too loud at equal level) - see tools/ci_check.py;
# then the decay in ms on the bells, and the motion's decay as a factor of its piece decay (250-950 ms)
STRIKE_GAIN = dict(bell=dict(bars=1.0, fm=0.8, blip=2.8, wood=1.0, wave=1.05, metal=1.2),
                   motion=dict(bars=14.0, fm=1.0, blip=18.0, wood=7.0, wave=9.0, metal=10.0))
STRIKE_DEC = dict(bars=5200, fm=2600, blip=900, wood=700, wave=3200, metal=3600)
STRIKE_MDEC = dict(bars=1.0, fm=1.0, blip=0.8, wood=0.6, wave=1.2, metal=1.4)
# the glassy wavetables (harmonic number: amplitude), shared by the glass pad and the wave engine
WAVETABLES = dict(acwtA={1: 1, 2: 0.25, 3: 0.4, 4: 0.08, 5: 0.22, 7: 0.15, 9: 0.1},
                  acwtB={1: 0.6, 3: 0.15, 4: 0.35, 6: 0.3, 8: 0.38, 11: 0.25, 13: 0.2, 16: 0.12})
FM_RATIO_WEIGHTS = [1, 1, 2, 2, 0.7, 2, 1, 1.5]
PARTIAL_WEIGHTS = [1, 0.8, 2, 1, 0.8, 2]


def pick_table(weights, n=40):
    """a table of n slots, each index repeated in proportion to its weight"""
    tot = sum(weights)
    counts = [max(1, round(n * w / tot)) for w in weights]
    # rounding can miss n: then the largest remainders decide (every slot read as int(r*n) must exist)
    while sum(counts) != n:
        err = [c - n * w / tot for c, w in zip(counts, weights)]
        if sum(counts) > n:
            counts[max((i for i in range(len(counts)) if counts[i] > 1), key=lambda i: err[i])] -= 1
        else:
            counts[min(range(len(counts)), key=lambda i: err[i])] += 1
    out = []
    for i, c in enumerate(counts):
        out += [i] * c
    return out
