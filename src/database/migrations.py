from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from models import Base

# Загрузка переменных окружения
load_dotenv()

# Получение параметров подключения к БД
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Создание URL для подключения к БД
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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