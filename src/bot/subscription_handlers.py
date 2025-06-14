import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import User, Subscription, Payment, PaymentStatus, SubscriptionStatus
from database.migrations import init_db
from ton.ton_client import TONClient
import os
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TON_API_KEY = os.getenv('TON_API_KEY')

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик начала процесса подписки"""
    # Сохраняем состояние для следующего шага
    context.user_data['state'] = 'waiting_name'
    
    # Используем edit_message_text для колбэка
    await update.callback_query.edit_message_text(
        "Для оформления подписки введите Имя и Фамилию в формате:\n"
        "Иван Иванов"
    )
    logger.info(f"Пользователь {update.effective_user.id} начал процесс подписки, ожидаем имя.")

async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода имени и фамилии"""
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
    """Обработчик проверки статуса платежа"""
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
                    amount_rub=3000.0,
                    amount_ton=context.user_data['amount_ton']
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

async def cancel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены подписки"""
    await update.callback_query.edit_message_text("Подписка отменена.")
    context.user_data.clear() # Очищаем состояние
    logger.info(f"Пользователь {update.effective_user.id} отменил подписку.") 