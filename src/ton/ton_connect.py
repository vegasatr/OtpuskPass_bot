from typing import Dict, Optional
import requests
import json
from datetime import datetime, timedelta
from config import TON_API_KEY, TON_API_URL

class TONConnect:
    def __init__(self):
        self.api_key = TON_API_KEY
        self.base_url = TON_API_URL
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_payment_request(self, amount_ton: float) -> Dict:
        """
        Создает запрос на оплату в TON
        """
        endpoint = f"{self.base_url}/createPayment"
        payload = {
            "amount": str(amount_ton),
            "currency": "TON",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при создании платежа: {str(e)}")

    def check_payment_status(self, payment_id: str) -> Dict:
        """
        Проверяет статус платежа
        """
        endpoint = f"{self.base_url}/payment/{payment_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при проверке статуса платежа: {str(e)}")

    def get_ton_price(self) -> float:
        """
        Получает текущий курс TON
        """
        endpoint = f"{self.base_url}/price"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except (requests.exceptions.RequestException, KeyError, ValueError) as e:
            raise Exception(f"Ошибка при получении курса TON: {str(e)}")

    def calculate_ton_amount(self, amount_rub: float) -> float:
        """
        Рассчитывает сумму в TON на основе суммы в рублях
        """
        ton_price = self.get_ton_price()
        # Примерный курс USD к RUB
        usd_to_rub = 90
        return (amount_rub / usd_to_rub) / ton_price 