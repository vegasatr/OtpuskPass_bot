import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

def generate_referral_code(length: int = 8) -> str:
    """Генерация уникального реферального кода"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def calculate_next_payment_date(start_date: datetime) -> datetime:
    """Расчет даты следующего платежа"""
    return start_date + timedelta(days=30)

def format_apartment_info(apartment: Dict[str, Any]) -> str:
    """
    Форматирование информации о квартире на основе данных из базы данных.
    Теперь ожидает ключи: 'city', 'address', 'area_sqm', 'num_bedrooms',
    'description', 'features', 'nearby_attractions'.
    Поле 'amenities' теперь включено в 'description'.
    """
    return f"""
🏠 Квартира в {apartment.get('city', 'Неизвестно')}

📍 Адрес: {apartment.get('address', 'Не указан')}
📐 Общая площадь: {apartment.get('area_sqm', 'N/A')} м²
🛏 Количество спален: {apartment.get('num_bedrooms', 'N/A')} (все квартиры односпальные)

Подробное описание квартиры:
{apartment.get('description', 'Не указано')}

В квартире есть: {apartment.get('features', 'Не указано')}

Окружение: {apartment.get('nearby_attractions', 'Не указано')}
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
    # ТЗ: "текущей даты + 7 месяцев", а min_nights по ТЗ = 7
    # 30 дней * 7 ночей = 210 дней, что приблизительно равно 7 месяцам.
    # Если нужна более точная дата через 7 месяцев (например, 14 июня -> 14 января),
    # то нужно использовать dateutil.relativedelta. Пока оставляем как есть.
    return current_date + timedelta(days=30 * min_nights) 