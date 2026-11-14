# tools: how Amble is built

Amble is a vanilla Pure Data patch written by Python. Nothing in `patches/Amble` is edited by hand: change the
generator here, then run `./build.sh` (it writes `patches/Amble`) and commit both.

```
python3 gen.py                 build the patch (= ./build.sh)
python3 ci_check.py            all the offline checks in Pd (about 25 min; CI runs them)
python3 ci_check.py --list     the checks' sections;  python3 ci_check.py 57 58  only those
python3 shots.py               OLED screenshots into ../docs/shots
./package.sh VERSION           the release zip and the PDF manual into ../dist
```

## The files

| File | What it builds |
| --- | --- |
| `gen.py` | the patch: `main.pd` (every canvas below as a subpatch), the abstractions, the text files |
| `pdlib.py` | the Pd writer: `Canvas`, and the *steps* language the control logic is written in (below) |
| `data.py` | the tables: scales, voicings, the pleasing palette, roles, pad types, textures, knob pages, factory pieces |
| `gen_brain.py` | the composer: seed, piece, form and sections, chords (`ac-chordnext` picks the next one, `ac-change` plays it), layers, players, verb settings, the clock |
| `gen_perform.py` | performing: the morph engine, ANCHOR, COMPARE, the changed check, macros, SINK / SWELL / DUCK, PUMP, JOURNEY, CC OUT, GLINT's engine |
| `gen_ui.py` | the Organelle keys, knobs (pickup), aux, footswitch, the text screen lines, the LED |
| `gen_oled.py` | the OLED: the play view, the MIX view, the knob pop-up (SETUP draws its own page) |
| `gen_setup.py` | SETUP: the 21 pages (`setup_pages()`), what each knob does (`setup()`), settings.txt, the CPU guard |
| `gen_saves.py` | SAVES: saves.txt, loading (through the morph), factory pieces (factory.txt) |
| `gen_midi.py` | MIDI out (clock, notes) and MIDI clock in |
| `gen_live.py` | MIDI in, the live voices, CC MAP and Mix CC targets, listening, audio analysis, memories, the 100 ms clock |
| `gen_dsp.py` | sound, core: pad and live voice abstractions, drone, textures, cloud, bells, motion, input, the master |
| `gen_sounds.py` | more sounds: pad types 7-14, drone designs 2-5, the sub, character, atmospheres, the vocoder |
| `gen_strikes.py` | the bells' and motion's engines (bars, fm, blip, wood, wave, metal) |
| `gen_verb.py` | the reverbs: Bloom (after Conduit / MidiVerb II), the Hall, the Shimmer |
| `manual.py`, `readme_text.py` | the PDF manual and the patch's README.txt, from the same data |
| `harness.py`, `ci_check.py` | running the patch offline in Pd with timed events, and the checks |
| `shots.py`, `oledemu.py` | screenshots: the OLED messages of an offline run drawn into PNGs |

## Names in the patch

- **Values** (global state) are `[value]`s named `ac<word>`, no dash, so `[expr]` can read them: `acdens`,
  `acsecsel`. Their defaults are in each module's `GLOBALS`; arrays in `ARRAYS`; arrays filled at start in
  `DATA_TABLES` (gen_brain collects every module's).
- **Messages** are `[send]` / `[receive]` names `ac-<word>`, with a dash: `ac-layers`, `ac-change`. A *proc* is a
  receiver that runs steps (`proc(c, "ac-layers", [...])`; `Call("ac-layers")` runs it).
- **Knobs**: the 32 knob values (8 pages x 4, `data.PAGES`) are also in the array `acparams`; turning one (or a
  morph, a macro, a CC target) sends `ac-param <index> <value>`, which sets the value and runs its side effect
  (`gen_ui.SIDE`).
- **Gains** of switched subpatches are `ac-g-<name>` messages, `"target ms"`; a subpatch computes only while its
  gain is above 0 (`gen_dsp.switched`).
- **Buses** are `throw~ / catch~ ac-<bus>L/R` (see `gen_dsp`'s docstring).

## The steps language (pdlib)

Control logic is a list of steps compiled to a `[t b b ...]` chain of `[expr]` boxes:

```python
proc(c, "ac-anchortap", [If("acancs", [Call("ac-anchorgo")], [Call("ac-anchorset")])])   # gen_perform
proc(c, "ac-anchorset", [
    Loop(str(NK), "aci", [T("acanc", "aci", "acparams[int(aci)]")]),   # acanc[aci] = acparams[aci], for each knob
    ...                                                                 # (the layer keys' states likewise)
    V("acancs", "1"), Toast("anchor set"), Call("ac-oledbottom"),       # a value, a message, another proc
])
```

`V` sets a value, `T` an array element, `X` several at once, `SendL` sends a list of expressions, `Line` builds a
screen line from expressions and word lists, `Arm` / `Later` run something after a delay, `RNG` refreshes the
piece's random numbers (`acr1..4`: seeded per piece, so a seed replays its piece).

## Where things are

| To find... | Look in |
| --- | --- |
| a key's function | `gen_ui.LOW_KEYS / TOP_KEYS` (names), `keys()` (wiring; the hold / release gestures at its top) |
| a knob page | `data.PAGES`; its side effects `gen_ui.SIDE`; its screen line `gen_ui.screen()` |
| a SETUP row | `gen_setup.setup_pages()` (text), `setup()` (`If(at("PAGE", row), ...)`: what it does) |
| a CC target | `gen_setup.TARGETS`; what it does: `gen_live.cc_map()` (`actg == n`) |
| how a chord is chosen | `gen_brain.change()`: `ac-chordnext` (the next one, Harm, the pleasing tables), `ac-change` |
| a section's layers and levels | `gen_brain.layers()` (`ac-layers`) |
| the save line | `gen_setup.SAVE_SCALARS / SAVE_ARRAYS / SAVE_EXTRA`; `gen_saves` |
| settings.txt | `gen_setup.SETTINGS` (its order); defaults `gen.py` |

## Adding things

- **A SETUP row**: a row in `setup_pages()` (every page's 4 rows are taken: a new page means a name in
  `SETUP_NAMES`, 4 rows, and `NSET` one up), its knob in `setup()` as
  `If(at("PAGE", row), [...])`, its value's default in `GLOBALS`. If it should survive a restart, add its name to
  the end of `SETTINGS` and its default to the end of the list in `gen.py`; if a saved piece should keep it, to the
  end of `SAVE_EXTRA`. Then a description in `manual.py` (`SETUP_DESC`) - the build stops without one.
- **A CC target**: append to `TARGETS` (the order is the saved index), handle `actg == <index>` in
  `gen_live.cc_map()`, describe it in the manual's `"to"` entry.
- **A pad type / drone / engine**: a switched subpatch in `gen_sounds` (pad types: `NEW_FLAVS`; drones:
  `NEW_DRONES`), its name appended to `data.FLAVOURS` / `DRONES`, a description in the manual. Append, never insert:
  saves and settings store indices.
- **A check**: a `# N. what it checks` section at the end of `ci_check.py` (it can then run alone).

Things that stay in step on purpose: `SETTINGS` and the defaults in `gen.py` (asserted at build), `SETUP_NAMES` and
`setup_pages()` (asserted), every control and its manual description (checked by `manual.py`).
