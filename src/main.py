import logging
import os
import signal
import sys
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from bot.handlers import setup_handlers
from telegram import Update

# Применяем патч для поддержки вложенных циклов событий
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

# Глобальная переменная для хранения приложения
application = None

async def log_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"ПОЛУЧЕН АПДЕЙТ: {update}")

async def shutdown(application: Application):
    """Корректное завершение работы бота"""
    logger.info("Завершение работы бота...")
    if application and application.running:
        await application.stop()
        await application.shutdown()

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения работы"""
    logger.info("Получен сигнал завершения работы")
    if application:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(shutdown(application))
    sys.exit(0)

async def main():
    """Основная функция запуска бота"""
    global application
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настраиваем обработчики
    setup_handlers(application)
    
    # Логируем все сообщения и callback-и
    application.add_handler(MessageHandler(filters.ALL, log_all_updates), group=999)
    application.add_handler(CallbackQueryHandler(log_all_updates), group=999)
    
    # Запускаем бота
    logger.info("Бот запущен")
    
    try:
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}", exc_info=True)
        await shutdown(application)

if __name__ == '__main__':
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)