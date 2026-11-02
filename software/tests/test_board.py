import tempfile
import unittest

from kody.board import detect, profile_for_model


class BoardTest(unittest.TestCase):
    def test_zero_w_and_wh(self):
        p = profile_for_model("Raspberry Pi Zero W Rev 1.1\x00")
        self.assertEqual(p.key, "zero_w")
        self.assertFalse(p.sdr_waterfall)

    def test_zero_2w(self):
        p = profile_for_model("Raspberry Pi Zero 2 W Rev 1.0\x00")
        self.assertEqual((p.key, p.cores), ("zero_2w", 4))

    def test_unknown_pi_is_conservative(self):
        self.assertEqual(profile_for_model("Raspberry Pi 4 Model B Rev 1.4").key, "zero_w")

    def test_pc(self):
        self.assertTrue(profile_for_model(None).simulated)

    def test_detect_reads_file(self):
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"Raspberry Pi Zero 2 W Rev 1.0\x00")
        self.assertEqual(detect(f.name)[0].key, "zero_2w")
        self.assertEqual(detect("/nonexistent")[0].key, "pc")


if __name__ == "__main__":
    unittest.main()
