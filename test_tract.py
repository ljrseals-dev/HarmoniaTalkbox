import unittest
import numpy as np
import mouth_tract as M
import mouth_guitar_talkbox as T

class TractTests(unittest.TestCase):
    def test_impulse_formants_within_12_percent(self):
        for i, v in enumerate(M.ORDER):
            f = M.formants(i / 4); self.assertGreaterEqual(len(f), 2, v)
            for k in range(2): self.assertLess(abs(f[k] / T.REF[v][k] - 1), 0.12, f"{v} F{k+1}={f[k]} target {T.REF[v][k]}")
    def test_rendered_guitar_follows_tract_response(self):
        for midi, i in ((45, 0), (52, 2), (45, 4)):
            e = T.lti_consistency(midi, i / 4); self.assertGreater(len(e), 10); self.assertLess(float(np.max(np.abs(e))), 1.5)
if __name__ == "__main__": unittest.main(verbosity=2)
