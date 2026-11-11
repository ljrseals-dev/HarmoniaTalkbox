"""AURA-G Integration Example
------------------------------
This script demonstrates how to bypass the internal YIN transcriber and use
AURA-G's custom neural codec to drive the HarmoniaTalkbox physical model.
"""
import numpy as np
from scipy.io import wavfile
import midi_bridge as B
import harmonia_guitar as G

# 1. Define a mock AURA-G transcriber
# (Replace this with your actual AURA-G model inference function)
def aura_g_transcribe(audio, sr):
    print("-> [AURA-G] Analyzing audio and extracting notes...")
    # AURA-G returns notes: (start_time, duration, midi_note, velocity)
    # Here we return a hardcoded guitar riff
    return [
        (0.0, 0.3, 52, 100),  # E3
        (0.3, 0.3, 55, 100),  # G3
        (0.6, 0.3, 59, 100),  # B3
        (0.9, 0.6, 64, 110),  # E4
    ]

# 2. Register the custom transcriber
B.register_transcriber(aura_g_transcribe)

# 3. Create a dummy audio array (AURA-G ignores this and runs its own logic)
dummy_audio = np.zeros(48000)

# 4. Transcribe and Render
print("Transcribing with AURA-G...")
notes = B.transcribe(dummy_audio, 48000)
print(f"Extracted {len(notes)} notes.")

print("Rendering through physical talk-box...")
# We can pass the notes straight to the renderer!
y = B.render_talkbox(notes)

# 5. Save output
out_path = "aura_g_talkbox_demo.wav"
wavfile.write(out_path, 48000, (y * 32767).astype(np.int16))
print(f"Wrote {out_path} ({len(y)/48000:.2f} seconds)")
