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

def log_envelope(x, fs=FS, fmax=3500):
    N = len(x); S = np.abs(np.fft.rfft(x * np.hanning(N), 1 << 17)); f = np.fft.rfftfreq(1 << 17, 1 / fs)
    c = np.fft.irfft(np.log(S + 1e-12)); lift = np.zeros_like(c); q = int(fs / 400); lift[:q] = 1; lift[-q:] = 1   # cepstral envelope
    return f, np.fft.rfft(c * lift).real

def tract_peaks(out, src, fs=FS, fmax=3500, k=2):
    """Peaks of (output envelope - source envelope): the tract's own response, with the string's spectral tilt removed."""
    f, eo = log_envelope(out, fs); _, es = log_envelope(src, fs); d = (eo - es); m = (f < fmax) & (f > 100)
    pk, _ = signal.find_peaks(d[m], prominence=0.3); return [round(float(f[m][p])) for p in pk[:k]]

if __name__ == "__main__":
    print("== tract resonances after fitting (impulse response) vs targets ==")
    for i, v in enumerate(M.ORDER): print(f"  {v}: {M.formants(i / 4)}   target F1,F2 {REF[v]}")
    print("\n== guitar string through the tract: tract response (output/source) at A2 (110 Hz) and E3 (165 Hz) ==")
    for midi in (45, 52):
      for i, v in enumerate(M.ORDER):
        y, src = render([midi], [i / 4], glide=1e-3, step=0.4, tail=0.2); a, b = int(0.1 * FS), int(0.5 * FS); pk = tract_peaks(y[a:b], src[a:b])
        ok = len(pk) >= 2 and all(abs(pk[j] / REF[v][j] - 1) < 0.25 for j in range(2)); print(f"  midi {midi} {v}: tract peaks {pk} vs {REF[v]}  {'OK' if ok else 'off by >25%'}")
    notes = [40, 47, 52, 55, 59, 55, 52, 47]; vow = [0, .25, .5, .75, 1.0, .75, .5, 0]
    y, src = render(notes, vow); wavfile.write("mouth_guitar_demo.wav", FS, (y * 32767).astype(np.int16))
    print(f"\nwrote mouth_guitar_demo.wav ({len(y)/FS:.1f} s), peak {20*np.log10(np.max(np.abs(y))):.1f} dBFS; finite: {bool(np.all(np.isfinite(y)))}")
