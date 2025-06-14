# OtpuskPass Bot

Telegram-бот для предоставления услуг краткосрочной аренды квартир бизнес-класса в Таиланде по подписочной модели с оплатой в TON.

## Основные функции

- Ежемесячная подписка на отпуск
- Интеграция с Telegram Mini App
- Оплата в криптовалюте TON
- Реферальная программа
- Управление бронированиями
- Интеграция с Gemini API для обработки запросов

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/OtpuskPass_bot.git
cd OtpuskPass_bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example` и заполните необходимые переменные окружения.

5. Создайте базу данных PostgreSQL и выполните миграции:
```bash
python src/database/migrations.py
```

## Запуск

1. Запустите бота:
```bash
python src/main.py
```

2. Запустите веб-приложение (для Mini App):
```bash
uvicorn src.web.main:app --reload
```

## Структура проекта

```
OtpuskPass_bot/
├── src/
│   ├── bot/              # Модули Telegram бота
│   ├── database/         # Модели и миграции БД
│   ├── web/             # Веб-приложение (Mini App)
│   ├── services/        # Бизнес-логика
│   └── utils/           # Вспомогательные функции
├── tests/               # Тесты
├── .env.example         # Пример конфигурации
├── requirements.txt     # Зависимости
└── README.md           # Документация
```

## Лицензия

MIT 