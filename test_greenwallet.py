# TEST SECTION 4: Score Calculation (Duaa Aamir — app.py)
# ══════════════════════════════════════════════════════════
class TestScoreCalculation(unittest.TestCase):
    """Tests for weighted Green Score math and risk flagging."""

    def test_equal_weight_score(self):
        pdata = [{"value":100,"esg":80}, {"value":100,"esg":60}]
        total = sum(s["value"] for s in pdata)
        score = sum(s["value"]*s["esg"] for s in pdata) / total
        self.assertEqual(score, 70.0)

    def test_heavy_weight_dominates(self):
        pdata = [{"value":900,"esg":80}, {"value":100,"esg":20}]
        total = sum(s["value"] for s in pdata)
        score = sum(s["value"]*s["esg"] for s in pdata) / total
        self.assertEqual(score, 74.0)

    def test_single_stock_equals_its_esg(self):
        pdata = [{"value":500,"esg":65}]
        total = sum(s["value"] for s in pdata)
        score = sum(s["value"]*s["esg"] for s in pdata) / total
        self.assertEqual(score, 65.0)

    def test_zero_value_no_crash(self):
        pdata = [{"value":0,"esg":50}]
        total = sum(s["value"] for s in pdata)
        score = sum(s["value"]*s["esg"] for s in pdata) / total if total > 0 else 0
        self.assertEqual(score, 0)

    def test_three_stocks_weighted(self):
        pdata = [{"value":500,"esg":80}, {"value":300,"esg":50}, {"value":200,"esg":30}]
        total = sum(s["value"] for s in pdata)
        score = sum(s["value"]*s["esg"] for s in pdata) / total
        self.assertEqual(score, 61.0)

    def test_flagged_below_30(self):
        pdata = [{"ticker":"MSFT","esg":81}, {"ticker":"XOM","esg":32}, {"ticker":"CVX","esg":25}]
        flagged = [s for s in pdata if s["esg"] < 30]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["ticker"], "CVX")

    def test_no_flags_when_all_above_30(self):
        pdata = [{"ticker":"AAPL","esg":73}, {"ticker":"MSFT","esg":81}]
        flagged = [s for s in pdata if s["esg"] < 30]
        self.assertEqual(len(flagged), 0)

    def test_all_flagged_when_all_below_30(self):
        pdata = [{"ticker":"XOM","esg":18}, {"ticker":"CVX","esg":22}]
        flagged = [s for s in pdata if s["esg"] < 30]
        self.assertEqual(len(flagged), 2)

    def test_score_at_boundary_30(self):
        pdata = [{"ticker":"TEST","esg":30}]
        flagged = [s for s in pdata if s["esg"] < 30]
        self.assertEqual(len(flagged), 0)

    def test_percentage_calculation(self):
        pdata = [{"value":600}, {"value":400}]
        total = sum(s["value"] for s in pdata)
        pct1 = pdata[0]["value"] / total * 100
        pct2 = pdata[1]["value"] / total * 100
        self.assertEqual(pct1, 60.0)
        self.assertEqual(pct2, 40.0)


if __name__ == "__main__":
    unittest.main()

