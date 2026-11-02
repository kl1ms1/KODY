import unittest

from kody.panels import CORE_PRODUCT, Status, check, report, simulated_inputs


def by_key(results):
    return {r.panel.key: r for r in results}


class PanelsTest(unittest.TestCase):
    def test_everything_present(self):
        res = check(*simulated_inputs())
        self.assertTrue(all(r.status is Status.OK for r in res))
        self.assertIn("3 из 3", report(res))

    def test_back_board_missing(self):
        res = by_key(check(*simulated_inputs(frozenset({"back"}))))
        self.assertIs(res["back"].status, Status.MISSING)
        self.assertIs(res["screen"].status, Status.OK)

    def test_chip_silent_on_front_board(self):
        present, hat, back = simulated_inputs()
        present.discard(0x6B)
        res = by_key(check(present, hat, back))
        self.assertIs(res["front"].status, Status.PARTIAL)
        self.assertIn("LSM6DSV16X", res["front"].problems[0])

    def test_front_board_detected_by_hat_eeprom(self):
        present, _, back = simulated_inputs()
        self.assertIs(by_key(check(present, None, back))["front"].status, Status.MISSING)
        self.assertIs(by_key(check(present, CORE_PRODUCT + "\x00", back))["front"].status, Status.OK)

    def test_screen_without_touch(self):
        present, hat, back = simulated_inputs()
        present.discard(0x5D)
        self.assertIs(by_key(check(present, hat, back))["screen"].status, Status.MISSING)


if __name__ == "__main__":
    unittest.main()
