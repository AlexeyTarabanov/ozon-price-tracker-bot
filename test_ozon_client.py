import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from ozon_client import BROWSER_PROFILE_DIR, OzonClient


class ParseWidgetPricesTest(unittest.TestCase):
    def setUp(self):
        self.client = object.__new__(OzonClient)

    def test_parses_card_and_regular_prices(self):
        text = "4 299 ₽\nс Ozon Картой\n4 799 ₽\nбез Ozon Карты"

        regular, card = self.client._parse_prices_from_widget_text(text)

        self.assertEqual(4799.0, regular)
        self.assertEqual(4299.0, card)

    def test_parses_card_price_only(self):
        text = "4\u202f299 ₽ с Ozon Картой"

        regular, card = self.client._parse_prices_from_widget_text(text)

        self.assertIsNone(regular)
        self.assertEqual(4299.0, card)

    def test_parses_regular_price_only(self):
        text = "4\u00a0799 ₽ без Ozon Карты"

        regular, card = self.client._parse_prices_from_widget_text(text)

        self.assertEqual(4799.0, regular)
        self.assertIsNone(card)

    def test_unlabelled_price_is_regular(self):
        regular, card = self.client._parse_prices_from_widget_text("4 799 ₽")

        self.assertEqual(4799.0, regular)
        self.assertIsNone(card)

    def test_parses_current_ozon_payment_blocks_and_ignores_old_price(self):
        text = "1\u2009887\u2009₽\nС банками\n2\u2009220\u2009₽\n4\u2009099\u2009₽\nС другими банками"

        regular, card = self.client._parse_prices_from_widget_text(text)

        self.assertEqual(2220.0, regular)
        self.assertEqual(1887.0, card)


class PlaywrightFallbackFlowTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = object.__new__(OzonClient)

    async def test_returns_playwright_price_without_second_json_request(self):
        self.client._make_request = Mock(return_value=(403, ""))
        self.client._get_product_price_playwright = AsyncMock(
            return_value=("Товар", 4799.0, 4299.0, True)
        )

        result = await self.client._get_product_price_json("https://www.ozon.ru/product/test-123/")

        self.assertEqual(("Товар", 4799.0, 4299.0, True), result)
        self.client._make_request.assert_called_once()
        self.client._get_product_price_playwright.assert_awaited_once()

    async def test_retries_json_once_with_cookies_and_does_not_reopen_playwright(self):
        self.client._make_request = Mock(side_effect=[(403, ""), (403, "")])
        self.client._get_product_price_playwright = AsyncMock(
            return_value=("Товар", None, None, True)
        )

        result = await self.client._get_product_price_json("https://www.ozon.ru/product/test-123/")

        self.assertEqual((None, None, None, False), result)
        self.assertEqual(2, self.client._make_request.call_count)
        self.client._get_product_price_playwright.assert_awaited_once()


class PersistentPlaywrightContextTest(unittest.IsolatedAsyncioTestCase):
    def _make_client(self):
        client = object.__new__(OzonClient)
        client._cookies = {}
        client._cookies_loaded_at = None
        client._save_cookies_to_file = Mock()
        client._extract_product_id_from_page_url = Mock(return_value="123")
        client._extract_product_name_from_page = AsyncMock(return_value="Товар")
        client._extract_prices_from_page = AsyncMock(return_value=(2220.0, 1887.0))
        return client

    def _make_playwright(self, launch_persistent_context):
        browser = Mock()
        browser.new_context = AsyncMock()

        chromium = Mock()
        chromium.launch = AsyncMock(return_value=browser)
        chromium.launch_persistent_context = launch_persistent_context

        playwright = Mock()
        playwright.chromium = chromium

        manager = MagicMock()
        manager.__aenter__ = AsyncMock(return_value=playwright)
        manager.__aexit__ = AsyncMock(return_value=False)
        return manager, chromium, browser

    def _make_context(self):
        page = Mock()
        page.goto = AsyncMock()
        page.title = AsyncMock(return_value="Ozon")
        page.wait_for_selector = AsyncMock()

        context = Mock()
        context.pages = [page]
        context.new_page = AsyncMock(return_value=page)
        context.cookies = AsyncMock(return_value=[{"name": "session", "value": "saved"}])
        context.close = AsyncMock()
        return context

    async def test_uses_persistent_profile_and_closes_context(self):
        client = self._make_client()
        context = self._make_context()
        launch_persistent_context = AsyncMock(return_value=context)
        manager, chromium, browser = self._make_playwright(launch_persistent_context)

        with (
            patch("playwright.async_api.async_playwright", return_value=manager),
            patch("ozon_client.asyncio.sleep", new=AsyncMock()),
        ):
            result = await client._get_product_price_playwright(
                "https://www.ozon.ru/product/test-123/"
            )

        self.assertEqual(("Товар", 2220.0, 1887.0, True), result)
        launch_persistent_context.assert_awaited_once()
        launch_kwargs = launch_persistent_context.await_args.kwargs
        self.assertEqual(BROWSER_PROFILE_DIR, launch_kwargs["user_data_dir"])
        self.assertTrue(os.path.isabs(launch_kwargs["user_data_dir"]))
        context.close.assert_awaited_once()
        chromium.launch.assert_not_awaited()
        browser.new_context.assert_not_awaited()

    async def test_parallel_fallbacks_do_not_open_profile_simultaneously(self):
        client = self._make_client()
        first_launch_started = asyncio.Event()
        allow_first_launch = asyncio.Event()
        launch_count = 0

        async def launch_persistent_context(**_kwargs):
            nonlocal launch_count
            launch_count += 1
            if launch_count == 1:
                first_launch_started.set()
                await allow_first_launch.wait()
            return self._make_context()

        launch_mock = AsyncMock(side_effect=launch_persistent_context)
        manager, _, _ = self._make_playwright(launch_mock)
        real_sleep = asyncio.sleep

        with (
            patch("playwright.async_api.async_playwright", return_value=manager),
            patch("ozon_client.asyncio.sleep", new=AsyncMock()),
        ):
            first = asyncio.create_task(
                client._get_product_price_playwright("https://www.ozon.ru/product/first-1/")
            )
            await first_launch_started.wait()
            second = asyncio.create_task(
                client._get_product_price_playwright("https://www.ozon.ru/product/second-2/")
            )
            await real_sleep(0.01)

            self.assertEqual(1, launch_mock.await_count)

            allow_first_launch.set()
            await asyncio.gather(first, second)

        self.assertEqual(2, launch_mock.await_count)


if __name__ == "__main__":
    unittest.main()
