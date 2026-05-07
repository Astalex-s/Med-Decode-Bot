# MedDecode — Telegram-бот для расшифровки медицинских анализов

> Загрузи фото или PDF с анализами — бот объяснит каждый показатель простым языком.

---

## Проблема

Пациенты получают результаты анализов на руки, но не понимают что они означают. Референсные значения есть, но что значит "МЧГ 24.3 пг" или "ТТГ 6.8 мМЕ/л" — непонятно без медицинского образования. Запись к врачу занимает дни, а тревога от непонятных цифр — немедленная.

## Решение

Telegram-бот MedDecode принимает фото или PDF с медицинским документом, распознаёт текст через OCR, передаёт в GPT-4o-mini и возвращает пользователю понятное объяснение каждого показателя: что в норме, что выходит за пределы, и что стоит обсудить с врачом.

---

## Как работает

```
Пользователь отправляет фото/PDF
        ↓
OCR (EasyOCR + OpenCV)
  — предобработка изображения (CLAHE, bilateral filter, adaptive threshold, deskew, upscale)
  — для PDF: PyMuPDF → рендер страниц → OCR каждой страницы
  — для фото: двойной проход (обработанное + оригинал, берётся лучший результат)
        ↓
Очистка текста (text_processor)
  — удаление мусорных символов, нормализация пробелов
        ↓
GPT-4o-mini (OpenAI API)
  — системный промпт: медицинский ассистент без права ставить диагнозы
  — temperature=0.3 для стабильных ответов
  — max_tokens=2000
        ↓
Результат → пользователю в Telegram (HTML-форматирование)
```

### Что умеет распознавать

- Общий анализ крови (ОАК): лейкоциты, эритроциты, гемоглобин, тромбоциты и т.д.
- Биохимия: глюкоза, холестерин, билирубин, АЛТ, АСТ, креатинин, мочевина
- Гормоны: ТТГ, Т3, Т4, инсулин, кортизол и др.
- Общий анализ мочи
- Коагулограмма
- Иммунология, аллергопробы, ПЦР-тесты
- Текстовые заключения УЗИ, МРТ, КТ, ЭКГ

### Умная обработка нечитаемых документов

Если OCR не смог извлечь текст или GPT определил что документ нечитаем — **попытка не засчитывается** в лимит пользователя.

---

## Функциональность

### Для пользователей

| Функция | Описание |
|---|---|
| Расшифровка анализов | Фото (JPG/PNG) или PDF → объяснение на русском |
| Бесплатный лимит | `FREE_LIMIT` анализов бесплатно (по умолчанию 3) |
| Подписка Premium | Неограниченные анализы на 30 дней |
| Оплата через Telegram Stars | Встроенная оплата звёздами Telegram, не нужны внешние провайдеры |
| Статус подписки | Команда "Моя подписка" — лимит, срок действия |
| Согласие на обработку ПДн | Экран согласия при первом запуске (ФЗ-152 РФ) |

### Для администраторов

| Команда | Описание |
|---|---|
| `/export_users` | CSV-выгрузка всех пользователей с датами регистрации и использованием |

### Для разработки

| Команда | Описание |
|---|---|
| `/test_pay` | Активирует Premium без оплаты (только для администраторов при отладке) |

---

## Технический стек

| Слой | Технология |
|---|---|
| **Бот** | Python 3.11, aiogram 3.10 |
| **Архитектура** | Clean Architecture (domain → application → infrastructure → presentation) |
| **OCR** | EasyOCR (ru + en), OpenCV, PyMuPDF |
| **AI** | OpenAI API, gpt-4o-mini |
| **БД** | PostgreSQL 16, SQLAlchemy 2.0 async, asyncpg, Alembic |
| **Кэш** | Redis 7 |
| **Конфиг** | pydantic-settings v2, .env |
| **Платежи** | Telegram Stars (XTR) |
| **PDF** | fpdf2 |
| **Контейнеризация** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Структура проекта

