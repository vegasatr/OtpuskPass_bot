import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from dotenv import load_dotenv
import asyncio
from telegram import Bot
from telegram.error import TelegramError

# Добавляем корневую директорию проекта в sys.path, чтобы импорты из src работали
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from src.database.models import Apartment, UserRole #
from src.database.migrations import init_db #

# Загрузка переменных окружения
load_dotenv(os.path.join(project_root, '.env')) # Указываем путь к .env

# Получаем токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("\033[91m❌ ОШИБКА: Токен BOT_TOKEN не найден в .env файле. Невозможно загрузить видео в Telegram.\033[0m")
    sys.exit(1)

# Инициализируем Telegram Bot
bot = Bot(token=BOT_TOKEN)

# Директория с файлами для добавления квартир (относительно корневой папки проекта)
ADD_PROPERTY_BASE_DIR = os.path.join(project_root, 'add_property')

# Список городов из ТЗ для создания подпапок
CITIES = ["phuket", "bangkok", "pattaya", "samui", "phi_phi", "krabi"]

# Необходимые файлы шаблонов описаний
REQUIRED_DESCRIPTION_FILES = ["description.txt", "features.txt", "nearby_attractions.txt"]
REQUIRED_VIDEO_FILE_LOCAL = "video.mp4" # Имя локального видеофайла
# Новые файлы для метаданных
REQUIRED_METADATA_FILES = ["metadata.txt"]

