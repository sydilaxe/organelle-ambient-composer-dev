# Project notes

Working memory for this project: read it first in a new session.

## Target
- Organelle M, Organelle OS 5, Pd 0.53, **vanilla objects only**. The tests run on Pd 0.54.
- Mother conventions: `[r~ inL/inR]`, `[throw~ outL/outR]`, `[r knob1..4]` (0..1), `[r notesRaw]` (note 60..83,
  vel 0/100), `[r aux]`, `[r fs]`, `[s screenLine1..5]`, `[s led]` (0 off, 3 green, 5 blue, 7 white).
  `midiOutGate 0` keeps mother from sending the keys out as MIDI.

## Design
- **Names:** values are `ac<word>` (no dash, so `[expr]` can read them). Sends and receives are
  `ac-<word>`. A `[value]` and a `[receive]` must never share a symbol: a float sent to that name would
  also set the value, and a list would give "no method" errors.
- **Control logic** is written in `pdlib` steps. `proc(name, steps)` becomes `[r name] -> [t b b ...]`,
  and step i fires before step i+1. `X`/`V`/`T`/`SendL` are `[expr]` boxes. `If` is `[expr] -> [sel 0]`.
  `Loop` is `[until]`. `Arm(tick, ms)` re-arms a `[delay]` that bangs `tick`, which is how the change,
  section and event clocks work.
- **Randomness:** `ac-rng` refreshes `acr1..acr4` from 4 `[random]` objects that are seeded per piece.
  Pd's `[random]` is an LCG whose *first* draw after `seed` can be nearly the same for different seeds
  (seeds 130920 and 372840 gave the same piece). So 5 draws are thrown away after seeding.
- **Uniqueness:** `seed.txt` counts start-ups. Seed = counter·7919 + µs jitter. The B key reseeds from the
  time since load. `ac-setseed N` replays piece N (the tests use this).
- **Harmony:** chord root = scale degree. Moves come from `MOVES`, with a home-return chance (only when
  not already home). A voicing family gives 4 offsets (degrees, or semitones for "spectral"). Each voice
  either takes the voicing as written or the octave nearest its last pitch (70 %). The result is folded
  into MIDI 43..86. Each voice gets its own glide and start delay (`pipe`) within the change time.
- **Layers** are `switch~`ed subpatches (`switched()` in `gen_dsp.py`). Each is on while its gain target
  is above 0 and off 100 ms after a fade to 0. Every output leaves through `throw~` or `outlet~`, never
  `s~`. The bowed string runs at block 16 (`switch~ 16`), so its output goes out by `outlet~`: `throw~`
  needs matching block sizes.
- **Pad voice** = abstraction `acvoice N`. 6 synthesis subpatches crossfade over 4 s, so at most 2 run.
- **Cloud** buffer `acbuf` (8 s) is written by an always-on writer. Its source is the patch's own drone
  and pads (`ac-src` -> `s~ ac-resamp`) or the input (cloud mode or capture). Grain position and
  transposition are `samphold~`ed at each grain start, so a new ratio never clicks mid-grain.
- **Comb resonators / bow:** the delay is `1000/f` ms (vd~ in a feedback loop clamps to one block; the
  combs fold their pitch into 98-370 Hz so they stay above 64 samples). The bow subtracts 0.012 ms for
  the loop low-pass's group delay (it measured within 0.5 % of pitch).
- **Levels** (single layers, offline): pad ≈ -24, drone ≈ -22, rain/wind ≈ -28, bells ≈ -27,
  cloud ≈ -29 dB RMS. Default mix ≈ -21 dB RMS, peaks < 0.45. The compressor starts at about -18 dBFS RMS.

## Pd gotchas met here
- Screen lines: `[pack]` parts must be fed right to left: the hot inlet (part 0) goes last.
- A message box `list word` with a single word arrives as `symbol word`. Toasts use two or more words.
- `[expr]` has `mtof`, `floor`, `fmod`, `pow`, `if`. `%` is integer-only, so wrap with
  `((x % n) + n) % n`.

## Testing
- `harness.run(events, seconds, inp)` builds the patch into a temporary folder (so `seed.txt` isn't
  touched), feeds `s~ inL/inR` (silence, plucked tone, or noise), and records `outL/outR`.
  `actime 0.04` compresses all clocks (section and change times, glides) for fast composition tests.
- `ci_check.py`: load errors, level, clipping, screen, uniqueness and replay, each pad type's level and
  pitch, a composition through to FIN and silence, knob pickup and pages, key functions, all input modes,
  ghost onsets.
- Checked by hand: 15-minute renders at all-max and all-min settings (stable, no NaN, peak 0.78), click
  scan during fast changes (none above -38 dB in the >9 kHz band), CPU (default 1.0 %, everything with
  input 1.5 % of an x86 core).

## Ideas
- Save the knob settings per session (`saveState`).
- MIDI in for key centre and chord-change triggers. MIDI clock out of the change grid.
- A spectral freeze (`rfft~`) input mode.
- Test on the hardware: CPU on the CM3, input levels, the LED colours.
