import unittest

from kody.panels import CORE_PRODUCT, Status, check, report, simulated_inputs


def by_key(results):
    return {r.panel.key: r for r in results}


class PanelsTest(unittest.TestCase):
    def test_everything_present(self):
        res = check(*simulated_inputs())
        self.assertTrue(all(r.status is Status.OK for r in res))
        self.assertIn("7 из 7", report(res))

    def test_missing_panel(self):
        res = by_key(check(*simulated_inputs(frozenset({"right"}))))
        self.assertIs(res["right"].status, Status.MISSING)
        self.assertIs(res["screen"].status, Status.OK)

    def test_panel_inserted_but_chip_silent(self):
        present, hat, rp = simulated_inputs()
        present.discard(0x15)  # тач не отвечает
        res = by_key(check(present, hat, rp))
        self.assertIs(res["screen"].status, Status.PARTIAL)
        self.assertIn("CST816", res["screen"].problems[0])

    def test_core_detected_by_hat_eeprom(self):
        present, _, rp = simulated_inputs()
        self.assertIs(by_key(check(present, None, rp))["core"].status, Status.MISSING)
        self.assertIs(by_key(check(present, CORE_PRODUCT + "\x00", rp))["core"].status, Status.OK)

    def test_rp2040_silent(self):
        present, hat, _ = simulated_inputs()
        self.assertIs(by_key(check(present, hat, False))["back"].status, Status.PARTIAL)


if __name__ == "__main__":
    unittest.main()
