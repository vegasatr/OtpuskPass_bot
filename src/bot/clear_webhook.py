import os
import sys
from dotenv import load_dotenv
from telegram import Bot

# Загружаем переменные окружения
load_dotenv()

def clear_webhook():
    """
    Очищает вебхук для бота
    """
    try:
        # Получаем токен из переменных окружения
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            print("❌ Ошибка: BOT_TOKEN не найден в .env файле")
            sys.exit(1)

        # Создаем экземпляр бота
        bot = Bot(token=bot_token)
        
        # Удаляем вебхук
        bot.delete_webhook()
        print("✅ Вебхук успешно удален")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении вебхука: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    clear_webhook() 