```
MedDecode/
├── domain/                     # Бизнес-сущности и интерфейсы (чистый Python)
│   ├── entities/
│   │   ├── user.py             # Пользователь
│   │   ├── subscription.py     # Подписка
│   │   ├── analysis.py         # Результат анализа
│   │   └── consent.py          # Согласие на ПДн
│   └── interfaces/
│       ├── user_repository.py
│       ├── analysis_repository.py
│       ├── ocr_service.py
│       └── consent_repository.py
│
├── application/                # Use cases — бизнес-логика
│   └── use_cases/
│       ├── analyze_file.py     # OCR → AI → сохранение → инкремент
│       ├── check_subscription.py
│       └── process_payment.py  # Активация Premium на 30 дней
│
├── infrastructure/             # Реализация интерфейсов
│   ├── db/
│   │   ├── models.py           # SQLAlchemy ORM-модели
│   │   ├── session.py          # AsyncSession фабрика
│   │   └── repositories/       # UserRepository, AnalysisRepository, ConsentRepository
│   ├── ocr/
│   │   ├── ocr.py              # OCRService: предобработка + EasyOCR
│   │   └── text_processor.py   # Очистка OCR-текста
│   ├── ai/
│   │   └── openai_client.py    # AsyncOpenAI клиент
│   └── payments/
│       └── yookassa_client.py  # Заготовка для ЮKassa (будущее)
│
├── presentation/
│   └── bot/
│       ├── main.py             # Точка входа, middleware, роутеры
│       ├── handlers/
│       │   ├── consent.py      # /start, согласие на ПДн
│       │   ├── analyze.py      # Обработка фото/PDF
│       │   ├── payment.py      # /subscribe, /test_pay, Stars оплата
│       │   └── admin.py        # /export_users
│       ├── middlewares/
│       │   ├── consent_check.py   # Блокировка без согласия на ПДн
│       │   └── subscription.py    # Блокировка при исчерпании лимита
│       └── keyboards/
│           └── main_kb.py      # Главное меню
│
├── alembic/                    # Миграции БД
├── consent_document.pdf        # PDF согласия на обработку ПДн
├── generate_consent_pdf.py     # Генератор PDF (fpdf2 + Arial)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env_example
```

---

## Схема базы данных

### `users`
| Поле | Тип | Описание |
|---|---|---|
| id | Integer PK | |
| telegram_id | BigInteger | Уникальный ID в Telegram |
| username | String | @username |
| analyses_used | Integer | Счётчик использованных анализов |
| created_at | DateTime(tz) | Дата регистрации |

### `subscriptions`
| Поле | Тип | Описание |
|---|---|---|
| id | Integer PK | |
| user_id | FK → users | |
| is_active | Boolean | Активна ли подписка |
| expires_at | DateTime(tz) | Дата окончания |
| created_at | DateTime(tz) | |

### `analyses`
| Поле | Тип | Описание |
|---|---|---|
| id | Integer PK | |
| user_id | FK → users | |
| file_type | String | pdf / jpg / png |
| result_text | Text | Ответ GPT |
| created_at | DateTime(tz) | |

### `user_consents`
| Поле | Тип | Описание |
|---|---|---|
| id | Integer PK | |
| telegram_id | BigInteger | |
| full_name | String | Имя из Telegram |
| username | String | @username |
| agreed | Boolean | Факт согласия |
| agreed_at | DateTime(tz) | Время согласия |
| declined_at | DateTime(tz) | Время отказа |
| created_at | DateTime(tz) | |

---

## Установка и запуск

### Требования

- Python 3.11+
- Docker и Docker Compose
- Telegram Bot Token (от @BotFather)
- OpenAI API Key

### 1. Клонировать репозиторий

```bash
git clone https://github.com/<your-username>/MedDecode.git
cd MedDecode
```

### 2. Настроить переменные окружения

```bash
cp .env_example .env
```

Заполнить `.env`:

