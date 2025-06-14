import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters, Application

from database.models import User, Subscription, Payment, PaymentStatus, Apartment
from database.migrations import init_db
from utils.helpers import get_nearest_available_date, format_apartment_info
from ton.ton_client import TONClient
import os
from dotenv import load_dotenv
from .subscription_handlers import (
    subscribe,
    handle_name_input,
    check_payment,
    cancel_subscription
)

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
TON_API_KEY = os.getenv('TON_API_KEY')

# Словарь для перевода названий месяцев на русский
MONTH_NAMES_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# Список городов Таиланда из ТЗ
THAILAND_CITIES = ["Пхукет", "Бангкок", "Паттайя", "Самуи", "Пхи-Пхи", "Краби"]

async def type_message(update_or_query: Update | Any, text: str, reply_markup=None, is_edit: bool = False):
    """Универсально отправляет или редактирует сообщение, поддерживает message и callback_query."""
    # Определяем chat_id, message_id и bot_instance
    chat_id = None
    message_id = None
    bot_instance = None
    message_obj = None

    # Если это callback_query
    if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query:
        query = update_or_query.callback_query
        if query.message:
            chat_id = query.message.chat_id
            message_id = query.message.message_id
            bot_instance = query.bot
            message_obj = query.message
    # Если это обычное сообщение
    elif hasattr(update_or_query, 'message') and update_or_query.message:
        chat_id = update_or_query.message.chat_id
        message_id = update_or_query.message.message_id
        # Если у сообщения нет атрибута bot, берем его из update_or_query
        if hasattr(update_or_query.message, 'bot'):
            bot_instance = update_or_query.message.bot
        else:
            bot_instance = update_or_query.get_bot() if hasattr(update_or_query, 'get_bot') else None
        message_obj = update_or_query.message
    # Если это Update с effective_chat
    elif hasattr(update_or_query, 'effective_chat') and update_or_query.effective_chat:
        chat_id = update_or_query.effective_chat.id
        bot_instance = update_or_query.get_bot() if hasattr(update_or_query, 'get_bot') else None

    if is_edit and bot_instance and chat_id and message_id:
        await bot_instance.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
    elif message_obj:
        await message_obj.reply_text(text, reply_markup=reply_markup)
    elif bot_instance and chat_id:
        await bot_instance.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
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

    # Отправляем приветственное сообщение
    await type_message(update, welcome_message)

    # Получаем ближайшую доступную дату
    current_date = datetime.now()
    available_date_for_7_nights = get_nearest_available_date(current_date, min_nights=7)
    formatted_available_date = available_date_for_7_nights.strftime("%d.%m.%Y")

    # Отправляем вопрос о планировании отпуска
    question_text = f"Когда вы планируете свой отпуск?\n\nБлижайшая доступная дата для 7 ночей: {formatted_available_date}"
    keyboard = [
        [
            InlineKeyboardButton("ДАТА", callback_data="plan_date_choice"),
            InlineKeyboardButton("ОПРЕДЕЛЮСЬ ПОЗЖЕ", callback_data="plan_later")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await type_message(update, question_text, reply_markup=reply_markup)

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
            await send_city_selection(query, "выбранный месяц")
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

        if apartment.video_url:
            await query.message.reply_video(video=apartment.video_url, caption="Видео-тур по квартире:")
            logger.info(f"Отправлен видео-тур для квартиры в {city_name}.")

        offer_message = f"На эти даты есть прекрасная квартира бизнес-класса в {apartment.city}.\n\n" + apartment_info
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

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на инлайн-кнопки"""
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
        await type_message(query, "Отлично! Для оформления подписки, пожалуйста, введите ваше Имя и Фамилию.", is_edit=True)
        logger.info("Пользователь выбрал 'Оформить подписку'.")
    elif query.data == "ask_question":
        await type_message(query, "Пожалуйста, задайте свой вопрос. Я постараюсь на него ответить или свяжу вас с поддержкой.", is_edit=True)
        logger.info("Пользователь выбрал 'Задать вопрос'.")
    elif query.data == "start_over":
        await type_message(query, "Вы вернулись в начало. Отправьте /start снова, чтобы увидеть приветствие.", is_edit=False)
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

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}", exc_info=True)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже или начните сначала с команды /start"
        )

def setup_handlers(application: Application):
    """Настройка обработчиков команд и колбэков"""
    # Базовые команды
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики подписок
    application.add_handler(CallbackQueryHandler(subscribe, pattern="^subscribe$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input))
    application.add_handler(CallbackQueryHandler(check_payment, pattern="^check_payment$"))
    application.add_handler(CallbackQueryHandler(cancel_subscription, pattern="^cancel_subscription$"))
    
    # Обработчики бронирования
    application.add_handler(CallbackQueryHandler(send_month_selection, pattern="^book$"))
    application.add_handler(CallbackQueryHandler(send_city_selection, pattern="^month_"))
    application.add_handler(CallbackQueryHandler(offer_apartment, pattern="^city_"))
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)