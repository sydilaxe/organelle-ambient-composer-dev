# Project notes (Amble)

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

## Stage 1 (form, rhythm, Bloom)
- **Form:** `ac-plan`. The archetype curve (`ARCH_EXPR`) gives each section's energy. The peak becomes
  the climax, and the recap is the first section after the climax and past 72 % of the piece. Roles come
  from the energy slope. Each role has its own `ROLE_MASK` (layer chances), `ROLE_TIDE`, `ROLE_TEMPO`
  and `ROLE_PULSE`. The key plan (`ackeyp`) is applied through `acpend` at the next chord change.
- **Recap:** the chord degrees of the first two sections are stored in `acprog`, and the return section
  replays them. `acmotif0` is the piece's motif, and `ac-motifgen` transforms it per role.
- **Clock:** a `metro` runs at 24 ticks a beat (`ac-tick`), giving `ac-step` (16ths), `ac-beat` and
  `ac-bar`. Motion hit = `((s + rot) % n * k) % n < k`. Swing and rubato are a `pipe` delay per note.
- **Bloom in Pd:** a `switch~ 16 1 0.5` subpatch, i.e. 22.05 kHz in 16-sample blocks. The delays are
  kept in ms (the unit's samples / 23.4375), so timing is independent of the rate. The input is
  low-passed twice before decimation (`inlet~` doesn't filter), and the output goes through
  `outlet~ lin` then a low-pass. The loop's feedback (`delread~ $0-blfb 0`) is one block, against one
  sample in C, and the 13-sample diffuser is clamped to 0.73 ms. The tests show this doesn't matter.
  Loop gain = exp(−4.2·size/T), as in Conduit's `verb_decay`. Freeze sets loop gain 1 and gates the
  input.
- **Hall:** 8 lines with a fast Hadamard (3 butterfly stages) and g/√8 per line. Lines 1 and 5 are
  modulated with `delread4~`. Shimmer: two windowed `vd~` taps sweeping 125 ms at 8 Hz (an octave up),
  then high-passed and fed back in.
- **Tests:** set `actime` (time compression) *before* `ac-setseed`. The first section is armed when the
  piece starts.

## Stage 2 (live MIDI and audio)
- **MIDI in** (`midi_in`): `notein`, `bendin`, `touchin`, `polytouchin` and `ctlin` (CC 2, 11; 120 and 123
  = all notes off) are normalised to `ac-livenote`, `ac-livebend` (semitones) and `ac-livebreath`.
  Channels are folded to 1..16. Bend uses `($f1-8192)/8192`, as DM48 Engine does.
- **Voices:** 4 `amlive` abstractions. Allocation takes a free voice, else steals the oldest.
  `aclvn`/`aclvc` hold each voice's note and channel, so MPE bend and breath reach only that channel's
  voice. Breath on channel 1 goes to all. A note-on first sends the channel's current breath
  (`acbrch`), so a note started at breath 0 is silent. A live voice switches its synthesis subpatch on
  at note-on, and off 1.6 s after its release.
- **Keys:** `notesRaw` goes to live notes unless `acext`, aux is held, or `acforce == 1`. Note-offs always
  go to live, so no note hangs when the mode changes. Aux: release with no key used = next page.
- **Listening:** `acfocus` (the pitch class you hold or sing). In a change, a root whose triad contains
  it is picked, with probability `acfollow`. After 6 s held it becomes `acpend` (the key).
  Breath adds `0.35·acbreath` to the effective density. `ac-nextsec` waits while breath or notes are active.
- **Pitch tracker** (`pitch_tracker`): `block~ 4096 4`, the window table `achann` (Hann on the first
  2048, zeros after, so the circular ACF doesn't wrap for lags < 2048), `rfft~` → power → `rifft~` →
  `tabsend~ acacf`. On `bang~`: `array max acacf 40 560` gives the lag, clarity = peak / acacf[0],
  then parabolic interpolation. `sigmund~` isn't used: it's in Pd's "extra" objects and may be missing.
- **Class** (`ac-ana`, every 100 ms):
  - activity = loud or recent onsets
  - pitchedness = EMA of stable pitch frames (clarity > 0.55)
  - onsets = EMA, +0.3 per onset
  - class: quiet (activity < 0.3), pitched (pitchedness > 0.45), plucked (onsets > 0.9), else texture
- **[value] gotcha (again):** `[v x]` doesn't output, so a bang can't be chained after it. Use
  `[t b f]` and set the value from the right outlet.

## Stage 3 (OLED, SETUP, MIDI clock)
- **OLED:** the patch draws every region itself with `/oled/g*` messages to `oscOut` and never sends
  `screenLine`, so the OS's text lines can't overwrite the graphics. The text Lines go to `ac-txt1..5`
  (the tests read these) and the renderer prints what it needs.
  - **Redraw rates:** the voice ladder every 100 ms, meters every 200 ms, form/bottom/time every 1 s,
    the rhythm pattern at each section.
  - **Rhythm cursor:** two `gInvertArea`s a step (the old cell back, the new one).
  - **Flip:** every 100 ms.
  - **Text gating:** text is gated at the moment it arrives (`gated_text`: `[t a b]` → condition → `spigot`).
    A spigot opened by another receiver of the same message can't be relied on: Pd doesn't order receivers.
- **Only these OLED commands are used:** gFillArea, gInvertArea, gBox, gPrintln, gFlip and gShowInfoBar,
  the ones DM48 Engine already uses on the device. Checked only in `oledemu.py` so far.
- **SETUP:** aux held 1 s (a `[delay 1000]` started by `[t b]`; a float into `[delay]` would *set its time*).
  Knobs in SETUP are absolute (selectors). `settings.txt` holds 24 numbers (12 knobs + 12 SETUP values).
  It is written 3 s after a change and when SETUP closes, and read at start-up before the first piece.
- **MIDI out:** through `ac-midibyte` → `[midiout]` and `ac-noteout` → `[noteout]`, so the tests can print
  them. Clock 248 on every `ac-tick` while `acclkon`. Start (250) at a new piece, Stop (252) at FIN.
- **Clock in:** `[midirealtimein]` → `ac-rtin`. In follow mode the internal metro is gated (`ac-mtick`) and
  incoming 248s bang `ac-tick`. Tempo = EMA of 60000/(24·tick ms); `[timer]` is read (right inlet), then
  restarted (left inlet).

## Wider sound world (after feedback: "more electric and synthetic", "I liked the sub", "vocode or morph")
- **Pad types 6-9** (`gen_sounds.py`): saws, pwm, digi and sync. They are added after the first six, so
  `acvoice` and `amlive` now hold 10 switched subpatches, with at most two running at once.
- **Drones:**
  - Each design is its own switched subpatch: `ac-g-drone` (pure), `ac-g-drone1..3`.
  - The layers proc sends `acgdrone*(acdcur==i)`.
  - `acdcur` is the piece's design, or its second design in a break.
- **Sub** (`ac-g-sub`, pitch `ac-subp`):
  - Mode 0: tonic − 12. Mode 1: `acnew[0]` folded into 28..42. Mode 2: they alternate by section.
  - The bar pulse swells it too.
  - Its level sits about −5 dB under a drone design: on its own, it had been louder than the drone.
- **Character:** 4 switched subpatches on the pad bus (in `master`). Their output goes to the mix, and
  the dry pads are scaled by `ac-chdry`. The gain also follows the pad layer (`acgpad`), so a muted pad
  layer turns the character off too. Tape hiss follows the signal's envelope: with a fixed hiss level,
  silence still hissed at −71 dB.
- **Vocoder:** 10 bands from 150 Hz to 7 kHz, `vcf~` Q 5 on both the modulator (`ac-in`) and the carrier,
  with envelope = `abs~` → `lop~ 30`. The carrier is 4 detuned saw pairs on the chord (`ac-voccar0..3`)
  plus noise for sibilance (vocode), or the pad bus `s~ ac-padsig` (morph).
- **RNG:** each stream's seed goes through `fract(sin(seed·12.9898 + k·78.233)·43758.5453)`. Without it,
  the 4 LCG streams seeded `seed + k·7919` moved together, and neighbouring seeds picked the same palettes.

## Stereo (feedback: "wide and interesting by default; I may also go mono into external effects")
- **Measured before:** L/R correlation 0.97–1.00 in openings and side/mid −16 to −20 dB, because a mono
  drone and sub dominated.
- **Measured now:** side/mid −5 to −10 dB, correlation above 200 Hz about 0, balance movement about 2 dB,
  mono sum −0.5 to −1.7 dB. These are checked in `ci_check` section 19.
- **`span()`:** equal-power pan by a *signal* position (`cos~` of pos·¼ and pos·¼ − ¼). It's used for the
  pad orbits, live voices, the drone's moving parts and per-grain cloud positions (`samphold~` of noise
  at each grain start).
- **Drone designs:**
  - pure: real stereo parts
  - analog: a saw and its own sweep on each side
  - organ: opposite rotary swells, the right a moving delayed copy
  - fm: a delayed copy
  - The sub stays mono.
- **Master:** M/S with `ac-width` = role width × SETUP Width, or 0 when SETUP Output is mono. Mono sums
  are unaffected by the side gain.

## Atmospheres, stereo engines, scenes, preferences (feedback: "atmospheres, not every piece"; "I liked the
## electronic and the bell-like ones"; "engines can have stereo elements"; "the composition can place voices")
- **Atmospheres** (`ATMOS`): haze, deep, space, night and tides, each a switched subpatch (`ac-g-atm<i>`).
  - A piece has one with chance 0.55 (`acatm`), and a section plays it with chance `ATMOS_ROLE[role]`.
  - A break may use the piece's second kind.
  - They are muted with the textures key.
  - They are retuned on every chord change: haze bands, space combs and night tones.
  - Thunder (`ac-ttick`) only plays in "deep".
- **Pad types are stereo:** `_out(s, L, ln, R)` and two outlets per type. The voice keeps the type's
  stereo and balance-pans it to its place (equal power × √2, clipped at 1).
  - **Mono safety:** an independent detuned copy cancels when summed to mono. FM measured −29 dB dips,
    so the right side keeps part of the left (R = 0.5·L + 0.65·R′). Worst mono dip across types is now
    about −5 dB, checked in `ci_check` 20.
- **Scenes** (`SCENE_DATA`, `SCENE_ROLE`): per section, 4 pad homes (`ac-v<k>-home`, 6 s glide), the
  bells' and motion's centre and spread, the cloud's spread, and an orbit-depth factor.
- **Preferences:** pick tables built by `pick_table(weights)` from `FLAVOUR_WEIGHTS`,
  `FM_RATIO_WEIGHTS` and `PARTIAL_WEIGHTS`. Electronic and bell-like types make about 80 % of picks.
  The bells layer's role chances were raised by 0.15.
- **CPU:** about 3 % of an x86 core in the heaviest case.

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
