import os
from dotenv import load_dotenv
from telegram import Bot
import asyncio
import logging

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def clear_webhook():
    if not BOT_TOKEN:
        print("BOT_TOKEN не найден в .env")
        logger.error("BOT_TOKEN не найден в .env")
        return

    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.delete_webhook()
        print("Вебхук успешно удален (если он был установлен).")
        logger.info("Вебхук успешно удален (если он был установлен).")
    except Exception as e:
        print(f"Ошибка при удалении вебхука: {e}")
        logger.error(f"Ошибка при удалении вебхука: {e}")

if __name__ == '__main__':
    asyncio.run(clear_webhook())