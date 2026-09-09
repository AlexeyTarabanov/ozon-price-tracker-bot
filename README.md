# 🛒 Ozon Price Tracker Bot

Telegram-бот для отслеживания цен на товары Ozon с уведомлениями об изменениях.

## Возможности

- отслеживание товаров по ссылке, SKU и shared cart;
- показ обычной цены и цены с Ozon Картой;
- автоматические уведомления об изменении цены;
- история цены с графиком;
- персональный порог уведомлений для каждого товара;
- мультипользовательский режим;
- обработка статусов «снят с продажи» и «снова в продаже».

## Как сейчас получается цена

Актуальный поток работы такой:

1. В базе хранятся обычные ссылки вида `https://www.ozon.ru/product/...`.
2. Для обхода antibot бот получает cookies через браузерную эмуляцию:
   - `Selenium` — если включён `USE_TEST_COOKIE_METHOD=true`;
   - `Playwright` — fallback или основной путь.
3. Затем `ozon_client.py` преобразует ссылку товара во внутренний JSON endpoint Ozon:
   - `https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=%2Fproduct%2F...`
4. Название и цены извлекаются из `widgetStates`.

Основной путь больше не зависит от HTML-парсинга карточки товара.

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Запустить бота |
| `/help` | Справка |
| `/add` | Добавить товар |
| `/cart` | Добавить товары из shared cart |
| `/list` | Список товаров |
| `/remove` | Удалить товар |
| `/history` | История цены |
| `/check` | Проверить один товар |
| `/checkall` | Проверить все товары пользователя |
| `/settings` | Показать настройки |
| `/status` | Статистика бота |
| `/monitoring` | Детальный мониторинг |
| `/cancel` | Отменить действие |

## Быстрый старт

### Windows

```bat
install.bat
```

Скрипт:

- создаёт `venv`;
- ставит зависимости из `requirements.txt`;
- устанавливает `chromium` для `Playwright`;
- создаёт `config.txt` из `config.txt.example`, если файла ещё нет.

### Ручная установка

1. Создай виртуальное окружение:

```bash
python -m venv venv
```

2. Активируй его:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

3. Установи зависимости:

```bash
pip install -r requirements.txt
```

4. Установи браузер для `Playwright`:

```bash
playwright install chromium
```

5. Скопируй `config.txt.example` в `config.txt` и заполни настройки.

Минимальный пример:

```ini
BOT_TOKEN=
CHECK_INTERVAL=1800
PRICE_CHANGE_THRESHOLD=3
NOTIFICATION_DIRECTION=down
USE_TEST_COOKIE_METHOD=true
PROXY_TYPE=none
PROXY_URL=
ADMIN_ID=
```

6. Запусти бота:

```bash
python main.py
```

## Конфигурация

- `BOT_TOKEN` — токен Telegram-бота от `@BotFather`;
- `CHECK_INTERVAL` — интервал проверки в секундах;
- `PRICE_CHANGE_THRESHOLD` — минимальный процент изменения цены для уведомления;
- `NOTIFICATION_DIRECTION` — `both`, `down`, `up`;
- `USE_TEST_COOKIE_METHOD`:
  - `true` — сначала `Selenium`, затем `Playwright`;
  - `false` — сразу `Playwright`;
- `PROXY_TYPE` / `PROXY_URL` / `PROXY_USER` / `PROXY_PASS` — прокси для Telegram-части;
  - поддерживаемые варианты: `none`, `socks5h`, `https`;
  - рабочий SOCKS-формат: `socks5h://host:port`;
  - логин и пароль указываются отдельно в `PROXY_USER` и `PROXY_PASS`;
- `ADMIN_ID` — ID администратора для `/status` и `/monitoring`.

## Структура репозитория

```text
ozon/
├── bot.py
├── cart_parser.py
├── config.txt.example
├── database.py
├── install.bat
├── list_handler.py
├── main.py
├── ozon_client.py
├── price_chart.py
├── price_checker.py
├── requirements.txt
└── README.md
```

Локальные runtime-файлы вроде `config.txt`, `ozon_tracker.db`, `ozon_cookies.json`, `bot.log` и тестовых дампов в репозиторий не коммитятся.

## Логика статуса товара

Клиент возвращает:

- `name`
- `regular_price`
- `ozon_bank_price`
- `request_ok`

Смысл результата:

- `request_ok=False` — ошибка сети/капчи, статус товара не меняется;
- `request_ok=True` и цены нет — товар считается снятым с продажи;
- `request_ok=True` и цена есть — товар в продаже.

На этом держатся:

- уведомления о снятии с продажи;
- уведомления о возвращении в продажу;
- фоновые проверки;
- ручные проверки `/check` и `/checkall`.

## Troubleshooting

### Цена не получается

- cookies могли истечь;
- Ozon мог изменить структуру `widgetStates`;
- проверь `bot.log`;
- при необходимости включи более подробное локальное логирование и проверь ответ Ozon вручную.

### Бот не запускается

- проверь `BOT_TOKEN` в `config.txt`;
- проверь корректность proxy-настроек, если они используются;
- переустанови зависимости:

```bash
pip install -r requirements.txt
```

### Playwright не стартует

Убедись, что браузер установлен:

```bash
playwright install chromium
```

## Замечания

- Ozon может менять структуру `widgetStates`, поэтому парсер нужно периодически проверять.
- Cookies всё ещё нужны, иначе Ozon может вернуть antibot / challenge.
- Слишком частые проверки повышают риск блокировок.
- Перед публикацией на GitHub не коммить `config.txt`, cookies, базы данных и логи.

## Лицензия

MIT
