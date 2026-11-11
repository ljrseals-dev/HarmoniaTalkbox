# Contributing to HarmoniaTalkbox

We welcome contributions! Here is how to get started.

## Development Setup
1. Clone the repo: `git clone https://github.com/ljrseals-dev/HarmoniaTalkbox.git`
2. Install in editable mode: `pip install -e .`
3. Run tests before submitting: `python -m unittest -v test_midi_bridge`

## Adding a New Vowel
The tract supports 5 primary vowels (`ah`, `eh`, `ee`, `oh`, `oo`). To add a new one:
1. Modify the `VOW` dictionary in `mouth_tract.py`.
2. Add the target formants (F1/F2) to the `REF` dictionary in `mouth_guitar_talkbox.py`.
3. Run `python mouth_guitar_talkbox.py` to verify the new impulse response aligns with your target.

## Changing the Tract Resolution
The tract currently uses `N = 48` sections. If you increase `N`, you must re-fit the `VOW` area functions to maintain the correct formant frequencies.

## Code style
- Prefer pure NumPy / SciPy; avoid heavy frameworks in the core path.
- Keep the `Tract().process(src, vowel_curve)` interface stable.
- All public MIDI helpers live in `harmonia_guitar.py` and are re-exported by `midi_bridge`.
