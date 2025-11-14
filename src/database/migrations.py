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

def get_database_url(db_url=None):
    """Преобразует DATABASE_URL в формат, понятный SQLAlchemy
    
    Args:
        db_url: URL базы данных. Если не указан, используется DATABASE_URL из окружения
    
    Returns:
        Преобразованный URL для SQLAlchemy
    """
    url = db_url or DATABASE_URL
    # Если URL начинается с mysql://, заменяем на mysql+pymysql:// для работы с pymysql
    if url and url.startswith('mysql://'):
        return url.replace('mysql://', 'mysql+pymysql://', 1)
    return url

def init_db():
    """Инициализация базы данных"""
    # Получаем правильный URL для SQLAlchemy
    db_url = get_database_url()
    # Создание движка SQLAlchemy
    engine = create_engine(db_url)
    
    # Создание всех таблиц
    Base.metadata.create_all(engine)
    
    # Создание сессии
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return SessionLocal()

if __name__ == "__main__":
    # Создание базы данных при запуске скрипта
    init_db()
    print("База данных успешно инициализирована!") 