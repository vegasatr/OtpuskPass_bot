from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from .models import Base

# Загрузка переменных окружения
load_dotenv()

# Получение URL для подключения к БД напрямую из .env
DATABASE_URL = os.getenv('DATABASE_URL')

# Проверка, что DATABASE_URL установлен
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен в файле .env")

def init_db():
    """Инициализация базы данных"""
    # Создание движка SQLAlchemy
    engine = create_engine(DATABASE_URL)
    
    # Создание всех таблиц
    Base.metadata.create_all(engine)
    
    # Создание сессии
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return SessionLocal()

if __name__ == "__main__":
    # Создание базы данных при запуске скрипта
    init_db()
    print("База данных успешно инициализирована!") 