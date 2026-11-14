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

LAYERS AND THEIR RHYTHMS (one clock, 40-72 BPM by default, meter 3-7)
  Drone    one of 4 designs per piece (the break may switch): pure (tonic,
           beating twin, interval, breath tube), analog (saws and a square
           through a slow resonant sweep), organ (drawbars, rotary shimmer),
           fm (an electric growl); swells on each bar in intense sections
  Sub      a sine under everything, softly saturated so small speakers hear
           it: the pedal an octave under the tonic, the chord root as a
           bass line, or both (alternating by section)
  Pads     4 voices, 13 synthesis types: fm, vox, bow, part, fold, pulsr,
           saws (detuned analog ensemble), pwm (Juno-like), digi (ring mod,
           bit-crush), sync (hard-sync sweep), tine (an electric-piano bell
           that strikes itself), sine (harmonic sines), glass (glassy
           wavetables); most are stereo inside. The electronic and
           bell-like types come up most often. Voice-led; each breathes in
           its own cycle (7, 9, 11, 13 half-bars) so they phase
  Character  per piece on the pads: clean, chorus, tape (wow, saturation,
           hiss), ring, crush
  Motion   Euclidean patterns (e.g. 5 in 8, 7 in 16) arpeggiating the chord,
           swing, tempo echoes; on FM pings or another engine (below)
  Bells    the motif, phrased in beats with rubato, on struck bars or another
           engine. Engines (both layers, SETUP page 9): bars, fm, blip (a
           filtered analog blip), wood (marimba-like), wave (a glassy
           wavetable), metal (a vibraphone-like metallophone)
  Textures rain (hiss, patter, plops), wind, embers, chirps, radio (static and a
           tuning whistle), data (blip bursts), buzz (electric hum on the tonic),
           murmur (ghostly distant voices), echoes (alien blips in bending
           echoes), whisper, leaves (rustling trees), brook (babbling water)
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

