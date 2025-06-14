import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
import os
from src.bot.handlers import start, callback_router, subscribe, setup_handlers, error_handler
from src.database.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def init_database():
    """Инициализация базы данных"""
    # Временно используем SQLite вместо PostgreSQL
    database_url = 'sqlite:///bot.db'
    logger.info(f"Используется база данных: {database_url}")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

async def main():
    """Основная функция запуска бота"""
    # Проверка наличия токена
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN не найден в .env файле")
        return

    # Инициализация базы данных
    Session = init_database()
    
    # Создание приложения
    application = Application.builder().token(token).build()
    
    # Добавление TON API ключа в контекст бота
    application.bot_data['ton_api_key'] = os.getenv('TON_API_KEY')
    
    # Настройка обработчиков
    setup_handlers(application)
    
    # Добавление обработчика ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    logger.info("Бот запущен")
    await application.initialize()
    await application.start()
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True) 