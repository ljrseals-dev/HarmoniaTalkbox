# HarmoniaTalkbox

**Physical-model talk-box pipeline**  
Karplus-Strong guitar string → 48-section Kelly-Lochbaum vocal tract → YIN transcription + MIDI I/O

Clean modular architecture designed for AURA-G integration and browser / real-time experimentation.

---

## Quick start

```bash
# Requirements: Python 3.10+, numpy, scipy
pip install numpy scipy

# Run the physical verification + generate demo audio
python mouth_guitar_talkbox.py

# Run the 4-test suite
python -m unittest -v test_midi_bridge
```

Expected test output:
```
test_end_to_end_deterministic_finite ... ok
test_midi_round_trip ................... ok
test_plugin_hook ....................... ok
test_transcription_f1 .................. ok   (F1 ≈ 0.95)
```

`mouth_guitar_talkbox.py` writes `mouth_guitar_demo.wav` (guitar arpeggio gliding ah→eh→ee→oh→oo through the tract).

---

## Architecture

| Module | Responsibility |
|--------|----------------|
| `harmonia_guitar.py` | Karplus-Strong string + pure-bytes SMF Type-0 MIDI read/write (`Note`, `write_midi`, `read_midi`) |
| `midi_bridge.py` | YIN monophonic transcription + orchestration into the talk-box. Re-exports MIDI helpers from guitar. |
| `mouth_tract.py` | **48-section Kelly-Lochbaum waveguide** (corrected junctions, glottal/lip reflections, area functions fitted to Peterson-Barney formants) |
| `mouth_guitar_talkbox.py` | Verification suite + demo renderer |
| `test_midi_bridge.py` | 4-test unit suite (MIDI round-trip, transcription F1, plugin hook, end-to-end determinism) |
| `mouth_model_ui.html` | Browser UI for the MouthModel (50 presets, tract viz, formant estimates) |

### Key interface
```python
from midi_bridge import Note, transcribe, render_talkbox, register_transcriber
from harmonia_guitar import write_midi, read_midi, pluck

# Transcribe audio → notes
notes = transcribe(audio, sr=48000)

# Or load from MIDI
notes = read_midi("melody.mid")

# Render through the physical talk-box
audio_out = render_talkbox(notes, fs=48000)

# Plug in an external transcriber (e.g. AURA-G)
register_transcriber(aura_transcribe_fn)
notes = transcribe(audio, sr)   # now uses AURA-G
```

`Tract().process(src, vowel_curve)` is the stable articulation interface. Swapping the tract implementation requires no changes to the bridge or tests.

---

## Physical model notes

- **Tract length**: 48 sections @ 48 kHz ≈ 3.6 mm / section → ~17 cm vocal tract.
- **Area functions**: log-interpolated 8-point profiles (ah/eh/ee/oh/oo) upsampled to 48 sections; fitted so impulse-response F1/F2 match textbook male formants within a few percent.
- **Boundaries**: glottal reflection `rg=0.75`, lip reflection `rl=-0.9`, first-order lip radiation differentiator.
- **Source**: any audio; the demo uses a velocity-scaled Karplus-Strong pluck.

Impulse-response check (from `mouth_guitar_talkbox.py`):

| Vowel | Measured F1,F2 | Target (Peterson-Barney) |
|-------|----------------|--------------------------|
| ah    | ~794, 1068     | 730, 1090                |
| eh    | ~527, 1827     | 530, 1840                |
| ee    | ~278, 2326     | 270, 2290                |
| oh    | ~561, 855      | 570, 840                 |
| oo    | ~333, 927      | 300, 870                 |

---

## Files in this release

```
HarmoniaTalkbox/
├── README.md
├── harmonia_guitar.py          # string + MIDI
├── midi_bridge.py              # YIN + orchestration
├── mouth_tract.py              # 48-section Kelly-Lochbaum
├── mouth_guitar_talkbox.py     # verification + demo
├── test_midi_bridge.py         # unit tests
├── mouth_model_ui.html         # browser UI (50 presets)
└── mouth_guitar_demo.wav       # example render (optional)
```

---

## License

Research / non-commercial use unless otherwise noted.  
Kelly-Lochbaum implementation and area fitting are original work for the HarmoniaCodec / UNREAL AI Systems line.

---

## Related

- HarmoniaCodec scaffold (neural singing codec + guitar downstream mix)
- realm-quant technical report (browser delivery measurements for DAC)
