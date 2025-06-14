from telegram import Bot
from config import BOT_TOKEN
from database.models import User, Subscription, PaymentStatus
from typing import Optional

class NotificationService:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)

    async def send_payment_success(self, user: User, subscription_id: int):
        """
        Отправляет уведомление об успешной оплате
        """
        message = (
            f"🎉 Поздравляем, {user.first_name}!\n\n"
            f"Ваш платеж успешно обработан.\n"
            f"Подписка активирована.\n\n"
            f"Теперь вы можете накапливать ночи для вашего отпуска."
        )
        await self.bot.send_message(chat_id=user.telegram_id, text=message)

    async def send_payment_reminder(self, user: User, subscription_id: int):
        """
        Отправляет напоминание об оплате
        """
        message = (
            f"👋 {user.first_name}, не забудьте оплатить подписку!\n\n"
            f"Для продолжения накопления ночей необходимо внести оплату.\n"
            f"Сумма: 3 000 руб.\n\n"
            f"Нажмите /subscribe для оформления подписки."
        )
        await self.bot.send_message(chat_id=user.telegram_id, text=message)

    async def send_night_accumulated(self, user: User, subscription: Subscription):
        """
        Отправляет уведомление о накоплении ночи
        """
        message = (
            f"✨ {user.first_name}, поздравляем!\n\n"
            f"Вы накопили {subscription.accumulated_nights} ночей.\n"
            f"До минимального количества осталось: {7 - subscription.accumulated_nights} ночей.\n\n"
            f"Продолжайте накапливать ночи для вашего отпуска!"
        )
        await self.bot.send_message(chat_id=user.telegram_id, text=message)

    async def send_subscription_expiring(self, user: User, subscription: Subscription):
        """
        Отправляет уведомление об истечении подписки
        """
        message = (
            f"⚠️ {user.first_name}, внимание!\n\n"
            f"Ваша подписка истекает через 3 дня.\n"
            f"Для продления нажмите /subscribe\n\n"
            f"Не теряйте накопленные ночи!"
        )
        await self.bot.send_message(chat_id=user.telegram_id, text=message)

    async def send_vacation_ready(self, user: User, subscription: Subscription):
        """
        Отправляет уведомление о готовности к отпуску
        """
        message = (
            f"🎉 {user.first_name}, отличные новости!\n\n"
            f"Вы накопили достаточно ночей для отпуска!\n"
            f"Всего накоплено: {subscription.accumulated_nights} ночей\n\n"
            f"Нажмите /book для выбора дат и бронирования квартиры."
        )
        await self.bot.send_message(chat_id=user.telegram_id, text=message) 