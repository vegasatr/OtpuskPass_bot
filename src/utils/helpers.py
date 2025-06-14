import random
import string
from datetime import datetime, timedelta
from typing import Optional

def generate_referral_code(length: int = 8) -> str:
    """Генерация уникального реферального кода"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def calculate_next_payment_date(start_date: datetime) -> datetime:
    """Расчет даты следующего платежа"""
    return start_date + timedelta(days=30)

def format_apartment_info(apartment: dict) -> str:
    """Форматирование информации о квартире"""
    return f"""
🏠 Квартира в {apartment['city']}

📍 Адрес: {apartment['address']}
📐 Площадь: {apartment['area_sqm']} м²
🛏 Спальни: {apartment['num_bedrooms']}

📝 Описание:
{apartment['description']}

✨ Особенности:
{apartment['features']}

🏖️ Рядом:
{apartment['nearby_attractions']}
"""

def format_subscription_info(subscription: dict) -> str:
    """Форматирование информации о подписке"""
    return f"""
📅 Статус подписки: {subscription['status']}
💰 Стоимость: {subscription['amount_rub']} руб. в месяц
💎 В TON: {subscription['amount_ton']} TON
📅 Следующий платеж: {subscription['next_payment_date']}
"""

def validate_booking_dates(start_date: datetime, end_date: datetime, min_nights: int = 7) -> bool:
    """Проверка корректности дат бронирования"""
    if start_date >= end_date:
        return False
    
    nights = (end_date - start_date).days
    return nights >= min_nights

def format_ton_amount(amount: float) -> str:
    """Форматирование суммы в TON"""
    return f"{amount:.4f} TON"

def get_nearest_available_date(current_date: datetime, min_nights: int = 7) -> datetime:
    """Получение ближайшей доступной даты для бронирования"""
    return current_date + timedelta(days=30 * min_nights) 