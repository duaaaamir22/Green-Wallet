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

