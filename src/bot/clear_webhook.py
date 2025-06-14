import os
from dotenv import load_dotenv
from telegram import Bot
import asyncio

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def clear_webhook():
    if not BOT_TOKEN:
        print("BOT_TOKEN не найден в .env")
        return

    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.delete_webhook()
        print("Вебхук успешно удален (если он был установлен).")
    except Exception as e:
        print(f"Ошибка при удалении вебхука: {e}")

if __name__ == '__main__':
    asyncio.run(clear_webhook())