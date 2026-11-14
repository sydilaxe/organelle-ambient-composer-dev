# Amble on the Organelle: a one-session check

Everything since the glide setting has been tested offline only (Pd in batch, an OLED emulator). This list checks
what only the device can tell: the CPU, the feel of the keys, and how it sounds. About 30-40 minutes. Note what you
find next to each item.

## 1. CPU (SETUP 4 shows the load; the CPU guard steps in above 78 %)

Start a piece, then build up to the heaviest case, one step at a time, and watch SETUP 4's CPU after each:

1. Plain piece, Dens 80 %, Rhy 80 %. Note the load.
2. SETUP 5 SOUNDS: Pads `beat`, Drone `frost`.
3. SETUP 19 JOURNEY: Speed `fast`, Pads `all`, Drone `on`, Bells `both`.
4. PERFORM (low F#): Sink 50 %, Blur 50 %, Swell 50 %.
5. SETUP 16 GROOVE: Pump `beat`, depth 50 %, Duck 50 %.
6. SETUP 20 COLOUR: Sparkle 100 %.
7. SETUP 21 CC OUT: on.
8. Turn In up with something plugged in (the input stage runs only while In is above 0).

What to note: the load at each step; whether `LTE` appears on the bottom line (the guard lightening the sound);
any crackle. If it crackles below 78 %, raise `-audiobuf` in `pd-opts.txt` (25 now; try 40).

## 2. Feel (one hand, while playing a MIDI keyboard with the other)

- **Low A**: tap = the next chord now; hold = another next chord every 0.7 s. Is 0.5 s before the first re-pick right?
- **Top B**: tap = new piece (on release); hold 0.6 s = COMPARE; hold + a key = load that slot; aux + hold + key =
  save. Does a tap ever turn into COMPARE by accident? Is 0.6 s right?
- **Aux + top A** (ANCHOR): set, change a few knobs, glide back. Is 8 s (SETUP 15) a good default?
- **Low F** twice: SENDS 1, then SENDS 2. **Low F#**: PERFORM.
- **Root**: hold low G and play a note on the keyboard: does the next key arrive at the next chord?
- The MIX view (low D#): is the framed column with its value readable at arm's length?

## 3. The sound

- **Harm at 0** (PERFORM knob 4): start five new pieces. Pleasing? Too sweet, too static? Then Harm 50 % and 100 %:
  does it drift out the way you want, and come back when you turn it down?
- **The factory pieces**: hold top B and press low C, C#, D, D#, E, F (slots 1-6: Dawn, Night river, Glass, Pulse,
  Deep, Frost). Each a minute or two. Any that should change?
- **Frost drone** and **Beat pads**: their level against the other drones and pad types.
- **GLINT** at 30 % and 100 %: too loud, too quiet, too high (+1 / +2 / +3 octaves)?
- **Hall and Bloom** at the default Mix: the Hall was turned down about 6 dB (it was louder than designed on most
  pieces). Does it now sit right?
- **DUCK** at 100 %: the piece dips to a quarter under your notes. Too much?

## 4. If something is off

Note the page, the settings and what you heard, and save the piece to a slot (hold aux and top B, press a key) so it
can be reproduced. `saves.txt` in the patch folder holds it.
