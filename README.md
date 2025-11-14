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

5. Создайте базу данных MySQL и выполните миграции:
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
├── docs/                # Документация
│   └── RAILWAY_DEPLOY.md # Инструкция по деплою на Railway
├── git/                 # Git скрипты автоматизации
│   ├── git_push.bat     # Скрипт пуша для Windows
│   ├── git_push.sh      # Скрипт пуша для Linux/Mac
│   └── README.md        # Документация git скриптов
├── tests/               # Тесты
├── .env.example         # Пример конфигурации
├── requirements.txt     # Зависимости
└── README.md           # Документация
```

## Git автоматизация

Для удобной работы с Git используйте автоматические скрипты:

**Windows:**
```batch
git\git_push.bat
```

**Linux/Mac:**
```bash
bash git/git_push.sh
```

Скрипты автоматически:
- Увеличивают версию проекта
- Создают коммит с умным описанием
- Создают ветку и тег
- Отправляют изменения на GitHub

Подробности в [git/README.md](git/README.md).

## Деплой на Railway

Подробная инструкция по деплою на Railway находится в [docs/RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md).

**Важно:** Для подключения к базе данных MySQL на Railway используйте внутреннюю ссылку:
```
mysql://root:BOrEIPmqHsfNbORBbxJaUhFSTyekKjYJ@mysql.railway.internal:3306/railway
```

## Лицензия

MIT 