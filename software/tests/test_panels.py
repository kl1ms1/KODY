import unittest

from kody.panels import CORE_PRODUCT, Status, check, report, simulated_inputs


def by_key(results):
    return {r.panel.key: r for r in results}


class PanelsTest(unittest.TestCase):
    def test_everything_present(self):
        res = check(*simulated_inputs())
        self.assertTrue(all(r.status is Status.OK for r in res))
        self.assertIn("4 из 4", report(res))

    def test_radio_cartridge_missing(self):
        res = by_key(check(*simulated_inputs(frozenset({"radio"}))))
        self.assertIs(res["radio"].status, Status.MISSING)
        self.assertIs(res["screen"].status, Status.OK)

    def test_chip_silent_on_main_board(self):
        present, hat, rp = simulated_inputs()
        present.discard(0x6B)  # гироскоп не отвечает
        res = by_key(check(present, hat, rp))
        self.assertIs(res["main"].status, Status.PARTIAL)
        self.assertIn("LSM6DSV16X", res["main"].problems[0])

    def test_main_board_detected_by_hat_eeprom(self):
        present, _, rp = simulated_inputs()
        self.assertIs(by_key(check(present, None, rp))["main"].status, Status.MISSING)
        self.assertIs(by_key(check(present, CORE_PRODUCT + "\x00", rp))["main"].status, Status.OK)

    def test_rp2040_silent(self):
        present, hat, _ = simulated_inputs()
        self.assertIs(by_key(check(present, hat, False))["radio"].status, Status.PARTIAL)

    def test_battery_gauge_silent(self):
        present, hat, rp = simulated_inputs()
        present.discard(0x36)
        self.assertIs(by_key(check(present, hat, rp))["power"].status, Status.PARTIAL)


if __name__ == "__main__":
    unittest.main()
