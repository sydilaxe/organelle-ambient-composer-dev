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

LAYERS AND THEIR RHYTHMS (one clock, 40-72 BPM by default, meter 3-7)
  Drone    one of 4 designs per piece (the break may switch): pure (tonic,
           beating twin, interval, breath tube), analog (saws and a square
           through a slow resonant sweep), organ (drawbars, rotary shimmer),
           fm (an electric growl); swells on each bar in intense sections
  Sub      a sine under everything, softly saturated so small speakers hear
           it: the pedal an octave under the tonic, the chord root as a
           bass line, or both (alternating by section)
  Pads     4 voices, 11 synthesis types: fm, vox, bow, part, fold, pulsr,
           saws (detuned analog ensemble), pwm (Juno-like), digi (ring mod,
           bit-crush), sync (hard-sync sweep), tine (an electric-piano bell
           that strikes itself); most are stereo inside. The electronic and
           bell-like types come up most often. Voice-led; each breathes in
           its own cycle (7, 9, 11, 13 half-bars) so they phase
  Character  per piece on the pads: clean, chorus, tape (wow, saturation,
           hiss), ring, crush
  Motion   Euclidean patterns (e.g. 5 in 8, 7 in 16) arpeggiating the chord on
           FM pings, swing, tempo echoes
  Bells    the motif, phrased in beats with rubato
  Textures rain, wind, embers, chirps, radio (soft drifting static, whistles), data (blip
           bursts), buzz (electric hum on the tonic)
  Cloud    grains of the recent sound or your input; locked to the beat in
           intense sections, free otherwise
  Atmosphere (about half the pieces, mostly in emerge, break, dissolve):
           haze (air shimmering on the chord), deep (rumble, distant
           thunder), space (air ringing in combs tuned to the chord), night
           (distant insects), tides (waves washing across the field)

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
  SENDS 1  reverb sends: 1 Drone (and sub)  2 Pads (and notes you play)
           3 Bells  4 Motion
  SENDS 2  reverb sends: 1 Textures  2 Cloud  3 Atmosphere  4 Input
  Each send runs from off (dry) to full; 50 % is the designed balance.
  Mix (SPACE) is the overall reverb return.

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
  A   input mode: auto / reso / cloud / tape / ghost / bands / vocode /
      morph
  A#  START / STOP: stop fades out and freezes the piece where it is
      (section, chord, time left); start fades back in and goes on.
      After FIN it starts a new piece. MIDI Start / Stop do the same
      when Sync = follow clock.
  B   new piece
  FREEZE (the reverb tail and the cloud): aux + F# with an external
      controller; standalone, aux + F# twice quickly
  Aux alone: next knob page.  Footswitch: chord change now

AUDIO INPUT (In knob = amount, always 0 when Amble loads; samples, guitar,
harmonica, voice, field recordings). Gate and automatic gain, then Amble listens for pitch, attacks
and noisiness and calls it pitched, plucked or texture (screen line 5).
  auto   pitched: chord strings ring with you, grains retuned to the chord,
         your pitch steers the harmony; plucked: attacks ring bells, the
         strings ring lightly; texture: tuned bands play the chord
  reso   4 comb strings tuned to the chord
  cloud  your sound feeds the granular cloud
  tape   long wobbling echoes
  ghost  unheard: loudness brightens, attacks ring bells
  bands  8 narrow bands on the chord tones (field recordings sing)
  vocode your sound speaks through a synth choir singing the chord
         (10-band vocoder; auto mode vocodes pitched input in some pieces)
  morph  your sound speaks through the pads themselves
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
  input       while external audio plays the right column shows it instead:
              6 s of its level as a waveform (onsets ticked above), the
              input mode and what Amble hears (pitch / pluck / textr), a dot
              while it records a memory; a pitch it hears is a line across
              the pitch ladder. The rhythm column returns 5 s after.
  bottom      section role and voicing; K = keys play, M = external MIDI,
              E = following an external clock; FIN at the end
  Turning a knob shows its page for 6 s.

