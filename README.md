# Amble

**Amble** is a generative ambient composer for the Critter & Guitari **Organelle M**, written in Pure Data.
It composes whole pieces of 5 to 30 minutes with a form, or drifts endlessly as a backing track.
It is built to play with live input: MPE / breath controllers such as the Lekholm DM48X, keyboards,
acoustic instruments, voice, samples and field recordings.

> **Status:** in development, delivered in three stages.
> 1. **Done:** form, rhythm, Bloom reverb.
> 2. **Done:** live MIDI (MPE, breath) and audio listening.
> 3. **Done:** the graphical OLED score, the SETUP page, and MIDI clock in and out.
>
> It builds, and passes its offline tests in Pure Data. It has not been run on an Organelle yet.

## Install

Copy `patches/Amble` into the Organelle's `Patches` folder. It needs Organelle OS 5 (Pd 0.53) and uses
vanilla Pd objects only. How to play it: [`patches/Amble/README.txt`](patches/Amble/README.txt).

**Demos** (offline renders, unedited):
- [`demos/amble_composition_seed_2718.mp3`](demos/amble_composition_seed_2718.mp3): a complete 5-minute composition. The form runs emerge, establish, develop, climax, dissolve. The key goes out and comes home, and the tempo and the motion layer follow the form.
- [`demos/amble_electric_composition_seed_3612.mp3`](demos/amble_electric_composition_seed_3612.mp3): an electric 5-minute piece: digi and saw pads, an analog drone, a sub bass line, chorus, buzz and radio textures.
- [`demos/amble_vocoder_voice_input_seed_4139.mp3`](demos/amble_vocoder_voice_input_seed_4139.mp3): a synthetic singer on the input, vocoded through a synth choir on Amble's chords.
- [`demos/amble_live_breath_mpe_and_input_seed_77.mp3`](demos/amble_live_breath_mpe_and_input_seed_77.mp3): a breath-controlled MPE part, sent as a DM48X would (notes on their own channels, breath swells, bends), with a plucked tone on the audio input in Auto mode.
- [`demos/amble_drift_resonate_input_seed_808.mp3`](demos/amble_drift_resonate_input_seed_808.mp3): DRIFT mode, with a plucked test tone on the input ringing the chord-tuned strings.

## How it composes

| | |
|---|---|
| **Piece** | A seed picks the key and scale (16, including just, harmonic-7th, slendro and pelog), voicing families, the pad synthesis palette, tempo (40 to 72 BPM), meter (3 to 7), motif, textures and reverb. A new seed is used at every start; a seed replays its piece. |
| **Form** | One of 5 archetypes (arch, slow build, waves, two peaks, journey) over 6 to 12 sections. Each section has a role: emerge, establish, develop, intensify, climax, break, return or dissolve. Roles set the layers, the key area (out from home and back), tempo, harmonic pace, drone pulse, motif transformation (inverted, raised, restored) and reverb. The return section replays the opening progression. |
| **Harmony** | Voice-led chords from 8 voicing families. Each voice glides on its own delay, so chords dissolve into each other. |
| **Rhythm** | One clock at 24 ticks a beat. Each layer has its own relation to it, so the texture has rhythm without a beat. |

The layers and their rhythms:

| Layer | Rhythm |
|---|---|
| Drone | a pulse locked to the bar |
| Pads | breathing cycles of 7, 9, 11 and 13 half-bars, which phase against each other |
| Motion | Euclidean patterns, with swing and tempo echoes |
| Bells | free phrasing, in beats |
| Textures | random weather |
| Cloud | grains, locked to the beat in intense sections |

## Live input

- **MIDI:** MPE notes, per-note bend (48 semitones; 2 on channel 1) and breath (CC 2, CC 11, channel or poly
  pressure) play 4 live voices in the piece's synthesis type. With a breath controller, breath sets the
  voices' level and brightness.
- **The Organelle keys** play notes when Amble is standalone. When an external controller plays, they
  become function keys; aux + key is a function at any time.
- **Listening:**
  - A held or sung pitch pulls the next chord to contain it.
  - A note held for 6 s becomes the key centre.
  - Breath raises the energy, and a section waits while you play (up to 3 × 30 s).
- **Audio:**
  - **Clean-up:** a gate and automatic gain.
  - **Pitch:** a pitch tracker built from vanilla objects (FFT autocorrelation; reads a 220 Hz sine as MIDI 57.06).
  - **Class:** pitched, plucked or texture, from pitch confidence, onset rate and level.
  - **Auto mode:** chooses chord strings, harmonised grains, bells on attacks or tuned bands to suit.
  - **Memories:** up to 4 × 8 s captured from your input, brought back transformed in break, return and dissolve sections.

## The screen and SETUP

The OLED is a live score. The images below are rendered offline by `tools/shots.py` with an OLED
emulator, so the font only approximates the Organelle's.

![screens](docs/shots/sheet.png)

