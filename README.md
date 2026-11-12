# organelle-ambient-composer-dev

**Ambient Composer**: a Pure Data patch for the Critter & Guitari **Organelle M** that makes ambient
music on its own. You can play over it as a backing track, or let it compose a whole piece.

Every start gives a new piece. Each piece picks its own key and scale (including just, harmonic-7th,
slendro and pelog tunings), chord voicings, synthesis palette, ratios, drone interval, textures and
form. Your own audio can play the composer's chord strings, feed its granular cloud, go through tape
echoes, or steer the piece without being heard ("ghost" mode).

## Install

Copy `patches/Ambient Composer` into the Organelle's `Patches` folder (USB stick, SD card or the OS 5
web editor). It needs Organelle OS 5 (Pd 0.53) and uses vanilla Pd objects only.

**How to play it:** see [`patches/Ambient Composer/README.txt`](patches/Ambient%20Composer/README.txt)
(knobs, keys, input modes, screen).

**Demos** (offline renders of the patch, with no editing):
- [`demos/composition_seed_2718.mp3`](demos/composition_seed_2718.mp3): a complete 3-minute composition (Len at 0), through to its fade-out.
- [`demos/drift_resonate_input_seed_808.mp3`](demos/drift_resonate_input_seed_808.mp3): DRIFT mode, with a plucked test tone on the input ringing the chord resonators.

## What is in it

| Part | What it does |
|---|---|
| Harmony | 16 scales, 8 voicing families (spread, quartal, cluster, fifths, ninths, spectral partials, mirror, sus). Root motion favours 4ths and 5ths. The piece can modulate on its own or follow the key you press, and with Weird up it borrows a different mode. Each voice is voice-led and glides on its own delay, so a chord dissolves into the next one. |
| Form | DRIFT: endless sections with random energy. COMPOSE: 5 to 8 sections whose energy rises and falls (emerge, haze, drift, bloom, swell, dissolve), then a fade to silence. |
| Pads | 4 voices. Each section crossfades every voice to one of 6 synthesis types: FM, vox formants, bowed string, drifting partials, wavefolder, pulsar. |
| Drone | The tonic, a beating twin, a per-piece interval (5th, 4th, octave, 7/4, 6/5), a sub, and a noise "tube". |
| Textures | Rain (water-drop bubbles on chord tones), wind (bands tuned to the chord), embers, creature chirps. |
| Cloud | 4 granular streams over an 8 s buffer of the patch's own sound or your input, transposed by consonant ratios. It can be captured and frozen. |
| Bells | A 5-note motif that mutates as it repeats, played on 3-partial bars. |
| Input | Chord-tuned comb resonators, cloud feed, tape echoes, ghost control (loudness and onsets). |
| Space | 4-line FDN reverb (2.5 to 28 s), master fade, compressor. |

CPU: about 1.5 % of one x86 core with every layer and input processing on (measured offline), which
should be roughly 12 to 15 % of the Organelle's CM3.

## Source (`tools/`)

The patch is **generated** by Python, so it can be rebuilt and tested. Edit the generator, not the `.pd`
files.

- `gen.py`: builds `patches/Ambient Composer` (`main.pd`, `acvoice.pd`, `README.txt`, `seed.txt`).
- `pdlib.py`: writes Pd files, plus a small step language (`proc`, `X`, `V`, `If`, `Loop`, `SendL`...). It
  compiles to `[t b b]` chains of `[expr]` over global `[value]`s.
- `gen_brain.py`: seed, piece, form, chord changes, event players. `gen_ui.py`: knobs, keys, screen, LED.
  `gen_dsp.py`: all sound. `data.py`: scales, voicings and ratio tables.
- `harness.py`: runs the patch offline (`pd -batch`) with timed events and a test input, and records it.
  `ci_check.py`: the test suite. `render_demo.py`: the demo MP3s.

```
cd tools
./build.sh            # regenerate the patch
python3 ci_check.py   # 32 offline checks in Pure Data
```

Requirements: Python 3 with numpy, Pure Data 0.53+ (`pd -batch`), and ffmpeg for the demos.

## Releases

`.github/workflows/release.yml` rebuilds the patch, fails if the committed patch is out of date, runs
`ci_check.py`, and packages `Ambient_Composer-<version>.zip`. Push a tag `v*` to publish a release. You
can also run the workflow by hand to get the zip as an artifact.

See [NOTES.md](NOTES.md) for design notes and Pd gotchas.
