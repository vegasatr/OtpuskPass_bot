#!/usr/bin/env python3
"""
Скрипт запуска для Railway
Инициализирует БД и запускает бота и веб-приложение
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Добавляем src в PYTHONPATH для корректных импортов
project_root = Path(__file__).parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Инициализация базы данных"""
    try:
        logger.info("Инициализация базы данных...")
        from src.database.migrations import init_db
        db = init_db()
        db.close()
        logger.info("База данных успешно инициализирована!")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}", exc_info=True)
        return False

def main():
    """Основная функция запуска"""
    # Проверяем наличие необходимых переменных окружения
    required_vars = ['BOT_TOKEN', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Инициализируем БД
    if not init_database():
        logger.warning("Не удалось инициализировать БД, продолжаем запуск...")
    
    # Определяем, какой процесс запускать
    # Railway может запускать разные процессы через Procfile
    process_type = os.getenv('RAILWAY_SERVICE_NAME', 'web')
    
    if process_type == 'bot' or 'BOT' in process_type.upper():
        # Запускаем бота
        logger.info("Запуск Telegram бота...")
        from src.main import main as bot_main
        import asyncio
        asyncio.run(bot_main())
    elif process_type == 'webapp' or 'WEB' in process_type.upper():
        # Запускаем веб-приложение
        logger.info("Запуск веб-приложения...")
        port = os.getenv('PORT', '8000')
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'src.web.main:app',
            '--host', '0.0.0.0',
            '--port', port
        ])
    else:
        # По умолчанию запускаем оба процесса через multiprocessing
        logger.info("Запуск бота и веб-приложения...")
        import multiprocessing
        import signal
        
        def run_bot():
            from src.main import main as bot_main
            import asyncio
            asyncio.run(bot_main())
        
        def run_webapp():
            port = os.getenv('PORT', '8000')
            subprocess.run([
                sys.executable, '-m', 'uvicorn',
                'src.web.main:app',
                '--host', '0.0.0.0',
                '--port', port
            ])
        
        # Создаем процессы
        bot_process = multiprocessing.Process(target=run_bot, name='bot')
        webapp_process = multiprocessing.Process(target=run_webapp, name='webapp')
        
        # Обработчик сигналов для корректного завершения
        def signal_handler(signum, frame):
            logger.info("Получен сигнал завершения, останавливаем процессы...")
            bot_process.terminate()
            webapp_process.terminate()
            bot_process.join(timeout=10)
            webapp_process.join(timeout=10)
            if bot_process.is_alive() or webapp_process.is_alive():
                logger.warning("Процессы не завершились, принудительное завершение...")
                bot_process.kill()
                webapp_process.kill()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Запускаем процессы
        bot_process.start()
        webapp_process.start()
        
        # Ждем завершения
        try:
            bot_process.join()
            webapp_process.join()
        except KeyboardInterrupt:
            signal_handler(None, None)

if __name__ == '__main__':
    main()

