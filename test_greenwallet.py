# ══════════════════════════════════════════════════════════
# TEST SECTION 3: Helpers & Utilities (Ariba Khan — helpers.py)
# ══════════════════════════════════════════════════════════
class TestHelpers(unittest.TestCase):
    """Tests for tier classification, price fetching, demo portfolios."""

    def test_tier_sustainable_at_70(self):
        from helpers import tier
        label, css, color = tier(70)
        self.assertEqual(label, "Sustainable")
        self.assertEqual(css, "pg")

    def test_tier_sustainable_at_90(self):
        from helpers import tier
        label, _, _ = tier(90)
        self.assertEqual(label, "Sustainable")

    def test_tier_moderate_at_40(self):
        from helpers import tier
        label, _, _ = tier(40)
        self.assertEqual(label, "Moderate")

    def test_tier_moderate_at_55(self):
        from helpers import tier
        label, css, _ = tier(55)
        self.assertEqual(label, "Moderate")
        self.assertEqual(css, "py")

    def test_tier_high_risk_at_39(self):
        from helpers import tier
        label, _, _ = tier(39)
        self.assertEqual(label, "High Risk")

    def test_tier_high_risk_at_0(self):
        from helpers import tier
        label, css, _ = tier(0)
        self.assertEqual(label, "High Risk")
        self.assertEqual(css, "pr")

    def test_tier_returns_three_values(self):
        from helpers import tier
        result = tier(50)
        self.assertEqual(len(result), 3)

    def test_four_demo_portfolios_exist(self):
        from helpers import DEMOS
        self.assertEqual(len(DEMOS), 4)

    def test_tech_growth_has_5_stocks(self):
        from helpers import DEMOS
        self.assertEqual(len(DEMOS["Tech Growth Portfolio"]), 5)

    def test_balanced_has_5_stocks(self):
        from helpers import DEMOS
        self.assertEqual(len(DEMOS["Balanced Portfolio"]), 5)

    def test_clean_energy_has_5_stocks(self):
        from helpers import DEMOS
        self.assertEqual(len(DEMOS["Clean Energy Portfolio"]), 5)

    def test_blue_chip_has_5_stocks(self):
        from helpers import DEMOS
        self.assertEqual(len(DEMOS["Blue Chip Portfolio"]), 5)

    def test_all_demo_shares_positive(self):
        from helpers import DEMOS
        for name, stocks in DEMOS.items():
            for ticker, shares in stocks:
                self.assertGreater(shares, 0, f"{name}: {ticker} has {shares}")

    def test_all_demo_tickers_are_strings(self):
        from helpers import DEMOS
        for name, stocks in DEMOS.items():
            for ticker, shares in stocks:
                self.assertIsInstance(ticker, str)
