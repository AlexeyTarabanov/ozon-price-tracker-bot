import unittest
from unittest.mock import patch

from list_handler import build_product_tracking_text


class ProductTrackingTextTest(unittest.TestCase):
    def setUp(self):
        self.product = {
            "product_id": 1,
            "product_name": "Сервер / чайник MHW-3BOMBER",
        }

    @patch("list_handler.db.get_user_price_summary")
    def test_formats_change_from_previous_recorded_price(self, get_summary):
        get_summary.return_value = {
            "start_price": 2220.0,
            "started_at": "2026-09-09 10:00:00",
            "current_price": 1887.0,
            "regular_price": 2220.0,
            "ozon_bank_price": 1887.0,
            "last_checked": "2026-09-09 20:53:00",
            "previous_price": 2220.0,
            "change_amount": -333.0,
            "min_price": 1887.0,
            "max_price": 2220.0,
        }

        text = build_product_tracking_text(self.product, user_id=10)

        self.assertIn("Старт: 2 220 ₽ · 09.09.2026", text)
        self.assertIn("Сейчас: 1 887 ₽ · 09.09.2026 23:53", text)
        self.assertIn("🔻 −333 ₽ (−15.0%) с предыдущей проверки", text)
        self.assertIn("Минимум: 1 887 ₽", text)

    @patch("list_handler.db.get_user_price_summary")
    def test_formats_subscription_without_price_changes(self, get_summary):
        get_summary.return_value = {
            "start_price": 1887.0,
            "started_at": "2026-09-09 20:53:00",
            "current_price": 1887.0,
            "regular_price": 2220.0,
            "ozon_bank_price": 1887.0,
            "last_checked": "2026-09-09 20:53:00",
            "previous_price": None,
            "change_amount": None,
            "min_price": 1887.0,
            "max_price": 1887.0,
        }

        text = build_product_tracking_text(self.product, user_id=10)

        self.assertIn("➖ Изменений пока нет", text)


if __name__ == "__main__":
    unittest.main()
