import asyncio
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.models import Payment, PaymentStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')

class PaymentChecker:
    def __init__(self):
        logger.info("Инициализация PaymentChecker...")
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.check_interval = 300  # 5 минут
        logger.info("PaymentChecker инициализирован")

    async def start(self):
        """
        Запускает периодическую проверку платежей
        """
        logger.info("Запуск проверки платежей...")
        while True:
            try:
                await self.check_pending_payments()
            except Exception as e:
                logger.error(f"Ошибка при проверке платежей: {str(e)}", exc_info=True)
            
            await asyncio.sleep(self.check_interval)

    async def check_pending_payments(self):
        """
        Проверяет все ожидающие платежи
        """
        session = self.Session()
        try:
            # Получаем все ожидающие платежи
            pending_payments = session.query(Payment)\
                .filter_by(status=PaymentStatus.PENDING)\
                .filter(Payment.created_at > datetime.utcnow() - timedelta(hours=24))\
                .all()

            logger.info(f"Найдено {len(pending_payments)} ожидающих платежей")
            
            for payment in pending_payments:
                try:
                    # TODO: Добавить проверку платежа через TON API
                    logger.info(f"Проверка платежа {payment.id}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке платежа {payment.id}: {str(e)}", exc_info=True)

        finally:
            session.close()

    def run(self):
        """
        Запускает проверку платежей в асинхронном режиме
        """
        logger.info("Запуск PaymentChecker в асинхронном режиме...")
        loop = asyncio.get_event_loop()
        loop.create_task(self.start())
        loop.run_forever() 