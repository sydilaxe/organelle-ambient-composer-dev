# Amble

**Amble** is a generative ambient composer for the Critter & Guitari **Organelle M**, written in Pure Data.
It composes whole pieces of 5 to 30 minutes with a form, or drifts endlessly as a backing track.
It is built to play with live input: MPE / breath controllers such as the Lekholm DM48X, keyboards,
acoustic instruments, voice, samples and field recordings.

> **Status:** in development, delivered in three stages.
> 1. **Done:** form, rhythm, Bloom reverb.
> 2. **Next:** live MIDI (MPE, breath) and audio listening.
> 3. **Then:** the graphical OLED score, the SETUP page, and MIDI clock in and out.
>
> It builds, and passes its offline tests in Pure Data. It has not been run on an Organelle yet.

## Install

Copy `patches/Amble` into the Organelle's `Patches` folder. It needs Organelle OS 5 (Pd 0.53) and uses
vanilla Pd objects only. How to play it: [`patches/Amble/README.txt`](patches/Amble/README.txt).

**Demos** (offline renders, unedited):
- [`demos/amble_composition_seed_2718.mp3`](demos/amble_composition_seed_2718.mp3): a complete 5-minute composition. The form runs emerge, establish, develop, climax, dissolve. The key goes out and comes home, and the tempo and the motion layer follow the form.
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

## Reverb

- **Bloom 1 / Bloom 2:** after the Alesis MidiVerb II *Bloom* programs (45 and 49).
  - **Where it comes from:** ported from [Conduit](https://github.com/sydilaxe/Trimui-Conduit-dev)'s `bloom.c`, which follows thement's [midiverb_emulator](https://github.com/thement/midiverb_emulator) analysis.
  - **How it sounds:** a damped loop through 15 diffusing all-passes makes the sound swell for about half a second before it rings out.
  - **How it runs:** at 22.05 kHz, close to the unit's 23.4 kHz.
  - **How close it is:** the tests compare it with the C version (`tools/ref`). The swell peak is within 0.02 s, T60 within 3 %, and the envelope correlates at r ≈ 0.9.
- **Hall:** an 8-line FDN.
- **Shimmer:** the Hall with an octave-up shifter in its loop.
- **Auto:** the piece chooses. Each section change blooms the reverb up, the climax lengthens it, and the dissolve darkens it.

CPU, measured offline: about 1.3 % of one x86 core with every layer and input processing on. That should be
roughly 10 to 13 % of the Organelle's CM3.

## Source (`tools/`)

The patch is **generated** by Python, so it can be rebuilt and tested. Edit the generator, not the `.pd`
files.

- `gen.py` builds `patches/Amble`.
- `pdlib.py` writes Pd files. It also has a small step language that compiles to `[expr]` chains.
- `gen_brain.py`: piece, form, sections, chord changes, clock and motion, reverb control.
- `gen_ui.py`: knobs, keys, screen.
- `gen_dsp.py`: voices, layers, input, master.
- `gen_verb.py`: the reverbs.
- `data.py`: the tables.
- `harness.py` runs the patch offline (`pd -batch`).
- `ci_check.py` is the test suite.
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
