#!/bin/bash

# Скрипт для автоматического добавления/обновления базовых квартир в базу данных
# Проходит по всем городам, проверяет файлы, загружает видео и добавляет/обновляет записи в БД.

set -e # Остановка при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Путь к корневой директории проекта
PROJECT_ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")

# Путь к Python-скрипту логики
PYTHON_SCRIPT="$PROJECT_ROOT/add_property/add_base_apartment_logic.py"

echo -e "${BLUE}--- Запуск процесса добавления/обновления базовых квартир ---${NC}"

# 1. Проверяем наличие Python-скрипта логики
echo -e "${YELLOW}🐍 Проверяем наличие Python-скрипта логики: ${PYTHON_SCRIPT}${NC}"
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}❌ ОШИБКА: Python-скрипт логики '$PYTHON_SCRIPT' не найден.${NC}"
    echo -e "${RED}Пожалуйста, создайте файл '$PYTHON_SCRIPT' со всей логикой.${NC}"
    exit 1
fi

# 2. Активируем виртуальное окружение
echo -e "${YELLOW}🐍 Активируем виртуальное окружение...${NC}"
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo -e "${GREEN}✅ Виртуальное окружение активировано.${NC}"
else
    echo -e "${RED}❌ ОШИБКА: Виртуальное окружение 'venv' не найдено в корне проекта.${NC}"
    echo -e "${RED}Пожалуйста, создайте его: 'python3 -m venv venv' и установите зависимости: 'pip install -r requirements.txt'.${NC}"
    exit 1
fi

# 3. Вызываем Python-скрипт для запуска всей логики
echo -e "${BLUE}⚙️ Запуск автоматической обработки квартир...${NC}"
if ! python3 "$PYTHON_SCRIPT"; then
    echo -e "${RED}🔥 Произошла ошибка при обработке квартир. Проверьте логи выше.${NC}"
    deactivate
    exit 1
fi

deactivate # Деактивируем виртуальное окружение
echo -e "${BLUE}--- Процесс завершен ---${NC}" 