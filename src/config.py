import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
TON_API_KEY = os.getenv('TON_API_KEY')

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')

# Настройки подписки
SUBSCRIPTION_PRICE_RUB = 3000
MIN_NIGHTS_FOR_VACATION = 7

# Настройки TON
TON_API_URL = "https://toncenter.com/api/v2"
TON_WALLET_ADDRESS = os.getenv('TON_WALLET_ADDRESS') 