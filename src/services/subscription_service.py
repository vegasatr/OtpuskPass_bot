from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import User, Subscription, Payment, PaymentStatus, SubscriptionStatus
from ton.ton_connect import TONConnect
from config import SUBSCRIPTION_PRICE_RUB
from typing import Optional

class SubscriptionService:
    def __init__(self, session: Session):
        self.session = session
        self.ton_connect = TONConnect()

    def create_subscription(self, telegram_id: int, first_name: str, last_name: str) -> tuple[User, Subscription, Payment]:
        """
        Создает новую подписку для пользователя
        """
        # Создаем или получаем пользователя
        user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name
            )
            self.session.add(user)
            self.session.commit()

        # Создаем подписку
        subscription = Subscription(
            user_id=user.id,
            start_date=datetime.utcnow(),
            status=SubscriptionStatus.ACTIVE
        )
        self.session.add(subscription)
        self.session.commit()

        # Рассчитываем сумму в TON
        amount_ton = self.ton_connect.calculate_ton_amount(SUBSCRIPTION_PRICE_RUB)
        
        # Создаем платеж
        payment_info = self.ton_connect.create_payment_request(amount_ton)
        
        payment = Payment(
            subscription_id=subscription.id,
            amount_ton=amount_ton,
            status=PaymentStatus.PENDING,
            ton_address=payment_info['address']
        )
        self.session.add(payment)
        self.session.commit()

        return user, subscription, payment

    def check_payment(self, payment_id: int) -> bool:
        """
        Проверяет статус платежа и обновляет подписку при успешной оплате
        """
        payment = self.session.query(Payment).get(payment_id)
        if not payment:
            return False

        payment_status = self.ton_connect.check_payment_status(payment.ton_address)
        
        if payment_status['status'] == 'completed':
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            
            subscription = payment.subscription
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.accumulated_nights += 1
            
            self.session.commit()
            return True
        
        return False

    def get_user_subscription(self, telegram_id: int) -> Optional[Subscription]:
        """
        Получает активную подписку пользователя
        """
        user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return None

        return self.session.query(Subscription)\
            .filter_by(user_id=user.id, status=SubscriptionStatus.ACTIVE)\
            .first()

    def add_night(self, subscription_id: int) -> bool:
        """
        Добавляет одну ночь к подписке
        """
        subscription = self.session.query(Subscription).get(subscription_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return False

        subscription.accumulated_nights += 1
        self.session.commit()
        return True

    def get_subscription_status(self, subscription_id: int) -> dict:
        """
        Возвращает статус подписки
        """
        subscription = self.session.query(Subscription).get(subscription_id)
        if not subscription:
            return None

        return {
            'status': subscription.status.value,
            'accumulated_nights': subscription.accumulated_nights,
            'start_date': subscription.start_date.isoformat(),
            'user': {
                'first_name': subscription.user.first_name,
                'last_name': subscription.user.last_name
            }
        } 