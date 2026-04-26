# ══════════════════════════════════════════════════════════
# TEST SECTION 2: ESG Data Engine (Radhika Chopra — esg_engine.py)
# ══════════════════════════════════════════════════════════
class TestESGData(unittest.TestCase):
    """Tests for ESG dataset integrity and scoring accuracy."""

    def setUp(self):
        from esg_engine import KNOWN_ESG, get_esg
        self.known = KNOWN_ESG
        self.get_esg = get_esg

    def test_dataset_has_30_stocks(self):
        self.assertEqual(len(self.known), 30)

    def test_all_env_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[0] <= 100, f"{ticker} env={data[0]}")

    def test_all_soc_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[1] <= 100, f"{ticker} soc={data[1]}")

    def test_all_gov_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[2] <= 100, f"{ticker} gov={data[2]}")

    def test_all_composite_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[3] <= 100, f"{ticker} comp={data[3]}")

    def test_xom_low_environmental(self):
        self.assertLess(self.known["XOM"][0], 25)

    def test_cvx_low_environmental(self):
        self.assertLess(self.known["CVX"][0], 25)

    def test_msft_high_composite(self):
        self.assertGreater(self.known["MSFT"][3], 75)

    def test_aapl_high_composite(self):
        self.assertGreater(self.known["AAPL"][3], 70)

    def test_nee_high_environmental(self):
        self.assertGreater(self.known["NEE"][0], 85)

    def test_enph_high_environmental(self):
        self.assertGreater(self.known["ENPH"][0], 80)

    def test_every_stock_has_sector(self):
        for ticker, data in self.known.items():
            self.assertTrue(len(data[4]) > 0, f"{ticker} missing sector")

    def test_every_stock_has_explanation(self):
        for ticker, data in self.known.items():
            self.assertTrue(len(data[5]) > 0, f"{ticker} missing explanation")

    def test_get_esg_returns_known_data(self):
        e, s, g, comp, src, sector, expl = self.get_esg("AAPL")
        self.assertEqual(comp, 73)
        self.assertEqual(src, "MSCI/Sustainalytics")

    def test_get_esg_returns_7_values(self):
        result = self.get_esg("MSFT")
        self.assertEqual(len(result), 7)

    def test_unknown_ticker_doesnt_crash(self):
        result = self.get_esg("ZZZZZ")
        self.assertEqual(len(result), 7)
