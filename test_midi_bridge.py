import os, tempfile, unittest
import numpy as np
import midi_bridge as B, harmonia_guitar as G

SR = 44100
def synth(notes, sr=SR):
    n = int(sr * (max(x.start + x.dur for x in notes) + 0.3)); y = np.zeros(n)
    for i, x in enumerate(notes):
        p = G.pluck(x.midi, x.dur, 0.8, sr, seed=i); a = int(x.start * sr); y[a:a + len(p)] += p[:n - a]
    return y

REF = [B.Note(0.1 + 0.45 * i, 0.4, m, 90) for i, m in enumerate([52, 55, 59, 57, 55, 52, 50, 47, 64, 62])]

class T(unittest.TestCase):
    def test_midi_round_trip(self):
        p = os.path.join(tempfile.gettempdir(), "rt.mid")
        B.write_midi(p, REF)
        got = B.read_midi(p)
        self.assertEqual([(g.midi, g.vel) for g in got], [(r.midi, r.vel) for r in REF])
        for g, r in zip(got, REF): 
            self.assertAlmostEqual(g.start, r.start, delta=0.002)
            self.assertAlmostEqual(g.dur, r.dur, delta=0.002)

    def test_transcription_f1(self):
        est = B.transcribe(synth(REF), SR)
        tp = 0; used = set()
        for r in REF:
            for j, e in enumerate(est):
                if j not in used and e.midi == r.midi and abs(e.start - r.start) < 0.06:
                    tp += 1; used.add(j); break
        prec = tp / max(len(est), 1)
        rec = tp / len(REF)
        f1 = 2 * prec * rec / max(prec + rec, 1e-9)
        print(f"  transcription: {tp}/{len(REF)} notes matched, {len(est)} estimated, F1 {f1:.2f}")
        self.assertGreaterEqual(f1, 0.9)

    def test_plugin_hook(self):
        B.register_transcriber(lambda a, sr: [(0.0, 0.5, 60, 100)])
        try_notes = B.transcribe(np.zeros(1000), SR)
        B.register_transcriber(None)
        self.assertEqual((try_notes[0].midi, try_notes[0].vel), (60, 100))

    def test_end_to_end_deterministic_finite(self):
        a = B.render_talkbox(REF[:4])
        b = B.render_talkbox(REF[:4])
        self.assertTrue(np.all(np.isfinite(a)))
        self.assertTrue(np.array_equal(a, b))
        self.assertLessEqual(np.max(np.abs(a)), 0.7001)

if __name__ == "__main__":
    unittest.main(verbosity=2)
