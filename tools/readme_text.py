PATCH_README = """AMBLE  -  generative ambient composer for the Organelle M
=========================================================

Every start (and the top B key) invents a new piece: key and scale (including
just, harmonic-7th, slendro and pelog), chord voicings, a palette of pad
synthesis types, tempo and meter, motif, textures, reverb and a FORM.

COMPOSE (default): a 5-30 minute piece. The form follows one of 5 shapes
(arch, slow build, waves, two peaks, journey) over 6-12 sections, each with a
role: emerge, establish, develop, intensify, climax, break, return, dissolve.
Sections change the key (out and home again), tempo, harmonic pace, the
layers that play, the motif (inverted, raised, restored) and the reverb.
The return section replays the opening chord progression. At the end it
fades out: B for a new piece.
DRIFT: endless sections, for backing a performance.

LAYERS AND THEIR RHYTHMS (one clock, 40-72 BPM, meter 3-7 per piece)
  Drone    tonic, beating twin, interval, sub, breath tube; swells on each
           bar in intense sections
  Pads     4 voices, 6 synthesis types (fm, vox, bow, part, fold, pulsr),
           voice-led; each breathes in its own cycle (7, 9, 11, 13 half-bars)
           so they phase against each other
  Motion   Euclidean patterns (e.g. 5 in 8, 7 in 16) arpeggiating the chord on
           FM pings, swing, tempo echoes
  Bells    the motif, phrased in beats with rubato
  Textures rain, wind, embers, chirps (random weather)
  Cloud    grains of the recent sound or your input; locked to the beat in
           intense sections, free otherwise

REVERB (page SPACE)
  Bloom 1 / Bloom 2: after the Alesis MidiVerb II Bloom programs (45, 49), as
  in Conduit - the sound swells for half a second through 15 diffusers before
  it rings out. Hall: 8-line FDN. Shimmer: Hall with an octave in the loop.
  Auto lets the piece choose (and the climax may shimmer); each section
  change makes the reverb bloom up.

KNOBS (aux cycles the pages; knobs pick up smoothly)
  SHAPE  1 Dens  how much plays     2 Tide  time between chord changes
         3 Colr  brightness         4 In    external audio amount
  SPACE  1 Mix   reverb mix         2 Verb  Auto/Bloom1/Bloom2/Hall/Shimmer
         3 Time  1.5-30 s           4 Tone  damping
  PIECE  1 Len   5-30 min           2 Weird FM, folding, key changes
         3 Mot   breathing, drift   4 Rhy   motion layer, swing, pulse

PLAYING IT
  Standalone, the Organelle keys PLAY NOTES (4 voices in the piece's own
  synthesis type). Functions are aux + key.
  When an external controller plays (DM48X, any keyboard), it takes over:
  the keys become function keys without aux. After 2 minutes with no
  external notes the keys play again.
  MPE: each note on its own channel, per-note bend (48 semitones; channel 1:
  2), breath = CC 2 / CC 11 / channel or poly pressure. With breath the notes
  follow your breath (level and brightness).

THE COMPOSER LISTENS
  - what you hold (or sing) pulls the next chord to contain it
  - a note held 6 s becomes the new key centre
  - breath raises the energy (more layers), and while you play a section
    waits for you (up to 3 x 30 s)
  - silence: the piece leads

FUNCTION KEYS (aux + key standalone, plain keys with external MIDI)
  Low octave C..B   next key centre
  C   COMPOSE / DRIFT          C#  chord change now    D  next section
  D#  drone on/off   E pads   F textures   F# cloud   G bells
  G#  capture 8 s of input (cloud + a memory)
  A   input mode: auto / reso / cloud / tape / ghost / bands
  A#  HOLD: freeze the reverb tail and the cloud
  B   new piece
  Aux alone: next knob page.  Footswitch: chord change now

AUDIO INPUT (In knob = amount; samples, guitar, harmonica, voice, field
recordings). Gate and automatic gain, then Amble listens for pitch, attacks
and noisiness and calls it pitched, plucked or texture (screen line 5).
  auto   pitched: chord strings ring with you, grains retuned to the chord,
         your pitch steers the harmony; plucked: attacks ring bells, the
         strings ring lightly; texture: tuned bands play the chord
  reso   4 comb strings tuned to the chord
  cloud  your sound feeds the granular cloud
  tape   long wobbling echoes
  ghost  unheard: loudness brightens, attacks ring bells
  bands  8 narrow bands on the chord tones (field recordings sing)
MEMORIES: while the piece develops Amble keeps 8 s of what you played (up to
4). Break, return and dissolve sections bring them back: reversed, slowed,
or retuned to the chord.

THE SCREEN (a live score)
  top strip   the form: a bar per section (height = energy), the current
              one inverted, a playhead (DRIFT: energy and progress)
  line 2      key and scale; time left (elapsed in DRIFT); messages
  left        the 4 pad voices as dots on a pitch ladder (they glide),
              your held notes as boxes, tonic ticks, breath bar
  middle      meters: drone, pads, textures, cloud, bells, motion,
              reverb, and the input level
  right       the motion layer's Euclidean pattern with its cursor, the
              tempo, the reverb (B1 B2 HALL SHIM)
  bottom      section role and voicing; K = keys play, M = external MIDI,
              E = following an external clock; FIN at the end
  Turning a knob shows its page for 2 s.

SETUP (hold aux 1 s; aux tap = page 2; hold aux 1 s to leave and save)
  1 MIDI out   off / clock / clock+notes / notes
     clock: 24 a beat at the piece's tempo, Start/Stop with the piece
     notes: chords on the base channel, drone +1, bells +2, motion +3
  2 Sync       internal / follow clock (external clock drives the rhythm;
               Start restarts the bar, Stop pauses the pulse layers)
  3 Keys       auto / play notes / functions
  4 Bloom      clean / vintage (13-bit, as the unit)
  page 2: Follow you (how much chords follow what you play), MPE bend
  range (12/24/48/96), MIDI out base channel, breath curve.
  Knob values and SETUP are saved in settings.txt.

LED: blue composing, green drifting, white flash on chord changes.
seed.txt counts start-ups so no two sessions begin the same way.

Amble is GPL-3. The Bloom reverb follows Conduit's bloom.c, after thement's
midiverb_emulator analysis of the MidiVerb II.
"""
