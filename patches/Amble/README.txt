AMBLE  -  generative ambient composer for the Organelle M
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

KEYS
  Low octave C..B   next key centre
  C   COMPOSE / DRIFT          C#  chord change now    D  next section
  D#  drone on/off   E pads   F textures   F# cloud   G bells
  G#  capture 8 s of input into the cloud
  A   input mode: reso / cloud / tape / ghost
  A#  HOLD: freeze the reverb tail and the cloud
  B   new piece
  Footswitch: chord change now

INPUT MODES (In knob = amount)
  reso   your sound rings 4 strings tuned to the chord
  cloud  your sound feeds the granular cloud
  tape   long wobbling echoes
  ghost  unheard: your loudness brightens the pads, attacks ring bells

LED: blue composing, green drifting, white flash on chord changes.
seed.txt counts start-ups so no two sessions begin the same way.

Amble is GPL-3. The Bloom reverb follows Conduit's bloom.c, after thement's
midiverb_emulator analysis of the MidiVerb II.
