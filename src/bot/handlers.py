import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from database.models import User, Subscription, Payment, PaymentStatus, Apartment
from database.migrations import init_db
from utils.helpers import get_nearest_available_date, format_apartment_info
from ton.ton_client import TONClient
import os
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения (нужно для BOT_TOKEN в этом файле)
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN') # Используем BOT_TOKEN напрямую для инициализации Bot в offer_apartment
TON_API_KEY = os.getenv('TON_API_KEY') # Для TONClient

# Словарь для перевода названий месяцев на русский
MONTH_NAMES_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# Список городов Таиланда из ТЗ
THAILAND_CITIES = ["Пхукет", "Бангкок", "Паттайя", "Самуи", "Пхи-Пхи", "Краби"]

async def type_message(update_or_query: Update | Any, text: str, reply_markup=None, is_edit: bool = False):
    """Имитирует набор текста и отправляет сообщение."""
    if hasattr(update_or_query, 'callback_query'):
        query = update_or_query.callback_query
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        bot_instance = query.bot
    else:
        chat_id = update_or_query.effective_chat.id
        message_id = update_or_query.message_id
        bot_instance = update_or_query.bot

    await bot_instance.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(len(text) * 0.05)

    if is_edit:
        await bot_instance.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
    else:
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(text, reply_markup=reply_markup)
        else:
            await bot_instance.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

async def send_month_selection(query: Any):
    """Отправляет сообщение с кнопками выбора месяца."""
    current_date = datetime.now()
    nearest_available_date = get_nearest_available_date(current_date, min_nights=7)
    nearest_month_name_ru = MONTH_NAMES_RU[nearest_available_date.month]
    nearest_month_year = nearest_available_date.year

    month_question_text = (
        f"На какой месяц планируете в отпуск в Таиланде? "
        f"Ближайший доступный месяц - {nearest_month_name_ru} {nearest_month_year} года."
    )

    months_list = list(MONTH_NAMES_RU.values())
    
    keyboard = []
    for i in range(0, len(months_list), 3):
        row = []
        for j in range(3):
            if (i + j) < len(months_list):
                month_name = months_list[i+j]
                month_number = list(MONTH_NAMES_RU.keys())[list(MONTH_NAMES_RU.values()).index(month_name)]
                row.append(InlineKeyboardButton(month_name, callback_data=f"select_month_{month_number}"))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("Вернуться назад", callback_data="back_to_main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=month_question_text, reply_markup=reply_markup)
    logger.info("Отправлены кнопки выбора месяца.")

async def send_city_selection(query: Any, selected_month_name: str):
    """Отправляет сообщение с кнопками выбора города."""
    city_question_text = (
        f"Отлично, {selected_month_name} - прекрасный месяц для поездки в Таиланд. "
        f"В каком городе вы хотели бы отдохнуть? На стоимость подписки это не влияет, поэтому выбирайте по душе!"
    )

    keyboard = []
    for i in range(0, len(THAILAND_CITIES), 2):
        row = []
        for j in range(2):
            if (i + j) < len(THAILAND_CITIES):
                city = THAILAND_CITIES[i+j]
                row.append(InlineKeyboardButton(city, callback_data=f"select_city_{city}"))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("Вернуться назад", callback_data="back_to_month_selection")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=city_question_text, reply_markup=reply_markup)
    logger.info(f"Отправлены кнопки выбора города после выбора месяца {selected_month_name}.")

