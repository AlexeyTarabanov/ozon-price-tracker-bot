import unittest
from unittest.mock import AsyncMock, Mock, patch

import bot


class LastNotifiedPriceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.product = {
            "product_id": 1,
            "product_name": "Товар",
            "ozon_url": "https://www.ozon.ru/product/test-123/",
        }
        self.subscriber = {
            "user_id": 10,
            "price_threshold": 3.0,
            "last_notified_price": 1887.0,
        }

    async def _notify(self, new_price, send_side_effect=None):
        send = AsyncMock(side_effect=send_side_effect)
        set_last_notified = Mock()
        with (
            patch.object(bot.db, "get_user_product_for_notification", return_value=[self.subscriber]),
            patch.object(bot.db, "set_last_notified_price", set_last_notified),
            patch.object(bot, "send_message_with_retry", send),
        ):
            count = await bot.notify_price_change_subscribers(
                Mock(), self.product, None, new_price, None
            )
        return count, send, set_last_notified

    async def test_price_increase_only_updates_history(self):
        count, send, set_last_notified = await self._notify(1900.0)

        self.assertEqual(0, count)
        send.assert_not_awaited()
        set_last_notified.assert_not_called()

    async def test_decrease_below_threshold_only_updates_history(self):
        count, send, set_last_notified = await self._notify(1840.0)

        self.assertEqual(0, count)
        send.assert_not_awaited()
        set_last_notified.assert_not_called()

    async def test_sufficient_decrease_notifies_and_updates_baseline(self):
        count, send, set_last_notified = await self._notify(1830.0)

        self.assertEqual(1, count)
        send.assert_awaited_once()
        set_last_notified.assert_called_once_with(10, 1, 1830.0)

    async def test_failed_send_does_not_update_baseline(self):
        count, send, set_last_notified = await self._notify(
            1830.0, send_side_effect=RuntimeError("send failed")
        )

        self.assertEqual(0, count)
        send.assert_awaited_once()
        set_last_notified.assert_not_called()


if __name__ == "__main__":
    unittest.main()
