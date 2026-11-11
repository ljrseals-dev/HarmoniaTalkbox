"""MIDI bridge: audio or MIDI file -> notes -> guitar string -> talk-box mouth.
 - transcribe(audio, sr): monophonic YIN transcriber.
 - render_talkbox(notes): plucked string through the corrected Kelly-Lochbaum tract.
 - Exposes Note, read_midi, and write_midi by importing them from harmonia_guitar.
"""
import numpy as np
from scipy import signal

# Import the shared structures and MIDI I/O from our standalone module
from harmonia_guitar import Note, write_midi, read_midi

# ---------------------------------------------------------------- transcription
_TRANSCRIBER = None

def register_transcriber(fn):
    """fn(audio: np.ndarray, sr: int) -> list[Note | (start, dur, midi, vel)]. 
    Use this to plug in AURA-G's transcription."""
    global _TRANSCRIBER
    _TRANSCRIBER = fn

def _yin(frame, sr, fmin=70.0, fmax=1200.0, thr=0.15):
    """YIN fundamental frequency estimator."""
    n = len(frame)
    tmax = int(sr / fmin)
    tmin = max(2, int(sr / fmax))
    
    fft = np.fft.rfft(frame, 2 * n)
    acf = np.fft.irfft(fft * np.conj(fft))[:tmax + 1]
    
    d = np.zeros(tmax + 1)
    sq = np.cumsum(np.r_[0, frame ** 2])
    for tau in range(1, tmax + 1):
        d[tau] = (sq[n - tau] + (sq[n] - sq[tau])) - 2 * acf[tau]
        
    cm = np.ones(tmax + 1)
    run = np.cumsum(d[1:])
    cm[1:] = d[1:] * np.arange(1, tmax + 1) / np.maximum(run, 1e-12)
    
    for tau in range(tmin, tmax):
        if cm[tau] < thr:
            while tau + 1 < tmax and cm[tau + 1] < cm[tau]:
                tau += 1
            a, b, c = cm[tau - 1], cm[tau], cm[tau + 1]
            den = a - 2 * b + c
            t = tau + (0.5 * (a - c) / den if den != 0 else 0.0)
            return sr / t, float(cm[tau])
    return 0.0, 1.0

def transcribe(audio, sr, hop=0.01, win=0.046, min_note=0.06, gate_db=-45.0):
    """Extract Note objects from an audio array."""
    if _TRANSCRIBER is not None:
        return [n if isinstance(n, Note) else Note(*n) for n in _TRANSCRIBER(audio, sr)]
        
    x = np.asarray(audio, dtype=np.float64)
    H = int(hop * sr)
    W = int(win * sr)
    pk = np.max(np.abs(x)) + 1e-12
    midis, rms = [], []
    
    for i in range(0, len(x) - W, H):
        f = x[i:i + W]
        r = np.sqrt(np.mean(f ** 2))
        rms.append(r)
        
        if 20 * np.log10(r / pk + 1e-12) > gate_db:
            f0, cm = _yin(f * np.hanning(W), sr)
        else:
            f0, cm = 0.0, 1.0
            
        midis.append(69 + 12 * np.log2(f0 / 440.0) if f0 > 0 and cm < 0.2 else np.nan)
        
    midis = np.array(midis)
    notes = []
    i = 0
    N = len(midis)
    
    while i < N:
        if np.isnan(midis[i]):
            i += 1
            continue
            
        j = i
        seg = [midis[i]]
        
        while j + 1 < N and not np.isnan(midis[j + 1]) and abs(midis[j + 1] - np.median(seg[-5:])) < 0.7:
            j += 1
            seg.append(midis[j])
            
        dur = (j - i + 1) * hop
        if dur >= min_note:
            lvl = np.mean(rms[i:j + 1]) / pk
            vel = int(np.clip(40 + 87 * lvl ** 0.5, 20, 127))
            notes.append(Note(i * hop, dur, int(round(float(np.median(seg)))), vel))
        i = j + 1
        
    return notes

# ---------------------------------------------------------------- guitar + talk box
def render_talkbox(notes, fs=48000, octave_shift=0, tail=0.8, glide=0.04):
    """Pluck notes and pass them through the Talk-Box mouth tract."""
    import harmonia_guitar as G
    import mouth_tract as M
    
    if not notes: 
        return np.zeros(0)
        
    n = int(fs * (max(x.start + x.dur for x in notes) + tail))
    src = np.zeros(n)
    curve = np.zeros(n)
    
    for i, nt in enumerate(sorted(notes, key=lambda z: z.start)):
        a = int(nt.start * fs)
        # G.pluck now maps directly to our updated Karplus-Strong
        p = G.pluck(nt.midi + octave_shift, nt.dur + tail, 0.25 + 0.7 * nt.vel / 127, fs, seed=1000 + i)
        src[a:a + len(p)] += p[:n - a]
        
        # Vowel curve: pitch class determines the ah..oo axis
        curve[a:] = (nt.midi % 12) / 12.0
        
    # Apply a low-pass filter to smooth the curve transitions
    curve = signal.lfilter([1 - np.exp(-1 / (glide * fs))], [1, -np.exp(-1 / (glide * fs))], curve)
    
    y = M.Tract().process(src, curve)
    
    # Normalize
    return y / (np.max(np.abs(y)) + 1e-12) * 0.7
