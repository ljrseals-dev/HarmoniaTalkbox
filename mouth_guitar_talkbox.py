"""Guitar-string-driven mouth (talk box): plucked-string excitation -> corrected Kelly-Lochbaum vocal tract.
python mouth_guitar_talkbox.py  -> writes mouth_guitar_demo.wav and prints the verification table."""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import mouth_tract as M
import harmonia_guitar as G
FS = 48000
REF = {'ah': (730, 1090), 'eh': (530, 1840), 'ee': (270, 2290), 'oh': (570, 840), 'oo': (300, 870)}

def render(notes, vowels, glide=0.08, step=0.5, tail=0.8):
    """notes: MIDI numbers, vowels: 0..1 positions (ah=0 .. oo=1), one per note."""
    n = int(FS * (len(notes) * step + tail)); src = np.zeros(n); curve = np.zeros(n)
    for i, (m, v) in enumerate(zip(notes, vowels)):
        p = G.pluck(m, step + tail, 0.9, FS, seed=i); a = int(i * step * FS); src[a:a + len(p)] += p[:n - a]
        curve[a:] = v
    curve = signal.lfilter([1 - np.exp(-1 / (glide * FS))], [1, -np.exp(-1 / (glide * FS))], curve)   # glide between vowels
    y = M.Tract().process(src, curve); return y / np.max(np.abs(y)) * 0.7, src

def tract_gain_db(vowel, n=1 << 14):
    """Exact magnitude response of the tract (dB) from its impulse response; returns (freqs, dB)."""
    imp = np.zeros(n); imp[0] = 1.0; h = M.Tract().process(imp, np.full(n, vowel), block=n)
    return np.fft.rfftfreq(n, 1 / FS), 20 * np.log10(np.abs(np.fft.rfft(h)) + 1e-12)

def lti_consistency(midi, vowel, fmax=4000.0, floor_db=-45.0):
    """For a held vowel the tract is a fixed filter, so every harmonic of the string must be scaled by the tract's gain at that
    frequency. Returns the per-harmonic error (dB) between measured output/source and the impulse-response gain."""
    y, src = render([midi], [vowel], glide=1e-3, step=0.4, tail=0.2); a, b = int(0.1 * FS), int(0.5 * FS)
    w = np.hanning(b - a); Y = np.abs(np.fft.rfft(y[a:b] * w, 1 << 16)); S = np.abs(np.fft.rfft(src[a:b] * w, 1 << 16)); fr = np.fft.rfftfreq(1 << 16, 1 / FS)
    f0 = 440 * 2 ** ((midi - 69) / 12); fh, gh = tract_gain_db(vowel); raw = Y / (np.max(np.abs(y)) / 0.7)   # undo the render's normalisation
    err = []
    for k in range(1, int(fmax / f0)):
        i = int(np.argmin(np.abs(fr - k * f0))); j = slice(max(i - 3, 0), i + 4); s_k = S[j].max()
        if 20 * np.log10(s_k / S.max() + 1e-12) < floor_db: continue
        meas = 20 * np.log10(raw[j].max() / s_k); err.append(meas - np.interp(k * f0, fh, gh))
    err = np.array(err); return err - np.median(err)          # remove the constant render gain; what is left is shape error

if __name__ == "__main__":
    print("== tract resonances after fitting (impulse response) vs targets ==")
    for i, v in enumerate(M.ORDER): print(f"  {v}: {M.formants(i / 4)}   target F1,F2 {REF[v]}")
    print("\n== rendered guitar vs the tract's own response: per-harmonic shape error (dB, constant gain removed) ==")
    worst = 0.0
    for midi in (45, 52):
        for i, v in enumerate(M.ORDER):
            e = lti_consistency(midi, i / 4); worst = max(worst, float(np.max(np.abs(e))))
            print(f"  midi {midi} {v}: {len(e)} harmonics, median |err| {np.median(np.abs(e)):.2f} dB, max |err| {np.max(np.abs(e)):.2f} dB")
    print(f"  worst harmonic error over all notes: {worst:.2f} dB  ({'OK' if worst < 1.5 else 'CHECK'})")
    notes = [40, 47, 52, 55, 59, 55, 52, 47]; vow = [0, .25, .5, .75, 1.0, .75, .5, 0]
    y, src = render(notes, vow); wavfile.write("mouth_guitar_demo.wav", FS, (y * 32767).astype(np.int16))
    print(f"\nwrote mouth_guitar_demo.wav ({len(y)/FS:.1f} s), peak {20*np.log10(np.max(np.abs(y))):.1f} dBFS; finite: {bool(np.all(np.isfinite(y)))}")
