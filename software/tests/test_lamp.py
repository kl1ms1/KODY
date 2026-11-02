import time
import unittest

from kody.hal import SimulatedPWMLED
from kody.lamp import PRESETS, Lamp, LampPreset, nearest_e12_above, wiring_advice
from kody.pins import PINS, PinUnavailable, check_user_pin, user_pins


class PinsTest(unittest.TestCase):
    def test_all_28_gpio_mapped_with_unique_physical_pins(self):
        self.assertEqual(sorted(PINS), list(range(28)))
        self.assertEqual(len({p.phys for p in PINS.values()}), 28)

    def test_free_pins(self):
        self.assertEqual([p.bcm for p in user_pins()], [14, 15, 17, 18, 7, 19, 16, 26, 20, 21])

    def test_reserved_and_shared_rejected(self):
        for bcm in (8, 2, 0, 99):
            with self.assertRaises(PinUnavailable):
                check_user_pin(bcm)

    def test_disabling_haptics_frees_vibro_pin(self):
        with self.assertRaises(PinUnavailable):
            check_user_pin(12)
        self.assertEqual(check_user_pin(12, frozenset({"haptics"})).phys, 32)


class AdviceTest(unittest.TestCase):
    def test_e12(self):
        self.assertEqual(nearest_e12_above(86.7), 100)
        self.assertEqual(nearest_e12_above(100), 100)
        self.assertEqual(nearest_e12_above(1300), 1500)

    def test_red_led_current_within_gpio_limit(self):
        a = wiring_advice(PRESETS[0])
        self.assertTrue(a.direct)
        self.assertLessEqual(a.current_ma, 16)
        self.assertEqual(a.resistor_ohm, 100)  # (3.3-2.0)/15мА = 86.7 → 100 Ом

    def test_high_voltage_needs_driver(self):
        for p in PRESETS[-2:]:
            self.assertFalse(wiring_advice(p).direct)

    def test_custom_led_too_much_current_is_capped(self):
        a = wiring_advice(LampPreset("x", 2.0, 50))
        self.assertLessEqual(a.current_ma, 16)


class LampTest(unittest.TestCase):
    def make(self, preset=PRESETS[0]):
        return Lamp(26, preset, lambda bcm: SimulatedPWMLED(bcm, render=False))

    def test_on_off_brightness(self):
        lamp = self.make()
        lamp.on()
        self.assertEqual(lamp.led.value, 1.0)
        lamp.on(0.3)
        self.assertAlmostEqual(lamp.led.value, 0.3)
        lamp.off()
        self.assertEqual(lamp.led.value, 0.0)
        lamp.close()

    def test_breathe_changes_brightness_over_time(self):
        lamp = self.make()
        lamp.breathe(period=0.4)
        seen = set()
        for _ in range(20):
            seen.add(round(lamp.led.value, 2))
            time.sleep(0.02)
        lamp.close()
        self.assertGreater(len(seen), 3)

    def test_relay_lamp_cannot_breathe(self):
        lamp = self.make(PRESETS[-1])
        with self.assertRaises(ValueError):
            lamp.breathe()
        lamp.close()

    def test_reserved_pin_refused(self):
        with self.assertRaises(PinUnavailable):
            Lamp(13, PRESETS[0], lambda bcm: SimulatedPWMLED(bcm, render=False))


if __name__ == "__main__":
    unittest.main()
