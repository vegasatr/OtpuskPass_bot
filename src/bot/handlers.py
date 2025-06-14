from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from datetime import datetime, timedelta
from src.utils.helpers import get_nearest_available_date
from src.ton.ton_client import TONClient
from src.database.models import User, Subscription, Payment, PaymentStatus
from sqlalchemy.orm import Session
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Приветствие и старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    welcome_message = (
        "Добро пожаловать в OtpuskPass_bot!\n\n"
        "Ваша ежемесячная подписка на отпуск теперь доступна прямо в Telegram.\n\n"
        "Как это работает:\n"
        "• 3 000 руб. в месяц — и на ваш счет поступает одна ночь отпуска.\n"
        "• Накопите минимум 7 ночей и отправляйтесь в путешествие.\n"
        "• Квартиры бизнес-класса в Таиланде.\n"
        "• Оплата в TON.\n\n"
        "Когда вы планируете свой отпуск?"
    )
    # Кнопки выбора месяца, дня, "Определюсь позже"
    now = datetime.now()
    nearest_date = get_nearest_available_date(now, min_nights=7)
    keyboard = [
        [InlineKeyboardButton("Выбрать месяц", callback_data="choose_month")],
        [InlineKeyboardButton("Выбрать день", callback_data="choose_day")],
        [InlineKeyboardButton("Определюсь позже", callback_data="later")],
    ]
    await update.message.reply_text(
        f"{welcome_message}\n\nБлижайшая доступная дата для 7 ночей: {nearest_date.strftime('%d.%m.%Y')}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обработка выбора даты
async def choose_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    months = [(datetime.now() + timedelta(days=30*i)).strftime('%B %Y') for i in range(1, 13)]
    keyboard = [[InlineKeyboardButton(month, callback_data=f"month_{i}")] for i, month in enumerate(months, 1)]
    await update.callback_query.edit_message_text(
        "Выберите месяц:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def choose_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    days = [(datetime.now() + timedelta(days=i)).strftime('%d.%m.%Y') for i in range(1, 32)]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"day_{i}")] for i, day in enumerate(days, 1)]
    await update.callback_query.edit_message_text(
        "Выберите день:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def choose_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cities = ["Пхукет", "Бангкок", "Паттайя", "Самуи", "Пхи-Пхи", "Краби"]
    keyboard = [[InlineKeyboardButton(city, callback_data=f"city_{city}")] for city in cities]
    await update.callback_query.edit_message_text(
        "В каком городе Таиланда вы бы хотели провести отпуск?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def offer_apartment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Заглушка: показываем одну типовую квартиру
    await update.callback_query.edit_message_text(
        "На эти даты есть прекрасная квартира бизнес-класса в выбранном городе.\n\nВидео-тур: [ссылка]\n\nОписание: ...\n\nУ вас остались вопросы?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Оформить подписку", callback_data="subscribe")],
            [InlineKeyboardButton("Задать вопрос", callback_data="ask")],
            [InlineKeyboardButton("Вернуться в начало", callback_data="start")],
        ])
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем состояние для следующего шага
    context.user_data['state'] = 'waiting_name'
    
    await update.callback_query.edit_message_text(
        "Для оформления подписки введите Имя и Фамилию в формате:\n"
        "Иван Иванов"
    )

async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'waiting_name':
        return
    
    try:
        first_name, last_name = update.message.text.split(' ', 1)
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите имя и фамилию через пробел.\n"
            "Например: Иван Иванов"
        )
        return
    
    # Сохраняем данные пользователя
    context.user_data['first_name'] = first_name
    context.user_data['last_name'] = last_name
    
    # Инициализируем TON клиент
    ton_client = TONClient(api_key=context.bot_data['ton_api_key'])
    
    # Рассчитываем сумму в TON
    amount_rub = 3000  # Стоимость подписки в рублях
    amount_ton = ton_client.calculate_ton_amount(amount_rub)
    
    # Генерируем адрес для оплаты
    payment_info = ton_client.generate_payment_address(amount_ton)
    
    # Сохраняем информацию о платеже
    context.user_data['payment_address'] = payment_info['address']
    context.user_data['amount_ton'] = amount_ton
    
    # Формируем сообщение с инструкциями
    message = (
        f"Отлично, {first_name}!\n\n"
        f"Для активации подписки необходимо оплатить {amount_ton:.2f} TON\n\n"
        f"Инструкция по оплате:\n"
        f"1. Откройте ваш TON кошелек\n"
        f"2. Отправьте {amount_ton:.2f} TON на адрес:\n"
        f"`{payment_info['address']}`\n\n"
        f"После подтверждения платежа, ваша подписка будет активирована автоматически.\n"
        f"Срок действия счета: 24 часа"
    )
    
    keyboard = [
        [InlineKeyboardButton("Проверить статус оплаты", callback_data="check_payment")],
        [InlineKeyboardButton("Отменить", callback_data="cancel_subscription")]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    # Меняем состояние
    context.user_data['state'] = 'waiting_payment'

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('payment_address'):
        logger.warning(f"Пользователь {update.effective_user.id} пытается проверить несуществующий платеж")
        await update.callback_query.answer("Ошибка: платеж не найден")
        return
    
    logger.info(f"Пользователь {update.effective_user.id} проверяет статус платежа")
    ton_client = TONClient(api_key=context.bot_data['ton_api_key'])
    payment_status = ton_client.check_payment_status(context.user_data['payment_address'])
    
    if payment_status['status'] == 'completed':
        # Создаем пользователя и подписку в базе данных
        session = Session()
        try:
            user = User(
                telegram_id=update.effective_user.id,
                first_name=context.user_data['first_name'],
                last_name=context.user_data['last_name']
            )
            session.add(user)
            session.commit()
            
            subscription = Subscription(
                user_id=user.id,
                start_date=datetime.utcnow(),
                status='active'
            )
            session.add(subscription)
            session.commit()
            
            payment = Payment(
                subscription_id=subscription.id,
                amount_ton=context.user_data['amount_ton'],
                status=PaymentStatus.COMPLETED,
                ton_address=context.user_data['payment_address'],
                completed_at=datetime.utcnow()
            )
            session.add(payment)
            session.commit()
            
            logger.info(f"Платеж подтвержден для пользователя {update.effective_user.id}")
            
            await update.callback_query.edit_message_text(
                "Оплата подтверждена! Ваша подписка активирована.\n\n"
                "Теперь вы можете накапливать ночи для вашего отпуска."
            )
            context.user_data.clear()
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя {update.effective_user.id}: {str(e)}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()
    else:
        logger.info(f"Платеж еще не получен для пользователя {update.effective_user.id}")
        await update.callback_query.answer(
            "Оплата еще не получена. Пожалуйста, проверьте статус позже.",
            show_alert=True
        )

# Роутинг callback_data
callback_map = {
    "choose_month": choose_month,
    "choose_day": choose_day,
    "later": subscribe,  # если "определюсь позже" — сразу к подписке
    "subscribe": subscribe,
    "check_payment": check_payment,
    "cancel_subscription": lambda u, c: u.callback_query.edit_message_text("Подписка отменена.")
}

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    handler = callback_map.get(data)
    if handler:
        await handler(update, context)
    elif data.startswith("month_") or data.startswith("day_"):
        await choose_city(update, context)
    elif data.startswith("city_"):
        await offer_apartment(update, context)
    else:
        await update.callback_query.answer("В разработке...")

def setup_handlers(application):
    # Базовые команды
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(callback_router))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}", exc_info=True)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже или начните сначала с команды /start"
        ) 