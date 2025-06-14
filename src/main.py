import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application

# Импортируем вспомогательные функции
# from utils.helpers import get_nearest_available_date, format_apartment_info # Больше не нужны здесь, перенесены в handlers.py
# from database.models import Apartment # Больше не нужны здесь, перенесены в handlers.py
from database.migrations import init_db # Оставляем для инициализации БД

# Импортируем PaymentChecker и setup_handlers
from services.payment_checker import PaymentChecker
from bot.handlers import setup_handlers # Импортируем функцию настройки обработчиков

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

# Получаем логгер для этого модуля
logger = logging.getLogger(__name__)

# Удалены дублирующиеся функции-обработчики (start, send_month_selection и т.д.),
# так как они теперь находятся в src/bot/handlers.py

async def main():
    """Основная функция запуска бота"""
    # Проверка наличия BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("❌ ОШИБКА: BOT_TOKEN не найден в файле .env. Убедитесь, что он установлен.")
        exit(1)

    # Инициализация базы данных
    logger.info("📦 Инициализация базы данных...")
    init_db() # Вызов init_db для создания таблиц, если они не существуют
    logger.info("✅ База данных инициализирована.")

    # Инициализация и запуск проверки платежей как асинхронной задачи
    logger.info("💰 Инициализация и запуск проверки платежей как асинхронной задачи...")
    payment_checker = PaymentChecker()
    logger.info("✅ Проверка платежей инициализирована.")

    # Создание приложения с post_init
    application = Application.builder().token(bot_token).post_init(payment_checker.start).build()

    # Используем функцию setup_handlers из src/bot/handlers.py для настройки всех обработчиков
    logger.info("⚙️ Настройка обработчиков из src/bot/handlers.py...")
    setup_handlers(application)
    logger.info("✅ Обработчики настроены.")

    # Запуск бота
    logger.info("🚀 Запуск бота...")
    try:
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}", exc_info=True)
    finally:
        await application.stop()
        logger.info("Бот остановлен.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания. Завершаем работу...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise