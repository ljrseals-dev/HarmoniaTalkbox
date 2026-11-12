# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-11-11
### Changed
- Replaced the cepstral peak-picking audio check (6 of 10 false failures) with a per-harmonic consistency test against the tract's impulse-response gain.
### Added
- `test_tract.py` (formants within 12%; rendered guitar follows the tract response within 1.5 dB).
- README verification section and monophonic-transcriber note.

## [1.0.0] - 2026-11-11
### Added
- **Core Physical Model:** 48-section Kelly-Lochbaum vocal tract with lip radiation and glottal reflection.
- **Synthesis Engine:** Karplus-Strong plucked string excitation.
- **Transcription:** Monophonic YIN pitch tracker with `register_transcriber` hook for custom models (e.g., AURA-G).
- **MIDI I/O:** Self-contained Type-0 Standard MIDI File reader/writer.
- **UI / Demos:** `mouth_guitar_talkbox.py` verification suite and `mouth_model_ui.html` browser interface.
- **Tests:** 4-test `unittest` suite verifying MIDI round-trip, F1 transcription score, plugin hook, and deterministic rendering.
- **Packaging:** `pyproject.toml` for `pip install -e .`
- **AURA-G example:** `examples/aura_integration.py`
