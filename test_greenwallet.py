# ─────────────────────────────────────────────────────────
# test_greenwallet.py
# Unit tests for GreenWallet ESG Portfolio Impact Scorer
# Run: python -m pytest test_greenwallet.py -v
# ─────────────────────────────────────────────────────────
import unittest
import sqlite3
from datetime import datetime

# ══════════════════════════════════════════════════════════
# TEST SECTION 1: Database Layer (Jugal Bhagat — config.py)
# ══════════════════════════════════════════════════════════
class TestDatabase(unittest.TestCase):
    """Tests for database schema creation and CRUD operations."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        c = self.conn.cursor()
        c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, portfolio_no TEXT DEFAULT "")')
        c.execute('CREATE TABLE holdings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, ticker TEXT, shares REAL)')
        c.execute('CREATE TABLE esg_cache (ticker TEXT PRIMARY KEY, env REAL, soc REAL, gov REAL, composite REAL, source TEXT, sector TEXT, explanation TEXT, fetched_at TIMESTAMP)')
        c.execute('CREATE TABLE analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, green_score REAL, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        self.conn.commit()

    def test_create_user(self):
        self.conn.execute("INSERT INTO users(username,portfolio_no) VALUES(?,?)", ("testuser","PF-001"))
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM users WHERE username='testuser'").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "testuser")
        self.assertEqual(row[2], "PF-001")

    def test_duplicate_user_rejected(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users(username) VALUES('testuser')")

    def test_add_holding(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM holdings WHERE user_id=1").fetchone()
        self.assertEqual(row[2], "AAPL")
        self.assertEqual(row[3], 10.0)

    def test_multiple_holdings_per_user(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'MSFT',5)")
        self.conn.commit()
        rows = self.conn.execute("SELECT * FROM holdings WHERE user_id=1").fetchall()
        self.assertEqual(len(rows), 2)

    def test_delete_holding(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.commit()
        self.conn.execute("DELETE FROM holdings WHERE ticker='AAPL' AND user_id=1")
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM holdings WHERE user_id=1").fetchone()
        self.assertIsNone(row)

    def test_update_shares(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.commit()
        self.conn.execute("UPDATE holdings SET shares=25 WHERE ticker='AAPL' AND user_id=1")
        self.conn.commit()
        row = self.conn.execute("SELECT shares FROM holdings WHERE ticker='AAPL'").fetchone()
        self.assertEqual(row[0], 25.0)

    def test_save_green_score(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,72)")
        self.conn.commit()
        row = self.conn.execute("SELECT green_score FROM analytics WHERE user_id=1").fetchone()
        self.assertEqual(row[0], 72.0)

    def test_multiple_analytics_entries(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,50)")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,55)")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,60)")
        self.conn.commit()
        rows = self.conn.execute("SELECT * FROM analytics WHERE user_id=1").fetchall()
        self.assertEqual(len(rows), 3)

    def test_esg_cache_write_and_read(self):
        self.conn.execute("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)",
            ("AAPL",82,65,73,73,"MSCI","Technology","Strong ESG",datetime.now()))
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM esg_cache WHERE ticker='AAPL'").fetchone()
        self.assertEqual(row[0], "AAPL")
        self.assertEqual(row[1], 82)
        self.assertEqual(row[4], 73)

    def test_esg_cache_overwrite(self):
        self.conn.execute("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)",
            ("AAPL",82,65,73,73,"MSCI","Technology","Old",datetime.now()))
        self.conn.execute("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)",
            ("AAPL",85,70,75,77,"Gemini","Technology","Updated",datetime.now()))
        self.conn.commit()
        row = self.conn.execute("SELECT composite,explanation FROM esg_cache WHERE ticker='AAPL'").fetchone()
        self.assertEqual(row[0], 77)
        self.assertEqual(row[1], "Updated")

    def tearDown(self):
        self.conn.close()
        
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
                
# ══════════════════════════════════════════════════════════
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
