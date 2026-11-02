import unittest

from kody.orientation import OrientationTracker, tilt_to_accel


def feed(t, angle, n=10, flat=0.0):
    r = None
    for _ in range(n):
        r = t.update(*tilt_to_accel(angle, flat))
    return r


class OrientationTest(unittest.TestCase):
    def test_portrait_by_default(self):
        self.assertEqual(feed(OrientationTracker(), 0), 0)

    def test_turn_sideways_both_ways(self):
        t = OrientationTracker()
        self.assertEqual(feed(t, 90), 90)
        self.assertEqual(feed(t, 270), 270)
        self.assertEqual(feed(t, 180), 180)

    def test_hysteresis_keeps_portrait_at_55_degrees(self):
        t = OrientationTracker()
        self.assertEqual(feed(t, 55), 0)
        self.assertEqual(feed(t, 70), 90)

    def test_needs_to_hold(self):
        t = OrientationTracker(hold_samples=5)
        self.assertEqual(feed(t, 90, n=4), 0)
        self.assertEqual(feed(t, 90, n=1), 90)

    def test_short_shake_ignored(self):
        t = OrientationTracker(hold_samples=5)
        feed(t, 90, n=3)
        feed(t, 0, n=1)
        self.assertEqual(feed(t, 90, n=3), 0)

    def test_flat_on_table_keeps_rotation(self):
        t = OrientationTracker()
        feed(t, 90)
        self.assertEqual(feed(t, 0, flat=0.95), 90)


if __name__ == "__main__":
    unittest.main()