def create_city_folders_and_templates():
    """Создает папки городов и пустые файлы шаблонов, если их нет."""
    print(f"\033[94m--- Проверка и создание папок и шаблонов в {ADD_PROPERTY_BASE_DIR} ---\033[0m")
    for city in CITIES:
        city_path = os.path.join(ADD_PROPERTY_BASE_DIR, city)
        os.makedirs(city_path, exist_ok=True)
        print(f"  \033[92m✔ Папка: {city_path}\033[0m")

        for filename in REQUIRED_DESCRIPTION_FILES + REQUIRED_METADATA_FILES:
            file_path = os.path.join(city_path, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    if filename == "description.txt":
                        f.write(f"Подробное описание квартиры в {city.capitalize()}.\n")
                    elif filename == "features.txt":
                        f.write("Кондиционер, стиральная машина, оборудованная кухня, Wi-Fi, телевизор.\n")
                    elif filename == "nearby_attractions.txt":
                        f.write("Рядом с пляжем, кафе, магазины, достопримечательности.\n")
                    elif filename == "metadata.txt":
                        f.write(f"address=Базовая квартира в {city.capitalize()} (адрес)\n")
                        f.write("area_sqm=50.0\n")
                        f.write("num_bedrooms=1\n")
                print(f"    \033[93m⚠ Создан шаблон: {filename}\033[0m")
        
        # Проверяем наличие локального видеофайла (для напоминания)
        video_local_path = os.path.join(city_path, REQUIRED_VIDEO_FILE_LOCAL)
        if not os.path.exists(video_local_path):
            print(f"    \033[93m⚠ ВНИМАНИЕ: Локальный видеофайл {REQUIRED_VIDEO_FILE_LOCAL} отсутствует в {city_path}. Его нужно добавить вручную.\033[0m")
    print("\033[94m--- Проверка папок и шаблонов завершена ---\033[0m")

async def upload_video_to_telegram(video_path: str) -> str | None:
    """Загружает видеофайл в Telegram и возвращает file_id."""
    print(f"  \033[96m📤 Загрузка видеофайла '{os.path.basename(video_path)}' в Telegram...\033[0m")
    try:
        with open(video_path, 'rb') as video_file:
            TEST_CHAT_ID = os.getenv('TELEGRAM_TEST_CHAT_ID')
            if not TEST_CHAT_ID:
                print("\033[91m  ❌ ОШИБКА: TELEGRAM_TEST_CHAT_ID не указан в .env для загрузки видео. Пожалуйста, добавьте свой chat_id.\033[0m")
                print("\033[91m  (Вы можете узнать свой chat_id, написав @userinfobot в Telegram)\033[0m")
                return None

            message = await bot.send_video(chat_id=TEST_CHAT_ID, video=video_file, disable_notification=True)
            video_file_id = message.video.file_id
            print(f"  \033[92m✅ Видео успешно загружено. file_id: {video_file_id}\033[0m")
            return video_file_id
    except TelegramError as e:
        print(f"\033[91m  ❌ Ошибка Telegram API при загрузке видео: {e}\033[0m")
        return None
    except Exception as e:
        print(f"\033[91m  ❌ Непредвиденная ошибка при загрузке видео: {e}\033[0m")
        return None

async def process_city_apartment(city: str) -> bool:
    """
    Обрабатывает файлы для одного города и пытается добавить квартиру в БД.
    Возвращает True в случае успешного добавления, False иначе.
    """
    print(f"\n\033[94m--- Обработка города: {city.capitalize()} ---\033[0m")

    db_session = init_db() #
    try:
        city_path = os.path.join(ADD_PROPERTY_BASE_DIR, city)
        
        description_path = os.path.join(city_path, "description.txt")
        features_path = os.path.join(city_path, "features.txt")
        nearby_attractions_path = os.path.join(city_path, "nearby_attractions.txt")
        metadata_path = os.path.join(city_path, "metadata.txt") # Путь к файлу метаданных
        video_local_path = os.path.join(city_path, REQUIRED_VIDEO_FILE_LOCAL)

        # Проверка наличия всех необходимых файлов
        missing_files = []
        if not os.path.exists(description_path): missing_files.append("description.txt")
        if not os.path.exists(features_path): missing_files.append("features.txt")
        if not os.path.exists(nearby_attractions_path): missing_files.append("nearby_attractions.txt")
        if not os.path.exists(metadata_path): missing_files.append("metadata.txt")
        if not os.path.exists(video_local_path): missing_files.append(REQUIRED_VIDEO_FILE_LOCAL)

        if missing_files:
            print(f"\033[91m  ❌ ОШИБКА: Отсутствуют необходимые файлы для '{city.capitalize()}': {', '.join(missing_files)}.\033[0m")
            print("\033[91m  Пожалуйста, убедитесь, что все файлы шаблонов заполнены, а видеофайл присутствует.\033[0m")
            return False
        
        # Читаем контент
        with open(description_path, 'r', encoding='utf-8') as f:
            description = f.read().strip()
        with open(features_path, 'r', encoding='utf-8') as f:
            features = f.read().strip()
        with open(nearby_attractions_path, 'r', encoding='utf-8') as f:
            nearby_attractions = f.read().strip()
        
        # Читаем метаданные
        metadata = {}
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                metadata[key] = value
        
        # Извлекаем данные из метаданных, проверяем их
        address = metadata.get('address')
        area_sqm = float(metadata.get('area_sqm')) if metadata.get('area_sqm') else None
        num_bedrooms = int(metadata.get('num_bedrooms')) if metadata.get('num_bedrooms') else None

        if not address or not area_sqm or not num_bedrooms:
            print(f"\033[91m  ❌ ОШИБКА: Файл 'metadata.txt' для '{city.capitalize()}' не заполнен или содержит некорректные данные (address, area_sqm, num_bedrooms).\033[0m")
            return False

        # Проверка, что шаблоны не пустые (или не содержат стандартный текст "Заполните...")
        if not description or "Заполните это описание" in description:
            print(f"\033[91m  ❌ ОШИБКА: Файл 'description.txt' для '{city.capitalize()}' не заполнен или содержит шаблонный текст.\033[0m")
            return False
        if not features or "Кондиционер, стиральная машина, оборудованная кухня" in features: # Проверяем на шаблонный текст
            print(f"\033[91m  ❌ ОШИБКА: Файл 'features.txt' для '{city.capitalize()}' не заполнен или содержит шаблонный текст.\033[0m")
            return False
        if not nearby_attractions or "Рядом с пляжем, кафе, магазины" in nearby_attractions: # Проверяем на шаблонный текст
            print(f"\033[91m  ❌ ОШИБКА: Файл 'nearby_attractions.txt' для '{city.capitalize()}' не заполнен или содержит шаблонный текст.\033[0m")
            return False
        
        # --- Логика загрузки видео и получения file_id ---
        apartment_video_id = None
        existing_apartment = db_session.query(Apartment).filter(
            Apartment.city == city,
            Apartment.apartment_type == "Base" #
        ).first()

        if existing_apartment:
            # Если квартира уже есть, используем её video_url (предполагаем, что это file_id)
            print(f"  \033[92m✔ Базовая квартира для города '{city.capitalize()}' уже существует в базе данных (ID: {existing_apartment.id}).\033[0m")
            if existing_apartment.video_url and existing_apartment.video_url.startswith('BAAD'): # Простая проверка, что это похоже на Telegram file_id
                apartment_video_id = existing_apartment.video_url
                print(f"  \033[96m♻️ Используется существующий file_id: {apartment_video_id}\033[0m")
            else:
                print(f"  \033[93m⚠️ Существующая квартира не имеет file_id Telegram или он невалиден. Попытка перезагрузить видео.\033[0m")
                # Если file_id нет или он невалидный, пробуем загрузить снова
                apartment_video_id = await upload_video_to_telegram(video_local_path)
                if not apartment_video_id:
                    print(f"\033[91m  ❌ ОШИБКА: Не удалось получить file_id для '{city.capitalize()}'. Пропуск.\033[0m")
                    return False
            
            # Если квартира уже существует, просто обновляем её данные, кроме video_url
            # Если video_url был обновлен (перезагружен), то он тоже обновится
            existing_apartment.address = address
            existing_apartment.description = description
            existing_apartment.features = features
            existing_apartment.nearby_attractions = nearby_attractions
            existing_apartment.status = "available"
            existing_apartment.area_sqm = area_sqm
            existing_apartment.num_bedrooms = num_bedrooms
            existing_apartment.video_url = apartment_video_id # Обновляем file_id

            db_session.add(existing_apartment) # Добавляем для обновления
            db_session.commit()
            db_session.refresh(existing_apartment)
            print(f"  \033[92m✅ Базовая квартира для '{city.capitalize()}' успешно обновлена в базе данных. ID: {existing_apartment.id}\033[0m")
            return True

        else:
            # Если квартиры нет, загружаем видео и создаем новую запись
            apartment_video_id = await upload_video_to_telegram(video_local_path)
            if not apartment_video_id:
                print(f"\033[91m  ❌ ОШИБКА: Не удалось получить file_id для '{city.capitalize()}'. Пропуск.\033[0m")
                return False

            new_apartment = Apartment(
                city=city,
                address=address,
                description=description,
                video_url=apartment_video_id, # Сохраняем file_id
                features=features,
                nearby_attractions=nearby_attractions,
                status="available",
                area_sqm=area_sqm,
                num_bedrooms=num_bedrooms,
                apartment_type="Base", #
                owner_id=None # Базовая квартира не имеет owner_id
            )

            db_session.add(new_apartment)
            db_session.commit()
            db_session.refresh(new_apartment)
            print(f"  \033[92m✅ Базовая квартира для '{city.capitalize()}' успешно добавлена в базу данных. ID: {new_apartment.id}\033[0m")
            return True
    except TelegramError as e:
        print(f"\033[91m  ❌ Ошибка Telegram API при обработке квартиры для '{city.capitalize()}': {e}\033[0m")
        db_session.rollback()
        return False
    except IntegrityError as e:
        db_session.rollback()
        print(f"\033[91m  ❌ ОШИБКА БД при добавлении/обновлении квартиры для '{city.capitalize()}': {e}\033[0m")
        return False
    except Exception as e:
        db_session.rollback()
        print(f"\033[91m  ❌ Непредвиденная ошибка при обработке квартиры для '{city.capitalize()}': {e}\033[0m")
        return False
    finally:
        db_session.close()

async def main_async():
    """Асинхронная основная функция для обработки всех городов."""
    create_city_folders_and_templates() # Сначала создаем папки и шаблоны

    print("\n\033[94m--- Запуск автоматического добавления/обновления базовых квартир ---\033[0m")
    overall_success = True
    for city in CITIES:
        if not await process_city_apartment(city): # Важно: вызываем асинхронную функцию
            overall_success = False
    
    if overall_success:
        print("\n\033[92m🎉 Все доступные базовые квартиры успешно обработаны.\033[0m")
        sys.exit(0)
    else:
        print("\n\033[91m⚠️ ВНИМАНИЕ: Некоторые базовые квартиры не были добавлены/обновлены из-за ошибок. Проверьте сообщения выше.\033[0m")
        sys.exit(1)

if __name__ == '__main__':
    # Эта часть будет вызываться из bash-скрипта
    # Для асинхронных функций нужна точка входа asyncio.run
    asyncio.run(main_async()) 