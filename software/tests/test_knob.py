import unittest

from kody.knob import KnobRouter, accel


class KnobTest(unittest.TestCase):
    def test_spins_forever_both_ways_on_channels(self):
        k = KnobRouter(); k.open("radio")
        k.rotate(-1, 0.0)
        self.assertEqual(k.current.value, 69)          # с 1-го назад — на последний
        k.rotate(+1, 1.0)
        self.assertEqual(k.current.value, 1)
        self.assertIn("433.075", k.rotate(0, 2.0))

    def test_each_app_uses_it_differently(self):
        k = KnobRouter()
        k.open("subghz"); k.rotate(+1, 0.0)
        self.assertAlmostEqual(k.current.value, 433.925)
        k.open("lamp"); k.rotate(+2, 5.0)
        self.assertEqual(k.current.value, 60)
        self.assertEqual(k.press(), "вкл/выкл")

    def test_volume_on_hold_everywhere_with_stops(self):
        k = KnobRouter(); k.open("radio")
        for _ in range(20):
            k.hold_rotate(+1)
        self.assertEqual(k.volume.value, 100)
        self.assertEqual(k.current.value, 1)           # канал не сдвинулся

    def test_acceleration(self):
        self.assertEqual(accel(1, 0.5), 1)
        self.assertEqual(accel(1, 0.05), 3)
        self.assertEqual(accel(-1, 0.01), -10)
        k = KnobRouter(); k.open("subghz")
        k.rotate(+1, 0.0); k.rotate(+1, 0.01)          # быстро — шаг ×10
        self.assertAlmostEqual(k.current.value, 433.92 + 0.005 + 0.05)

    def test_long_press_goes_back(self):
        k = KnobRouter(); k.open("gps")
        self.assertEqual(k.long_press(), "назад в меню")
        self.assertEqual(k.app, "menu")


if __name__ == "__main__":
    unittest.main()
