import os
from dotenv import load_dotenv
import aiohttp
from datetime import datetime
from database.models import PaymentTransaction
from sqlalchemy.orm import Session

# Загрузка переменных окружения
load_dotenv()

# Получение адреса кошелька TON
TON_WALLET_ADDRESS = os.getenv('TON_WALLET_ADDRESS')

class TONPaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.wallet_address = TON_WALLET_ADDRESS

    async def get_ton_price(self) -> float:
        """Получение текущей цены TON в рублях"""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=rub') as response:
                data = await response.json()
                return data['the-open-network']['rub']

    async def calculate_ton_amount(self, rub_amount: float) -> float:
        """Расчет суммы в TON на основе суммы в рублях"""
        ton_price = await self.get_ton_price()
        return rub_amount / ton_price

    async def create_payment_transaction(self, user_id: int, rub_amount: float) -> PaymentTransaction:
        """Создание транзакции платежа"""
        ton_amount = await self.calculate_ton_amount(rub_amount)
        
        transaction = PaymentTransaction(
            user_id=user_id,
            amount_rub=rub_amount,
            amount_ton=ton_amount,
            type="subscription",
            status="pending"
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction

    async def verify_payment(self, transaction_hash: str) -> bool:
        """Проверка статуса платежа"""
        # TODO: Реализовать проверку транзакции через TON API
        # Временная заглушка
        return True

    async def process_payment(self, user_id: int, rub_amount: float = 3000.0) -> dict:
        """Обработка платежа"""
        transaction = await self.create_payment_transaction(user_id, rub_amount)
        
        return {
            "wallet_address": self.wallet_address,
            "amount_ton": transaction.amount_ton,
            "transaction_id": transaction.id
        }

    async def check_payment_status(self, transaction_id: int) -> str:
        """Проверка статуса платежа по ID транзакции"""
        transaction = self.db.query(PaymentTransaction).filter(
            PaymentTransaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValueError("Транзакция не найдена")
            
        if transaction.status == "pending":
            is_verified = await self.verify_payment(transaction.transaction_hash)
            if is_verified:
                transaction.status = "completed"
                self.db.commit()
                
        return transaction.status 