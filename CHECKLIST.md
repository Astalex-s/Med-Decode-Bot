# MedDecode — Чеклист реализации

## Шаг 1. Подготовка окружения
- [x] Виртуальное окружение `venv_md`
- [x] `.env` файл с переменными
- [x] `.gitignore`
- [x] Git-репозиторий инициализирован

## Шаг 2. Архитектура проекта (Clean Architecture)
- [x] Структура папок создана
- [x] `__init__.py` во всех пакетах

## Шаг 3. Конфигурация
- [x] `config.py` с pydantic-settings
- [x] `.env_example` (включая `ADMIN_IDS`)

## Шаг 4. Docker — базовая инфраструктура
- [x] `docker-compose.yml` с сервисами `postgres`, `redis`, `bot`
- [x] `Dockerfile` для бота

## Шаг 5. База данных — модели и подключение
- [x] `infrastructure/db/session.py`
- [x] `infrastructure/db/models.py` (User, Subscription, AnalysisHistory, UserConsent)
- [x] Миграция `455af65ad8db` — init tables
- [x] Миграция `b1c2d3e4f5a6` — add user_consents
- [x] `infrastructure/db/repositories/user_repo.py`
- [x] `infrastructure/db/repositories/analysis_repo.py`
- [x] `infrastructure/db/repositories/consent_repo.py`

## Шаг 6. Telegram-бот — /start и главное меню
- [x] `presentation/bot/main.py`
- [x] `presentation/bot/handlers/start.py` (делегировано в consent.py)
- [x] `presentation/bot/keyboards/main_kb.py`
- [x] Регистрация пользователя в БД после согласия ПДн

## Шаг 7. Приём файлов — фото и PDF
- [x] `presentation/bot/handlers/analyze.py` — скачивание файлов в `temp/`

## Шаг 8. OCR-модуль
- [x] `infrastructure/ocr/ocr.py` — OCRService (OpenCV + EasyOCR)

## Шаг 9. Постобработка текста
- [x] `infrastructure/ocr/text_processor.py`

## Шаг 10. Интеграция OpenAI API
- [x] `infrastructure/ai/openai_client.py` — AsyncOpenAI, промпт медассистента

## Шаг 11. Domain layer
- [x] `domain/entities/user.py`
- [x] `domain/entities/subscription.py`
- [x] `domain/entities/analysis.py`
- [x] `domain/entities/consent.py`
- [x] `domain/interfaces/user_repository.py`
- [x] `domain/interfaces/analysis_repository.py`
- [x] `domain/interfaces/ocr_service.py`
- [x] `domain/interfaces/consent_repository.py`

## Шаг 12. Application layer — Use Cases
- [x] `application/use_cases/analyze_file.py`
- [x] `application/use_cases/check_subscription.py`
- [x] `application/use_cases/process_payment.py`

## Шаг 13. Сборка пайплайна в обработчике
- [x] `presentation/bot/handlers/analyze.py` — полный пайплайн

## Шаг 14. Согласие на обработку ПДн (ФЗ-152)
- [x] `consent_document.txt` — типовой документ согласия
- [x] `presentation/bot/handlers/consent.py` — экран согласия с inline-кнопками
- [x] `presentation/bot/middlewares/consent_check.py` — блокировка без согласия

## Шаг 15. Система подписки и лимитов
- [x] `presentation/bot/middlewares/subscription.py`

## Шаг 16. Интеграция платежей
- [x] `infrastructure/payments/yookassa_client.py`
- [x] `presentation/bot/handlers/payment.py`

## Шаг 17. Логирование
- [x] Настройка логгера в `main.py`
- [x] Логи во всех ключевых модулях

## Шаг 18. Админ-функционал
- [x] `presentation/bot/handlers/admin.py` — `/export_users` → CSV с журналом пользователей
- [x] `config.py` — поле `ADMIN_IDS` (список Telegram ID через запятую в .env)

## Шаг 19. Dockerfile и финальный docker-compose.yml
- [x] `Dockerfile`
- [x] `docker-compose.yml` обновлён (сервис `bot`, healthcheck)
