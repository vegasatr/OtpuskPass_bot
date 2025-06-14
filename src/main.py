import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import os

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Консольный обработчик
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Файловый обработчик
fh = logging.FileHandler('bot.log') # Логи будут записываться в bot.log в корне проекта
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

async def start(update, context):
    """Обработчик команды /start"""
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}") # Добавим лог для проверки
    welcome_message = """
Добро пожаловать в OtpuskPass_bot!

Ваша ежемесячная подписка на отпуск теперь доступна прямо в Telegram. Забудьте о долгих поисках и высоких ценах: мы предлагаем вам эксклюзивный доступ к односпальным квартирам бизнес-класса в Таиланде.

Как это работает:

• Всего 3 000 руб. в месяц — и на ваш счет поступает одна ночь отпуска.
• Накопите минимум 7 ночей и отправляйтесь в незабываемое путешествие.
• Мы гарантируем комфорт и качество: все квартиры для размещения в прекрасном состоянии, в хороших локациях и напрямую от собственников.
• Ищете еще больше выгоды? Приглашайте друзей оформить подписку и получайте бесплатные месяцы за каждого нового участника!
• Оплата подписки удобно производится в криптовалюте TON.

OtpuskPass_bot — ваш пропуск в мир беззаботного отдыха, где каждая подписка приближает вас к отпуску мечты.
    """
    await update.message.reply_text(welcome_message)

def main():
    """Основная функция запуска бота"""
    # Создание приложения
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))

    # Запуск бота
    logger.info("Бот запущен и ожидает команды...") # Добавим лог при запуске
    application.run_polling()
    logger.info("Бот остановлен.") # Добавим лог при остановке

if __name__ == '__main__':
    main()