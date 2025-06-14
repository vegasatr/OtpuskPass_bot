from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Создание приложения FastAPI
app = FastAPI(title="OtpuskPass Mini App")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость для получения сессии БД
def get_db():
    from database.migrations import init_db
    db = init_db()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "Добро пожаловать в OtpuskPass Mini App!"}

@app.get("/api/user/{telegram_id}")
async def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получение информации о пользователе"""
    from database.models import User
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@app.get("/api/apartments/{city}")
async def get_apartments(city: str, db: Session = Depends(get_db)):
    """Получение списка квартир в городе"""
    from database.models import Apartment
    apartments = db.query(Apartment).filter(Apartment.city == city).all()
    return apartments

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 