KNOBS (low C..F# open the pages, aux cycles them; knobs pick up smoothly)
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
  MIX 1  levels: 1 Drone  2 Sub  3 Pads  4 Bells
  MIX 2  levels: 1 Motion  2 Textures  3 Cloud  4 Atmosphere
  Each level runs from silent to +6 dB; 50 % is the designed balance.
  PERFORM  1 Sink (everything under a low-pass)  2 Blur (into the reverb)
           3 Swell (fuller, brighter)  4 Harm (0 = pleasing harmony only;
           up = other relationships drift in)

PLAYING IT
  Amble starts READY and silent: choose COMPOSE or DRIFT (aux + top A#),
  then top A# starts it. You play from MIDI controllers (DM48X, any
  keyboard); the Organelle keys are always functions, one press each.
  MPE: each note on its own channel, per-note bend (48 semitones; channel 1:
  2), breath = CC 2 / CC 11 / channel or poly pressure. With breath the notes
  follow your breath (level and brightness).

THE COMPOSER LISTENS
  - what you hold (or sing) pulls the next chord to contain it
  - a note held 6 s becomes the new key centre
  - breath raises the energy (more layers), and while you play a section
    waits for you (up to 3 x 30 s)
  - silence: the piece leads

THE ORGANELLE KEYS (functions; aux + a low key = that SETUP page, C = 1)
  Low octave
  C   SHAPE page   C#  SPACE page   D  PIECE page
  D#  MIX 1 page   E   MIX 2 page   F  SENDS (again: SENDS 2)   F#  PERFORM
  G   ROOT: hold it and press a key, play a MIDI note or turn knob 1 -
      that note is the next key (while G is up, MIDI notes play)
  G#  RESOLVE: the tonic as open fifths, held - no modulation, no
      dissonant chords - until pressed again (a CC mapped to resolve
      holds it from a pedal)
  A   tap: chord change now (to the next chord shown); hold: pick another
      next chord, again every 0.7 s - let go when you like it
  A#  next section
  B   hold section (stays past its length; again: moves on)
  Top octave
  C..G  layers: drone, sub, pads, bells, motion, textures, atmosphere,
        cloud - tap: in (if silent) / out (if playing); aux + tap: auto
  G#  input mode: auto / reso / cloud / tape / ghost / bands / vocode /
      morph; aux: capture 8 s of input (cloud + a memory)
  A   FREEZE: the reverb tail and the cloud hold still; again to release.
      Aux + A: ANCHOR - first sets it, then glides everything back to it
      (held: anchors here anew)
  A#  START / STOP: stop fades out (8 s) and freezes the piece where it is
      (section, chord, time left); start goes on. After FIN it starts a
      new piece. MIDI Start / Stop do the same when Sync = follow clock.
      Aux: COMPOSE / DRIFT
  B   tap: new piece; hold: COMPARE (the slot as saved); hold + a key: load
      that slot (low C..B = 1-12, top C..D# = 13-16), with aux: save there;
      aux + tap: the SAVES page. Empty slots 1-6: factory pieces
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
  line 2      the chord now > the next chord; a bar under it shrinks to
              the change; messages
  left        the 4 pad voices as dots on a pitch ladder (they glide),
              your held notes as boxes, tonic ticks, breath bar
  voices      a row (Dr Sb Pd Bl Mo Tx At Cl): two letters while one
              sounds, a dot while it rests, a dash when it's out
  right       the motion layer's Euclidean pattern with its cursor, the
              tempo
  input       while external audio plays the right column shows it instead:
              its level as a waveform (onsets ticked above), the input mode
              (in auto: what Amble hears - pitch / pluck / textr), a dot
              while it records a memory; a pitch it hears is a line across
              the pitch ladder. The rhythm column returns 5 s after.
  bottom      key and scale, the section's role (or HOLD / FRZ);
              READY / STOPPED, or FIN at the end
  Turning a knob shows its page for 6 s.
THE MIX VIEW (while a MIX or SENDS page is open)
  a bar per voice: the level now, the knob as a tick, two letters below
  (the four the knobs turn underlined); a dot on top = on (a layer key), a
  dash at the foot = out; the column a knob turns is framed with its value

SETUP (hold aux 1 s, or aux + a low key; aux tap = next page (21); hold aux
1 s to leave, save)
  1 MIDI out   off / tempo only / tempo+notes / notes only
     tempo: MIDI clock, 24 a beat at the piece's tempo, Start/Stop with it
     notes, by channel from the base channel (page 2):
       base  the chord as voiced (held)     +1  the tonic (held)
       +2    bells                          +3  the motion arpeggio
       +4    the bass (the sub's note)      +5  the ARP CHORD: the chord in
             close position from the Arp octave - for arpeggiators
  2 Sync       internal / follow clock (external clock drives the rhythm;
               Start restarts the bar and the piece, Stop stops it)
  3 Mode       COMPOSE / DRIFT (the next piece; saved)
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
               fold pulsr saws pwm digi sync tine sine glass. raw = the dry, buzzy
               types of the first demos (vox, part, fold, pulsr), no
               character effect
    Drone      auto / pure / analog / organ / fm
    Texture    auto / rain / wind / ember / chirp / radio / data / buzz /
               murmur / echoes / whisper / leaves / brook
    Character  auto / clean / chorus / tape / ring / crush
  page 6, MUSIC (a fixed choice stays: no modulation, no scale change):
    Key        auto / C .. B (applies at once, with a chord change)
    Scale      auto / one of the 16 scales
    Chords     auto / one voicing: spread quartal cluster fifths ninths
               spectral mirror sus
    Pulse      off / gentle / normal / strong - the drone and sub swell
               on every bar
  page 7, MIDI IN:
    Notes to   what MIDI notes play: voice (the live voice) /
               chords (your held notes are the pad chord) / drone (drone
               and sub on your note) / bells (a bell per note) / cloud
               (each note tunes a grain stream)
    Breath to  voice+piece / voice / density / brightness / reverb /
               swell (the whole level, like an expression pedal)
    Pressure to  what channel / poly pressure does (a target, below)
    Breath in  the breath level arriving now
  page 8, CC MAP (knob 1 picks a CC: 1 2 7 11 64 71 74; knob 2 its target):
    targets    off / breath (into Breath to) / vibrato / voice tone /
               voice level / voice type / hold (sustain) / density /
               colour / reverb / swell / motion / resolve. Voice tone and level act
               per note on the CC's channel (MPE; channel 1 = all).
    defaults   1 vibrato, 2 7 11 breath, 64 hold, 71 off, 74 voice tone
    Last CC    the last CC in and its value
    Vib rate   3-8 Hz
  page 9, VOICES (auto = the piece's; a choice applies at once):
    Bells      auto / bars / fm / blip / wood / wave / metal
    Motion     auto / bars / fm / blip / wood / wave / metal
    Glide      off / fast / short / medium / long / slow - how the pad
               voices slide to a new chord (slow = up to 75 % of the time
               between changes; off = they jump, all together)
    Sub        auto / pedal / root / both
  page 10, FORM:
    Form       auto / arch / build / waves / twin / journey / custom (your
               sections, pages 11-12)
    Tempo      auto / a fixed tempo 40-140 bpm
    Meter      auto / 3-7 beats
    Atmos      auto / one atmosphere
  page 11, SECTIONS (editing one turns the form to custom):
    Section    now (follows the playing section) / 1-12
    Role       the section's role, or end (the piece ends there)
    Length     short / normal / long
    Pads       the section's pad type (auto = SOUNDS)
  page 12, SECTION MIX:
    Section    now / 1-12      Layer  drone .. cloud
    Play       auto / off / on / in 1/4, 1/2, 3/4 (silent, then it swells in
               to its level) / out 1/4, 1/2, 3/4
    Level      0-200 % in this section (on top of MIX)
  page 13, SAVES (also aux + top B): 16 slots in saves.txt (an update
  keeps them). Slot (its name); Save - turn knob 2 fully up; Load - turn
  knob 3 fully up (stopped: it waits ready; playing: it plays now); Name
  (auto = the key and scale, or a word).
  page 14, LIVE:
    Mix CCs    off / CC 20-35 / CC 102-117: 8 layer levels, then 8 in/out
               buttons, for a controller's faders and pads
    Prog change  off / loads a slot (program 1-16)
    Key fade   0.5-20 s: a layer key bringing a layer in or out
    Entry fade 2-40 s: a section's layer coming in or going out
  page 15, RECALL: Morph (cut .. 2 min: how a load glides in), Recall
  (piece / sound only), Anchor glide (2-30 s), Compare (yours / saved)
  page 16, GROOVE: Pump (off / 4 bars .. beat), Pump depth, Duck (the
  piece dips while you play), Duck release
  pages 17-18, MACRO A / B: four macros (CC targets macro 1-4), each
  moving two knobs with a depth (-100..+100 %), offset or latch
  page 19, JOURNEY: Speed, Pads (off / soft / bright / all), Drone,
  Bells (off / bells / motion / both) - they travel through their
  engines, slowly crossfaded
  page 20, COLOUR: Pre-delay (0-200 ms), Era (70s / 80s / 90s / now),
  Sparkle (GLINT: small FM bells high on the chord tones), its octave
  page 21, CC OUT: 16 CCs of what moves inside (layer levels, energy,
  density, brightness, the way to the next chord ...), Channel, From CC,
  Rate

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
  Knob values and SETUP are saved in settings.txt; pieces in saves.txt.

LED: blue composing, green drifting, white flash on chord changes.
seed.txt counts start-ups so no two sessions begin the same way.

Amble is GPL-3. The Bloom reverb follows Conduit's bloom.c, after thement's
midiverb_emulator analysis of the MidiVerb II.
