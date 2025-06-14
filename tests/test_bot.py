import asyncio
import logging
import os
import sys
import nest_asyncio
from datetime import datetime
from unittest import IsolatedAsyncioTestCase
from telegram import Update, Bot
from telegram.ext import Application
from dotenv import load_dotenv

# Применяем патч для поддержки вложенных циклов событий
nest_asyncio.apply()

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Подробное логирование в файл и консоль
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler('test_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
TEST_CHAT_ID = os.getenv('TELEGRAM_TEST_CHAT_ID')

class TestBot(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        logger.info('asyncSetUp: инициализация бота')
        self.bot = Bot(token=BOT_TOKEN)
        self.application = Application.builder().token(BOT_TOKEN).build()
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info('Тестовый бот запущен')
        except Exception as e:
            logger.exception(f'Ошибка при запуске бота: {e}')
            raise

    async def asyncTearDown(self):
        logger.info('asyncTearDown: остановка бота')
        try:
            if self.application and self.application.running:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info('Тестовый бот остановлен')
        except Exception as e:
            logger.exception(f'Ошибка при остановке бота: {e}')

    async def test_start_command(self):
        logger.info('Тест: отправка /start')
        try:
            message = await self.bot.send_message(
                chat_id=TEST_CHAT_ID,
                text="/start"
            )
            logger.info(f'Команда /start отправлена, message_id={message.message_id}')
        except Exception as e:
            logger.exception(f'Ошибка при отправке /start: {e}')
            self.fail(f'Ошибка при отправке /start: {e}')

        await asyncio.sleep(2)
        logger.info('Пробую получить обновления...')
        try:
            updates = await self.bot.get_updates()
            logger.debug(f'Получено {len(updates)} обновлений')
            for upd in updates:
                if upd.message and str(upd.message.chat.id) == str(TEST_CHAT_ID):
                    logger.info(f'Ответ: {upd.message.text}')
                    self.assertIsNotNone(upd.message.text)
                    self.assertIn("Добро пожаловать", upd.message.text)
                    return
            logger.error('Нет ответа от бота на /start')
            self.fail('Бот не ответил на команду /start')
        except Exception as e:
            logger.exception(f'Ошибка при получении обновлений: {e}')
            self.fail(f'Ошибка при получении обновлений: {e}')

if __name__ == '__main__':
    import unittest
    unittest.main() 