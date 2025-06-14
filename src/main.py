import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import os

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Обработчик команды /start"""
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
    application.run_polling()

if __name__ == '__main__':
    main() 