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
]

FLAVOURS = ["fm", "vox", "bow", "part", "fold", "pulsr", "saws", "pwm", "digi", "sync"]          # pad synthesis types
TEXTURES = ["rain", "wind", "ember", "chirp", "radio", "data", "buzz"]
DRONES = ["pure", "analog", "organ", "fm"]
CHARACTERS = ["clean", "chorus", "tape", "ring", "crush"]
SUBMODES = ["pedal", "bassline", "both"]
INMODES = ["auto", "reso", "cloud", "tape", "ghost", "bands", "vocode", "morph"]
NOTE_NAMES = "C Db D Eb E F Gb G Ab A Bb B".split()

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
]
PAGE_NAMES = ["SHAPE", "SPACE", "PIECE"]

CLOUD_LEN = 352800        # 8 s at 44.1 kHz

# ---- form
ARCHETYPES = ["arch", "build", "waves", "twin", "journey"]
ROLES = ["emerge", "establish", "develop", "intensify", "climax", "break", "return", "dissolve"]
LAYERS = ["drone", "pad", "tex", "cloud", "bell", "motion"]
# chance that a layer plays in a section of each role
ROLE_MASK = [
    # drone pad  tex  cloud bell motion
    [1.0, 0.35, 0.8, 0.5, 0.15, 0.0],    # emerge
    [1.0, 1.0, 0.6, 0.4, 0.4, 0.2],      # establish
    [0.9, 1.0, 0.6, 0.6, 0.7, 0.6],      # develop
    [0.9, 1.0, 0.7, 0.7, 0.7, 0.9],      # intensify
    [1.0, 1.0, 0.8, 0.9, 0.8, 1.0],      # climax
    [0.4, 0.2, 0.9, 0.8, 0.6, 0.4],      # break
    [1.0, 1.0, 0.5, 0.5, 0.9, 0.4],      # return
    [1.0, 0.6, 0.7, 0.8, 0.3, 0.0],      # dissolve
]
ROLE_TIDE = [1.6, 1.2, 1.0, 0.75, 0.6, 1.5, 1.0, 2.0]      # x the time between chord changes
ROLE_TEMPO = [0.92, 1.0, 1.0, 1.06, 1.1, 0.95, 1.0, 0.85]  # x the piece tempo
ROLE_PULSE = [0.0, 0.1, 0.15, 0.3, 0.35, 0.1, 0.15, 0.0]   # drone pulse depth on the bar
AWAY = [5, 7, -3, 2, 4, -4, -5, 3]                         # key areas away from home (semitones)
EUCLID = [(3, 8), (5, 8), (5, 12), (7, 16), (5, 13), (4, 11), (7, 12), (3, 7), (5, 16), (9, 16)]
METERS = [4, 4, 3, 5, 6, 7]
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