SETUP (hold aux 1 s; aux tap = next page (7); hold aux 1 s to leave, save)
  1 MIDI out   off / tempo only / tempo+notes / notes only
     tempo: MIDI clock, 24 a beat at the piece's tempo, Start/Stop with it
     notes, by channel from the base channel (page 2):
       base  the chord as voiced (held)     +1  the tonic (held)
       +2    bells                          +3  the motion arpeggio
       +4    the bass (the sub's note)      +5  the ARP CHORD: the chord in
             close position from the Arp octave - for arpeggiators
  2 Sync       internal / follow clock (external clock drives the rhythm;
               Start restarts the bar and the piece, Stop stops it)
  3 Keys       auto / play notes / functions
  4 Bloom      clean / vintage (13-bit, as the unit)
  page 2: Follow you (how much chords follow what you play), MPE bend
  range (12/24/48/96), MIDI out base channel, breath curve.
  page 3: Output (stereo wide / mono - for mono rigs and external effects /
  split - pads and drone left, everything else right, as mono stems),
  Width (50-150 %), Pan motion (how far the voices travel), Tempo range:
  ambient 40-72, slow 24-48, wide 30-110, pulse 60-100, fast 90-140. Above
  84 BPM bells, breathing and the drone swell move at half time.
  page 4: MIDI notes (all / harmony: no bells or motion / arp only),
  Arp octave (C1-C5, where the arp chord starts), CPU (the load now and
  the guard's level), CPU guard on/off.
  page 5, SOUNDS (each auto = the piece chooses; a choice applies at
  once, crossfaded, and stays for every section - for auditioning):
    Pads       auto / raw / one type for all four voices: fm vox bow part
               fold pulsr saws pwm digi sync tine. raw = the dry, buzzy
               types of the first demos (vox, part, fold, pulsr), no
               character effect
    Drone      auto / pure / analog / organ / fm
    Texture    auto / rain / wind / ember / chirp / radio / data / buzz
    Character  auto / clean / chorus / tape / ring / crush
  page 6, MUSIC (a fixed choice stays: no modulation, no scale change):
    Key        auto / C .. B (applies at once, with a chord change)
    Scale      auto / one of the 16 scales
    Chords     auto / one voicing: spread quartal cluster fifths ninths
               spectral mirror sus
    Pulse      off / gentle / normal / strong - the drone and sub swell
               on every bar
  page 7, MIDI IN:
    Notes to   what MIDI notes and the keys play: voice (the live voice) /
               chords (your held notes are the pad chord) / drone (drone
               and sub on your note) / bells (a bell per note) / cloud
               (each note tunes a grain stream)
    Breath to  voice+piece / voice / density / brightness / reverb /
               swell (the whole level, like an expression pedal)
    Breath CC  2 + 11 / 2 / 11 / 1 (mod) / 74 / touch only (pressure
               always counts)
    Breath in  the breath level arriving now

CPU GUARD: Amble measures its own load each second. Above 78 % it gets
lighter in steps ("CPU high - lighter"): 1 cloud and atmosphere off,
2 textures and the pad character off, 3 the automatic vocoder off. Below
50 % for 20 s it steps back. Nothing else changes: the pads, drone, sub,
bells, motion and reverb always keep their full sound. SETUP page 4 can
turn it off. pd-opts.txt asks the Organelle for a 25 ms audio buffer (its
default is 6 ms), so brief spikes don't crackle; lower the number for less
delay when playing live, raise it if you still hear crackles. Heavy changes (a new piece, a new section, a chord) are
spread over a few milliseconds so they don't click.

STEREO SCENES: each section places the voices - spread (across the
field), split (pads left, bells and motion right), center (a focused core,
a wide halo), circle (everything orbits wide), mirror (pairs mirrored).
STEREO: the bass and sub stay centred; above them the drone's twin and
interval orbit in opposite directions, its breath tubes drift, each pad
voice has its own place and slowly orbits around it, grains and bells land
anywhere, the motion arpeggio sweeps across, the reverbs are decorrelated.
Width grows with the form (narrower as a piece emerges, widest at the
climax). It stays mono-compatible: summed to mono it loses about 1 dB.
  Knob values and SETUP are saved in settings.txt.

LED: blue composing, green drifting, white flash on chord changes.
seed.txt counts start-ups so no two sessions begin the same way.

Amble is GPL-3. The Bloom reverb follows Conduit's bloom.c, after thement's
midiverb_emulator analysis of the MidiVerb II.
"""