async def offer_apartment(query: Any, city_name: str):
    """Получает информацию о базовой квартире из БД и предлагает ее пользователю."""
    db_session = init_db()
    try:
        apartment = db_session.query(Apartment).filter(
            Apartment.city == city_name,
            Apartment.apartment_type == "Base"
        ).first()

        if not apartment:
            error_message = f"Извините, для города {city_name} базовая квартира пока не найдена. Пожалуйста, попробуйте другой город или обратитесь в поддержку."
            await type_message(query, error_message, is_edit=True)
            logger.warning(f"Базовая квартира для города {city_name} не найдена в БД.")
            await send_city_selection(query, "выбранный месяц") # Возвращаем к выбору города
            return

        apartment_info = format_apartment_info({
            'city': apartment.city,
            'address': apartment.address,
            'area_sqm': apartment.area_sqm,
            'num_bedrooms': apartment.num_bedrooms,
            'description': apartment.description,
            'features': apartment.features,
            'nearby_attractions': apartment.nearby_attractions
        })

        # Проверяем наличие BOT_TOKEN перед отправкой видео
        if BOT_TOKEN and apartment.video_url:
            bot_instance_for_video = Bot(token=BOT_TOKEN)
            await bot_instance_for_video.send_video(chat_id=query.message.chat_id, video=apartment.video_url, caption="Видео-тур по квартире:")
            logger.info(f"Отправлен видео-тур для квартиры в {city_name}.")
        elif not BOT_TOKEN:
             logger.warning("BOT_TOKEN не установлен. Видео не может быть отправлено.")
        else:
            logger.info(f"Видео URL для квартиры в {city_name} отсутствует.")


        offer_message = f"На эти даты есть прекрасная квартира бизнес-класса в {apartment.city}.\n\n" + apartment_info
        # Отправляем сообщение без редактирования, чтобы видео осталось
        await type_message(query, offer_message, is_edit=False)

        action_message = "У вас остались вопросы?"
        keyboard = [
            [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_now")],
            [InlineKeyboardButton("Задать вопрос", callback_data="ask_question")],
            [InlineKeyboardButton("Вернуться в начало", callback_data="start_over")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await type_message(query, action_message, reply_markup=reply_markup, is_edit=False)
        logger.info(f"Информация о квартире в {city_name} отправлена пользователю.")

    finally:
        db_session.close()

# Приветствие и старт (расширенная версия из main.py)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
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
    await type_message(update, welcome_message)

    current_date = datetime.now()
    available_date_for_7_nights = get_nearest_available_date(current_date, min_nights=7)
    formatted_available_date = available_date_for_7_nights.strftime("%d.%m.%Y")

    question_text = f"Когда вы планируете свой отпуск?\n\nБлижайшая доступная дата для 7 ночей: {formatted_available_date}"

    keyboard = [
        [
            InlineKeyboardButton("ДАТА", callback_data="plan_date_choice"),
            InlineKeyboardButton("ОПРЕДЕЛЮСЬ ПОЗЖЕ", callback_data="plan_later")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await type_message(update, question_text, reply_markup=reply_markup)
    logger.info("Отправлен вопрос о планировании отпуска с инлайн-кнопками 'ДАТА' и 'ОПРЕДЕЛЮСЬ ПОЗЖЕ'.")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем состояние для следующего шага
    context.user_data['state'] = 'waiting_name'
    
    # Используем edit_message_text для колбэка
    await update.callback_query.edit_message_text(
        "Для оформления подписки введите Имя и Фамилию в формате:\n"
        "Иван Иванов"
    )
    logger.info(f"Пользователь {update.effective_user.id} начал процесс подписки, ожидаем имя.")


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'waiting_name':
        return
    
    try:
        # Убедимся, что имя и фамилия присутствуют
        full_name_parts = update.message.text.strip().split(' ', 1)
        if len(full_name_parts) < 2:
            raise ValueError("Имя и фамилия должны быть указаны через пробел.")
        first_name, last_name = full_name_parts
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите имя и фамилию через пробел.\n"
            "Например: Иван Иванов"
        )
        return
    
    context.user_data['first_name'] = first_name
    context.user_data['last_name'] = last_name
    
    # Инициализируем TON клиент
    if not TON_API_KEY:
        logger.error("TON_API_KEY не найден в .env файле.")
        await update.message.reply_text("Ошибка: TON API ключ не настроен. Пожалуйста, свяжитесь с поддержкой.")
        context.user_data.clear() # Очищаем состояние
        return
    
    ton_client = TONClient(api_key=TON_API_KEY)
    
    amount_rub = 3000  # Стоимость подписки в рублях
    amount_ton = ton_client.calculate_ton_amount(amount_rub)
    
    payment_info = ton_client.generate_payment_address(amount_ton)
    
    context.user_data['payment_address'] = payment_info['address']
    context.user_data['amount_ton'] = amount_ton
    
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
    
    context.user_data['state'] = 'waiting_payment'
    logger.info(f"Пользователю {update.effective_user.id} отправлены инструкции по оплате TON.")

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('payment_address'):
        logger.warning(f"Пользователь {update.effective_user.id} пытается проверить несуществующий платеж")
        await update.callback_query.answer("Ошибка: платеж не найден")
        return
    
    logger.info(f"Пользователь {update.effective_user.id} проверяет статус платежа")
    
    if not TON_API_KEY:
        logger.error("TON_API_KEY не найден в .env файле.")
        await update.callback_query.answer("Ошибка: TON API ключ не настроен. Пожалуйста, свяжитесь с поддержкой.", show_alert=True)
        return

    ton_client = TONClient(api_key=TON_API_KEY)
    payment_status = ton_client.check_payment_status(context.user_data['payment_address'])
    
    if payment_status['status'] == 'completed':
        session = init_db()
        try:
            # Проверяем, существует ли пользователь, если нет - создаем
            user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
            if not user:
                user = User(
                    telegram_id=update.effective_user.id,
                    first_name=context.user_data['first_name'],
                    last_name=context.user_data['last_name']
                )
                session.add(user)
                session.commit()
                session.refresh(user) # Обновляем user, чтобы получить id

            # Проверяем, существует ли активная подписка
            subscription = session.query(Subscription).filter_by(user_id=user.id, status=SubscriptionStatus.ACTIVE).first()
            if not subscription:
                subscription = Subscription(
                    user_id=user.id,
                    start_date=datetime.utcnow(),
                    status='active',
                    amount_rub=3000.0, # Добавил стоимость в рублях
                    amount_ton=context.user_data['amount_ton'] # Добавил стоимость в TON
                )
                session.add(subscription)
                session.commit()
                session.refresh(subscription)

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
            context.user_data.clear() # Очищаем данные пользователя после успешной подписки
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя {update.effective_user.id}: {str(e)}", exc_info=True)
            session.rollback()
            await update.callback_query.answer("Произошла ошибка при активации подписки. Пожалуйста, попробуйте позже.", show_alert=True)
        finally:
            session.close()
    else:
        logger.info(f"Платеж еще не получен для пользователя {update.effective_user.id}")
        await update.callback_query.answer(
            "Оплата еще не получена. Пожалуйста, проверьте статус позже.",
            show_alert=True
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}", exc_info=True)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже или начните сначала с команды /start"
        )

# Роутинг callback_data
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logger.info(f"Получен callback_data: {query.data} от пользователя {query.from_user.id}")

    if query.data == "plan_date_choice":
        await send_month_selection(query)
        logger.info("Пользователь выбрал 'ДАТА'. Отправлены кнопки выбора месяца.")
    elif query.data == "plan_later":
        subscribe_message = "У вас остались вопросы? Если вы готовы, предлагаем оформить подписку."
        keyboard = [
            [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_now")],
            [InlineKeyboardButton("Задать вопрос", callback_data="ask_question")],
            [InlineKeyboardButton("Вернуться в начало", callback_data="start_over")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await type_message(query, subscribe_message, reply_markup=reply_markup, is_edit=True)
        logger.info("Пользователь выбрал 'Определюсь позже', предложено оформить подписку.")
    
    elif query.data.startswith("select_month_"):
        month_number = int(query.data.split('_')[2])
        selected_month_name = MONTH_NAMES_RU[month_number]
        await send_city_selection(query, selected_month_name)
    
    elif query.data.startswith("select_city_"):
        city_name = query.data.split('_')[2]
        await type_message(query, f"Вы выбрали город: {city_name}. Теперь я подберу для вас квартиру. Минуточку...", is_edit=True)
        await asyncio.sleep(2)
        await offer_apartment(query, city_name)
        logger.info(f"Пользователь выбрал город: {city_name}. Запущен подбор квартиры.")

    elif query.data == "subscribe_now":
        # Перенаправляем на функцию subscribe
        await subscribe(update, context)
        logger.info("Пользователь выбрал 'Оформить подписку'.")
    elif query.data == "ask_question":
        await type_message(query, "Пожалуйста, задайте свой вопрос. Я постараюсь на него ответить или свяжу вас с поддержкой.", is_edit=True)
        logger.info("Пользователь выбрал 'Задать вопрос'.")
    elif query.data == "start_over":
        # Используем reply_text вместо edit_message_text для /start, так как это новая "ветка" взаимодействия
        await type_message(query, "Вы вернулись в начало. Отправьте /start снова, чтобы увидеть приветствие.", is_edit=True)
        logger.info("Пользователь выбрал 'Вернуться в начало'.")

    elif query.data == "back_to_main_menu":
        current_date = datetime.now()
        available_date_for_7_nights = get_nearest_available_date(current_date, min_nights=7)
        formatted_available_date = available_date_for_7_nights.strftime("%d.%m.%Y")

        question_text = f"Когда вы планируете свой отпуск?\n\nБлижайшая доступная дата для 7 ночей: {formatted_available_date}"

        keyboard = [
            [
                InlineKeyboardButton("ДАТА", callback_data="plan_date_choice"),
                InlineKeyboardButton("ОПРЕДЕЛЮСЬ ПОЗЖЕ", callback_data="plan_later")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await type_message(query, question_text, reply_markup=reply_markup, is_edit=True)
        logger.info("Пользователь вернулся к главному меню планирования отпуска.")
    
    elif query.data == "back_to_month_selection":
        await send_month_selection(query)
        logger.info("Пользователь вернулся к выбору месяца.")
    
    elif query.data == "check_payment":
        await check_payment(update, context)

    elif query.data == "cancel_subscription":
        await update.callback_query.edit_message_text("Подписка отменена.")
        context.user_data.clear() # Очищаем состояние
        logger.info(f"Пользователь {update.effective_user.id} отменил подписку.")


def setup_handlers(application):
    """
    Настраивает все обработчики для Telegram-бота.
    """
    # Базовые команды
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики callback-запросов (единый роутер)
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Обработчик текстовых сообщений для получения имени и фамилии
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)