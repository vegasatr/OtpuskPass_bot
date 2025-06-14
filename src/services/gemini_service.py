import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional

# Загрузка переменных окружения
load_dotenv()

# Настройка API ключа Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = self.model.start_chat(history=[])

    async def get_response(self, user_input: str) -> Optional[str]:
        """Получение ответа от Gemini на запрос пользователя"""
        try:
            # Добавление контекста о сервисе
            context = """
            Вы - помощник сервиса OtpuskPass, который предоставляет услуги краткосрочной аренды квартир бизнес-класса в Таиланде по подписочной модели.
            Стоимость подписки: 3 000 руб. в месяц.
            Минимальное количество ночей для бронирования: 7.
            Оплата производится в криптовалюте TON.
            """
            
            full_prompt = f"{context}\n\nВопрос пользователя: {user_input}"
            
            response = await self.chat.send_message(full_prompt)
            return response.text
            
        except Exception as e:
            print(f"Ошибка при получении ответа от Gemini: {str(e)}")
            return None

    async def process_user_query(self, user_input: str) -> str:
        """Обработка запроса пользователя"""
        response = await self.get_response(user_input)
        
        if response:
            return response
        else:
            return "Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или обратитесь в поддержку." 