| Screen | Contents |
|---|---|
| **Score** | The form strip (one bar per section, height = energy, current one inverted, a playhead). Key and scale, with the time left. The pad voices gliding on a pitch ladder, with your held notes as boxes and a breath bar. Meters for every layer, the reverb and the input. The motion layer's Euclidean pattern with a moving cursor, the tempo and the reverb type. The section role and voicing, and K/M/E tags for who is playing and the clock. |
| **Knob page** | Shown for 2 s when you turn a knob. |
| **SETUP** | Hold aux for 1 s. Page 1: MIDI out (off, clock, clock + notes, notes), Sync (internal or follow clock), Keys (auto, play, functions), Bloom (clean or vintage). Page 2: how much the chords follow you, MPE bend range, MIDI out channel, breath curve. Saved in `settings.txt` with the knob values. |

**MIDI out:**
- **Clock:** 24 ticks a beat at the piece's tempo, with Start and Stop at the start and end of a piece.
- **Notes:** chords, drone root, bells and motion, each on its own channel.

**Sync:** Amble leads, or it follows an incoming clock. Incoming ticks drive its rhythm and Start resets the bar.

## Sounds

| | Choices (each piece picks its own) |
|---|---|
| **Pads** | 10 types: fm, vox formants, bowed string, drifting partials, wavefolder, pulsar, **saws** (detuned analog ensemble through a tracking resonant low-pass), **pwm** (Juno-like), **digi** (ring mod, bit crush, sample-rate reduction), **sync** (hard-sync sweep). A piece uses a palette of 3, per voice and per section. |
| **Drone** | 4 designs: pure, analog (saws and a square through a slow resonant sweep), organ (drawbars with a rotary shimmer), fm (an electric growl). The break may switch to the piece's second design. |
| **Sub** | A dedicated layer: the pedal an octave under the tonic, the chord root as a bass line, or both. Softly saturated, so small speakers still hear it. |
| **Character** | On the pads: clean, chorus, tape (wow, saturation, hiss that follows the music), ring modulation, or crush. |
| **Textures** | 7: rain, wind, embers, chirps, radio (static and drifting whistles), data (blip bursts), buzz (electric hum on the tonic). |
| **Input** | Besides chord strings, cloud, tape, ghost and tuned bands: **vocode** (a 10-band vocoder; your sound speaks through a synth choir singing the chord) and **morph** (it speaks through the pads themselves). Auto mode vocodes pitched input in some pieces. |

The four random streams are seeded through a hash, so nearby seeds don't share their sound choices. The
tests check that 10 consecutive seeds give 10 different palettes.

## Reverb

- **Bloom 1 / Bloom 2:** after the Alesis MidiVerb II *Bloom* programs (45 and 49).
  - **Where it comes from:** ported from [Conduit](https://github.com/sydilaxe/Trimui-Conduit-dev)'s `bloom.c`, which follows thement's [midiverb_emulator](https://github.com/thement/midiverb_emulator) analysis.
  - **How it sounds:** a damped loop through 15 diffusing all-passes makes the sound swell for about half a second before it rings out.
  - **How it runs:** at 22.05 kHz, close to the unit's 23.4 kHz.
  - **How close it is:** the tests compare it with the C version (`tools/ref`). The swell peak is within 0.02 s, T60 within 3 %, and the envelope correlates at r ≈ 0.9.
- **Hall:** an 8-line FDN.
- **Shimmer:** the Hall with an octave-up shifter in its loop.
- **Auto:** the piece chooses. Each section change blooms the reverb up, the climax lengthens it, and the dissolve darkens it.

CPU, measured offline: about 2.2 % of one x86 core with every layer, the vocoder, a character effect, 4 live voices,
the OLED and the clock running. That should be roughly 18 to 22 % of the Organelle's CM3.

## Source (`tools/`)

The patch is **generated** by Python, so it can be rebuilt and tested. Edit the generator, not the `.pd`
files.

- `gen.py` builds `patches/Amble`.
- `pdlib.py` writes Pd files. It also has a small step language that compiles to `[expr]` chains.
- `gen_brain.py`: piece, form, sections, chord changes, clock and motion, reverb control.
- `gen_live.py`: MIDI in, live voices, listening, audio analysis and class, memories.
- `gen_ui.py`: knobs, keys, screen.
- `gen_dsp.py`: voices, layers, input, master.
- `gen_sounds.py`: the electric pad types, drone designs, sub, electric textures, character effects and vocoder.
- `gen_oled.py`: the OLED score.
- `gen_setup.py`: SETUP, settings, MIDI clock and notes out, clock in.
- `gen_verb.py`: the reverbs.
- `data.py`: the tables.
- `harness.py` runs the patch offline (`pd -batch`).
- `ci_check.py` is the test suite (101 checks).
- `shots.py` renders OLED screenshots with `oledemu.py`.
- `ref/` holds Conduit's Bloom in C, the reference for the reverb tests.

```
cd tools
./build.sh            # regenerate the patch
python3 ci_check.py   # offline checks in Pure Data (needs gcc for the Bloom reference)
```

Requirements: Python 3 with numpy, Pure Data 0.53+, gcc, and ffmpeg for the demos.

## Releases

`.github/workflows/release.yml` builds, checks the committed patch is up to date, runs the tests and
packages `Amble-<version>.zip`. Push a tag `v*` to publish a release.

## Licence

GPL-3.0 (see `LICENSE`), as is Conduit, whose Bloom reverb Amble ports.
