"""
harmonia_guitar.py
------------------
A self-contained guitar string physical model (Karplus-Strong) 
plus Standard MIDI File (SMF) Type-0 read/write utilities.
"""
import struct
from dataclasses import dataclass
import numpy as np

# ==========================================
# 1. Data Structures
# ==========================================
@dataclass
class Note:
    start: float   # seconds
    dur: float     # seconds
    midi: int
    vel: int = 90

# ==========================================
# 2. Audio Synthesis (Karplus-Strong)
# ==========================================
def pluck(midi: int, dur: float, vel: float, fs: int, seed=None) -> np.ndarray:
    """
    Synthesize a plucked string note using the Karplus-Strong algorithm.
    midi: MIDI note number (0-127)
    dur: duration in seconds
    vel: velocity (0.0 to 1.0)
    fs: sample rate
    seed: random seed for reproducibility
    """
    if seed is not None:
        np.random.seed(seed)
        
    freq = 440.0 * (2.0 ** ((midi - 69) / 12.0))
    n_samples = int(fs * dur)
    
    # Delay line length (period)
    N = max(2, int(round(fs / freq)))
    
    # Excitation: white noise burst
    # Blend in velocity to affect initial amplitude
    noise = (np.random.rand(N) * 2.0) - 1.0
    out = np.zeros(n_samples)
    
    # Fill the buffer with the initial noise
    out[:N] = noise * (vel ** 1.5)
    
    # Karplus-Strong feedback loop (averaging filter)
    for i in range(N, n_samples):
        out[i] = 0.5 * (out[i - N] + out[i - N - 1]) * 0.996
        
    return out

# ==========================================
# 3. MIDI File I/O Utilities
# ==========================================
def _vlq(v):
    """Encode an integer as a MIDI Variable Length Quantity."""
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    return bytes(reversed(out))

def _read_vlq(data, q):
    """Read a MIDI Variable Length Quantity from bytes at index q."""
    v = 0
    while True:
        b = data[q]
        q += 1
        v = (v << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    return v, q

def _build_midi_bytes(notes, bpm=120, tpq=480):
    """Pure bytes builder for a Standard MIDI File (Type-0)."""
    ev = []
    for n in notes:
        t0 = int(round(n.start * tpq * bpm / 60))
        t1 = int(round((n.start + n.dur) * tpq * bpm / 60))
        ev += [
            (t0, 1, bytes([0x90, n.midi, n.vel])), # Note On
            (t1, 0, bytes([0x80, n.midi, 0]))      # Note Off
        ]
    
    # Sort events chronologically (Note Offs before Note Ons at same time)
    ev.sort(key=lambda e: (e[0], e[1]))
    
    # Build Track data
    trk = _vlq(0) + bytes([0xFF, 0x51, 3]) + struct.pack(">I", int(60e6 / bpm))[1:]
    last = 0
    for t, _, msg in ev:
        trk += _vlq(t - last) + msg
        last = t
    trk += _vlq(0) + bytes([0xFF, 0x2F, 0]) # End of Track
    
    # Build Header and wrap Track
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, tpq) + b"MTrk" + struct.pack(">I", len(trk)) + trk

def write_midi(path, notes, bpm=120, tpq=480):
    """Write a list of Note objects to a MIDI file."""
    data = _build_midi_bytes(notes, bpm=bpm, tpq=tpq)
    with open(path, "wb") as f:
        f.write(data)

def _read_midi_impl(d):
    """Parse bytes of a Standard MIDI File into a list of Note objects."""
    assert d[:4] == b"MThd"
    _, fmt, ntrk, div = struct.unpack(">IHHH", d[4:14])
    p = 14
    tempo = 500000
    notes = []
    open_notes = {}
    
    for _ in range(ntrk):
        assert d[p:p + 4] == b"MTrk"
        ln = struct.unpack(">I", d[p + 4:p + 8])[0]
        q = p + 8
        end = q + ln
        t = 0
        run = 0
        
        while q < end:
            v, q = _read_vlq(d, q)
            t += v
            s = d[q]
            
            if s == 0xFF: # Meta event
                typ = d[q + 1]
                ln_meta = d[q + 2]
                q += 3
                if typ == 0x51: # Tempo
                    tempo = int.from_bytes(d[q:q + 3], "big")
                q += ln_meta
                continue
                
            if s in (0xF0, 0xF7): # SysEx
                ln_sysex = d[q + 1]
                q += 2 + ln_sysex
                continue
                
            if s & 0x80: # Explicit Status
                run = s
                q += 1
                
            st = run
            c1 = d[q]
            q += 1
            
            if (st & 0xF0) in (0xC0, 0xD0): # 1-byte messages
                continue
                
            c2 = d[q]
            q += 1
            sec = t * tempo / 1e6 / div
            
            if (st & 0xF0) == 0x90 and c2 > 0:
                open_notes[(st & 0x0F, c1)] = (sec, c2)
            elif (st & 0xF0) == 0x80 or ((st & 0xF0) == 0x90 and c2 == 0):
                k = (st & 0x0F, c1)
                if k in open_notes:
                    s0, vel = open_notes.pop(k)
                    notes.append(Note(s0, sec - s0, c1, vel))
        p = end
        
    return sorted(notes, key=lambda n: (n.start, n.midi))

def read_midi(path):
    """Read a MIDI file and return a sorted list of Note objects."""
    with open(path, "rb") as f:
        return _read_midi_impl(f.read())

# ==========================================
# 4. Verification (Run directly)
# ==========================================
if __name__ == "__main__":
    import os, tempfile
    
    test_notes = [
        Note(0.0, 1.0, 60, 100),
        Note(0.5, 0.8, 64, 90),
        Note(1.0, 1.5, 67, 80)
    ]
    
    p = os.path.join(tempfile.gettempdir(), "test_guitar.mid")
    write_midi(p, test_notes)
    
    print(f"wrote {os.path.getsize(p)} bytes")
    got = read_midi(p)
    for n in got:
        print(f"  start={n.start:0.3f} dur={n.dur:0.3f} midi={n.midi} vel={n.vel}")
        
    assert len(got) == len(test_notes)
    print("round-trip OK")