```env
# Telegram
BOT_TOKEN=ваш_токен_от_BotFather

# База данных
DB_HOST=localhost
DB_PORT=5432
DB_NAME=meddecode
DB_USER=meddecode_user
DB_PASSWORD=strongpassword
DB_URL=postgresql+asyncpg://meddecode_user:strongpassword@localhost:5432/meddecode

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# OpenAI
OPENAI_API_KEY=sk-...

# Платежи (Telegram Stars — токен не нужен, оставить пустым или любое значение)
YOOMONEY_TOKEN=

# Лимит бесплатных анализов
FREE_LIMIT=3

# Telegram ID администраторов (через запятую)
ADMIN_IDS=123456789
```

### 3. Запустить через Docker Compose

```bash
# Запустить PostgreSQL и Redis
docker compose up -d postgres redis

# Применить миграции
pip install alembic asyncpg sqlalchemy
alembic upgrade head

# Собрать и запустить бота
docker compose up -d bot
```

### 4. Запустить локально (для разработки)

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить PostgreSQL и Redis через Docker
docker compose up -d postgres redis

# Применить миграции
alembic upgrade head

# Сгенерировать PDF согласия (только при первом запуске)
python generate_consent_pdf.py

# Запустить бота
python -m presentation.bot.main
```

### 5. Проверить работу

- Откройте бота в Telegram и отправьте `/start`
- Дайте согласие на обработку данных
- Отправьте фото или PDF с анализами
- Для теста Premium без оплаты: `/test_pay`
- Для просмотра инвойса: `/subscribe`

---

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `BOT_TOKEN` | ✅ | Токен бота от @BotFather |
| `DB_URL` | ✅ | URL подключения к PostgreSQL |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | ✅ | Параметры БД |
| `REDIS_HOST`, `REDIS_PORT` | ✅ | Параметры Redis |
| `OPENAI_API_KEY` | ✅ | Ключ OpenAI API |
| `YOOMONEY_TOKEN` | — | Токен платёжного провайдера (для Telegram Stars не нужен) |
| `FREE_LIMIT` | ✅ | Количество бесплатных анализов (рекомендуется 3) |
| `ADMIN_IDS` | — | Telegram ID администраторов через запятую |

---

## Платежи

Бот использует **Telegram Stars (XTR)** — встроенную валюту Telegram. Не требует регистрации в платёжных системах.

Текущие настройки:
- Цена подписки: **300 ⭐** (≈ 299 ₽ / 30 дней)

Для подключения ЮKassa (реальные рубли):
1. Зарегистрируйтесь на [kassa.yandex.ru](https://kassa.yandex.ru) как ИП/самозанятый
2. Получите shopId и secretKey
3. В @BotFather → Payments → ЮKassa → введите реквизиты → получите provider_token
4. Вставьте токен в `.env` как `YOOMONEY_TOKEN=`
5. В `payment.py` замените `CURRENCY = "XTR"` на `CURRENCY = "RUB"` и `provider_token=""` на `provider_token=settings.YOOMONEY_TOKEN`

---

## Администрирование

### Выгрузка пользователей

Команда `/export_users` (только для `ADMIN_IDS`) отправляет CSV-файл со столбцами:

```
telegram_id, username, analyses_used, registered_at, subscription_active, subscription_expires
```

Файл сохраняется в кодировке UTF-8 с BOM (корректно открывается в Excel).

---

## Миграции БД

```bash
# Применить все миграции
alembic upgrade head

# Откатить все миграции
alembic downgrade base

# Создать новую миграцию
alembic revision --autogenerate -m "описание изменений"
```

---

## Результат

- Бот принимает любые форматы медицинских документов: фото с телефона (включая наклонные, с тенями, низкого разрешения) и PDF-сканы
- OCR работает на реальных фотографиях анализов: адаптивная бинаризация, выравнивание наклона, CLAHE, двойной проход
- GPT объясняет показатели без медицинского жаргона, указывает отклонения, рекомендует обратиться к врачу
- Монетизация через Telegram Stars без внешних интеграций
- Соответствие ФЗ-152 РФ: согласие на обработку ПДн с PDF-документом, журнал согласий в БД

---

## Лицензия

MIT
