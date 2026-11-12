PATCH_README = """AMBIENT COMPOSER  -  Organelle M patch
=====================================

A generative ambient instrument. Every time it starts (and every time you
press the top B key) it invents a new piece: a key and scale (including just,
harmonic-7th, slendro and pelog tunings), two chord-voicing families, a palette
of synthesis types, FM and partial ratios, drone interval, bell tuning,
textures and a form. It runs forever as a backing track (DRIFT), or composes a
whole piece with a beginning, a peak and an ending (COMPOSE).

SOUND SOURCES
  Pads (4 voices, voice-led chords that change one voice at a time):
    fm    - FM with a per-piece ratio (some inharmonic)
    vox   - saw through two drifting vowel formants
    bow   - a string kept ringing by filtered noise
    part  - 4 sine partials (harmonic, odd, bar, stretched, organ, bell sets)
            that swell independently
    fold  - wavefolded sine, ring-modulated by its sub-octave
    pulsr - pulsar synthesis: windowed bursts with a drifting formant
  Drone  - tonic + beating twin + per-piece interval + sub + breathing tube
  Textures - rain (rising water-drop bubbles on chord tones), wind (noise
            whistling through bands tuned to the chord), embers (crackle and
            wood knocks), chirps (creature calls in bursts)
  Cloud  - 4 granular streams over an 8 s buffer of the patch's own recent
           sound (or your input), transposed by chord-friendly ratios,
           sometimes reversed
  Bells  - a 5-note motif that mutates as it repeats, on struck bars
  Space  - 4-line FDN reverb, 2.5 to 28 s

KNOBS (aux button switches the page; knobs pick up smoothly, nothing jumps)
  Page SHAPE:  1 Dens   how many layers play (with the section's energy)
               2 Tide   time between chord changes (6 s .. 90 s)
               3 Colr   brightness of everything
               4 In     external audio amount (see input modes)
  Page SPACE:  1 Space  reverb size and mix
               2 Weird  FM index, folding, key changes, modal mixture,
                        reversed grains
               3 Len    length of a composition (3 .. 40 min)
               4 Mot    breathing and drift of the pad voices

KEYS
  Low octave C..B   next key centre (the next change modulates there)
  C   DRIFT / COMPOSE (COMPOSE starts a new arc of 5-8 sections)
  C#  chord change now          D   next section now
  D#  drone on/off   E pads   F textures   F# cloud   G bells
  G#  capture 8 s of the input into the cloud, then freeze it
  A   input mode: reso / cloud / tape / ghost
  A#  freeze / unfreeze the cloud buffer
  B   new piece (new seed)
  Footswitch: chord change now

INPUT MODES (In knob = amount)
  reso   your sound rings 4 comb "strings" tuned to the current chord;
         they glide when the chord changes
  cloud  your sound feeds the granular cloud, pitched into the harmony
  tape   long wobbling echoes that darken and saturate
  ghost  you are not heard: your playing drives the piece - its loudness
         brightens the pads, each attack rings the next bell note and
         sometimes changes the chord

SCREEN
  1  DRIFT <mood> seed N   |  COMP <section> of <n> <stage>  |  FIN
  2  key, scale, voicing family
  3  the 4 pad synthesis types and the main texture (and messages)
  4-5  the knob page

LED: green drifting, blue composing, white flash on each chord change.
A composition fades out at its end; press B for a new piece or C to drift.
seed.txt counts start-ups so that no two sessions begin the same way.
"""
