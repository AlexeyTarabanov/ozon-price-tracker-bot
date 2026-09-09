import os
import tempfile
import unittest

import database as db


class PriceTrackingDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.temp_dir.name, "test.db")
        db.init_db()
        db.add_user(1, username="test")
        self.product_id, _ = db.add_product(1, "https://www.ozon.ru/product/test-123/")

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_start_price_is_set_once(self):
        self.assertTrue(db.set_user_product_start_price(1, self.product_id, 1887.0))
        self.assertFalse(db.set_user_product_start_price(1, self.product_id, 1800.0))

        product = db.get_user_products(1)[0]
        self.assertEqual(1887.0, product["start_price"])
        self.assertEqual(1887.0, product["last_notified_price"])

    def test_last_notified_price_changes_independently_from_start_price(self):
        db.set_user_product_start_price(1, self.product_id, 1887.0)

        self.assertTrue(db.set_last_notified_price(1, self.product_id, 1800.0))

        product = db.get_user_products(1)[0]
        self.assertEqual(1887.0, product["start_price"])
        self.assertEqual(1800.0, product["last_notified_price"])

    def test_history_contains_only_effective_price_changes(self):
        db.update_product_price(self.product_id, 2220.0, 1887.0, "Товар")
        db.set_user_product_start_price(1, self.product_id, 1887.0)
        db.update_product_price(self.product_id, 2220.0, 1887.0, "Товар")
        db.update_product_price(self.product_id, 2200.0, 1800.0, "Товар")

        history = db.get_price_history(self.product_id, limit=None, ascending=True)
        self.assertEqual(1, len(history))
        self.assertEqual(1887.0, history[0]["old_price"])
        self.assertEqual(1800.0, history[0]["price"])

    def test_summary_uses_only_changes_after_subscription_started(self):
        connection = db.get_connection()
        connection.execute('''
            UPDATE user_products
            SET start_price = 2220, added_at = '2026-09-09 10:00:00'
            WHERE user_id = 1 AND product_id = ?
        ''', (self.product_id,))
        connection.execute('''
            UPDATE products
            SET current_price = 2220,
                current_ozon_bank_price = 1887,
                last_checked = '2026-09-09 12:00:00'
            WHERE product_id = ?
        ''', (self.product_id,))
        connection.executemany('''
            INSERT INTO price_history (product_id, price, old_price, checked_at)
            VALUES (?, ?, ?, ?)
        ''', [
            (self.product_id, 2500.0, 2600.0, "2026-09-09 09:00:00"),
            (self.product_id, 2000.0, 2220.0, "2026-09-09 11:00:00"),
            (self.product_id, 1887.0, 2000.0, "2026-09-09 12:00:00"),
        ])
        connection.commit()
        connection.close()

        summary = db.get_user_price_summary(1, self.product_id)

        self.assertEqual(2220.0, summary["start_price"])
        self.assertEqual(1887.0, summary["current_price"])
        self.assertEqual(2000.0, summary["previous_price"])
        self.assertEqual(-113.0, summary["change_amount"])
        self.assertEqual(1887.0, summary["min_price"])
        self.assertEqual(2220.0, summary["max_price"])


if __name__ == "__main__":
    unittest.main()
