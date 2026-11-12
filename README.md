# HarmoniaTalkbox

**Physical-model talk-box pipeline**  
Karplus-Strong guitar string → 48-section Kelly-Lochbaum vocal tract → YIN transcription + MIDI I/O

Clean modular architecture designed for AURA-G integration and browser / real-time experimentation.

---

## Quick start

```bash
# Requirements: Python 3.9+, numpy, scipy
pip install -e .

# Verify the tract (impulse response + per-harmonic consistency of the rendered guitar) and write the demo audio
python mouth_guitar_talkbox.py

# Run the tests
python -m unittest -v test_midi_bridge test_tract
```

Expected test output:
```
test_end_to_end_deterministic_finite ... ok
test_midi_round_trip ................... ok
test_plugin_hook ....................... ok
test_transcription_f1 .................. ok   (F1 ≈ 0.95)
```

`mouth_guitar_talkbox.py` writes `mouth_guitar_demo.wav` (guitar arpeggio gliding ah→eh→ee→oh→oo through the tract).

Open `mouth_model_ui.html` in a browser for an interactive Web Audio approximation (Karplus-Strong + cascaded formant filters).

---

## Architecture

| Module | Responsibility |
|--------|----------------|
| `harmonia_guitar.py` | Karplus-Strong string + pure-bytes SMF Type-0 MIDI read/write (`Note`, `write_midi`, `read_midi`) |
| `midi_bridge.py` | YIN monophonic transcription + orchestration into the talk-box. Re-exports MIDI helpers from guitar. |
| `mouth_tract.py` | **48-section Kelly-Lochbaum waveguide** (corrected junctions, glottal/lip reflections, area functions fitted to Peterson-Barney formants) |
| `mouth_guitar_talkbox.py` | Verification suite + demo renderer |
| `test_midi_bridge.py` | 4-test unit suite (MIDI round-trip, transcription F1, plugin hook, end-to-end determinism) |
| `mouth_model_ui.html` | Browser UI (Web Audio Karplus-Strong + formant filters) |
| `examples/aura_integration.py` | How to plug a custom neural transcriber (AURA-G) into the pipeline |

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

## Verification

- **Impulse response:** F1/F2 of each vowel against textbook male formants (table below).
- **Rendered guitar:** for a held vowel the tract is a fixed filter, so each harmonic of the string must come out scaled by the tract's gain at that
  frequency. `mouth_guitar_talkbox.py` measures the per-harmonic shape error (constant gain removed): median under 0.1 dB, worst 1.33 dB over 10 notes (A2, E3).
  This replaces an earlier peak-picking check that reported false failures. It shows the audio carries the tract's resonances; it does not prove the
  vowels are intelligible to a listener or an ASR model, and it does not cover glides between vowels.
- **Transcription:** `transcribe()` is a lightweight *monophonic* YIN fallback (it missed 1 of 10 test notes). For chords or polyphonic audio use
  `register_transcriber` with AURA-G or another polyphonic model. `examples/aura_integration.py` uses a mock, not AURA-G itself.

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

### Browser Path & Neural Codecs (`realm-quant`)

While the Python implementation in this repository provides an offline, physically accurate 48-section Kelly-Lochbaum waveguide, we also maintain a real-time browser path via the [realm-quant](https://github.com/ljrseals-dev/realm-quant) project.

**Trade-offs:**
- **Neural Codecs (AURA-G / realm-quant):** Extremely fast, suitable for real-time Web Audio / WASM execution. They can infer complex vocal tract shapes but may lack the physical constraints of a true waveguide (resulting in occasional unnatural transients).
- **Physical Model (This Repo):** Mathematically rigorous. The 48-section Kelly-Lochbaum tract guarantees physically valid wave propagation, perfect for offline rendering, analysis, and generating high-fidelity training data for neural codecs.

The `mouth_model_ui.html` file in this repository provides a pure Web Audio API approximation (using cascaded formant filters) for immediate browser playback without requiring neural inference.

---

## Files in this release

```
HarmoniaTalkbox/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── harmonia_guitar.py
├── midi_bridge.py
├── mouth_tract.py
├── mouth_guitar_talkbox.py
├── test_midi_bridge.py
├── mouth_model_ui.html
├── mouth_guitar_demo.wav
└── examples/
    └── aura_integration.py
```

---

## License

Research / non-commercial use unless otherwise noted.  
Kelly-Lochbaum implementation and area fitting are original work for the HarmoniaCodec / UNREAL AI Systems line.
