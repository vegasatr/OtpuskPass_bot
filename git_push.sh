#!/bin/bash

# Скрипт автоматического пуша проекта на Git с увеличением версии
# Использование: ./scripts/git_push.sh [описание изменений]

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск автоматического пуша проекта OtpuskPass Bot${NC}" # Изменено название проекта

# Проверяем, что мы в корне проекта
if [ ! -f "version.txt" ]; then
    echo -e "${RED}❌ Файл version.txt не найден. Запустите скрипт из корня проекта.${NC}"
    exit 1
fi

# Читаем текущую версию
CURRENT_VERSION=$(cat version.txt | tr -d '\n\r')
echo -e "${YELLOW}📋 Текущая версия: ${CURRENT_VERSION}${NC}"

# Увеличиваем версию (предполагаем формат x.y.z)
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
major=${version_parts[0]}
minor=${version_parts[1]}
patch=${version_parts[2]}

# Увеличиваем patch версию
new_patch=$((patch + 1))
NEW_VERSION="${major}.${minor}.${new_patch}"

echo -e "${GREEN}🆙 Новая версия: ${NEW_VERSION}${NC}"

# Обновляем version.txt
echo "$NEW_VERSION" > version.txt
echo -e "${GREEN}✅ Версия обновлена в version.txt${NC}"

# Функция генерации подробного описания изменений
generate_smart_description() {
    # Анализируем измененные файлы
    local changes=$(git diff --cached --name-only)
    local added_files=$(git diff --cached --name-status | grep "^A" | wc -l)
    local modified_files=$(git diff --cached --name-status | grep "^M" | wc -l)
    local deleted_files=$(git diff --cached --name-status | grep "^D" | wc -l)
    
    # Проверяем основные категории изменений и создаем подробное описание для OtpuskPass_bot
    if echo "$changes" | grep -q "src/main.py"; then # Основной файл бота
        echo "Внесены ключевые изменения в основной модуль бота, улучшена логика запуска и обработки команд. Добавлено расширенное логирование для отслеживания активности."
    elif echo "$changes" | grep -q "src/web/"; then # Web-приложение Mini App
        echo "Обновления в веб-приложении (Mini App) для управления подпиской и профилем. Добавлены новые API-эндпоинты и улучшена обработка запросов."
    elif echo "$changes" | grep -q "src/database/"; then # База данных (models, migrations)
        echo "Внесены изменения в структуру базы данных и миграции. Обновлены модели для поддержки новых функций подписки и бронирования."
    elif echo "$changes" | grep -q "src/services/ton_payment.py"; then # TON платежи
        echo "Усовершенствована логика обработки платежей в TON. Обновлены механизмы расчета суммы и создания транзакций."
    elif echo "$changes" | grep -q "src/services/gemini_service.py"; then # Gemini API
        echo "Обновлена интеграция с Gemini API для более точной обработки запросов пользователей и формирования ответов."
    elif echo "$changes" | grep -q "src/utils/"; then # Вспомогательные функции
        echo "Добавлены или обновлены вспомогательные функции для различных операций бота, включая генерацию кодов и форматирование данных."
    elif echo "$changes" | grep -q "requirements.txt"; then # Зависимости
        echo "Обновлен список зависимостей проекта. Добавлены новые библиотеки или обновлены версии существующих."
    elif echo "$changes" | grep -q "README\.md"; then # Документация README
        echo "Обновлена основная документация проекта (README.md) с актуальной информацией о функциях и установке."
    elif [ "$added_files" -gt 3 ]; then # Если много новых файлов, но специфические условия не сработали
        echo "Добавлены новые компоненты и модули, расширяющие функциональность бота. Проведена значительная доработка системы."
    elif [ "$modified_files" -gt 5 ]; then # Если много измененных файлов
        echo "Масштабные обновления кодовой базы с улучшениями производительности и надежности. Проведен рефакторинг и оптимизация."
    else
        echo "Выполнены точечные исправления и оптимизации для повышения стабильности работы системы. Устранены мелкие ошибки."
    fi
}

# Генерируем описание изменений
if [ -z "$1" ]; then
    # Умное автоматическое описание на основе анализа изменений
    DESCRIPTION=$(generate_smart_description)
else
    DESCRIPTION="$1"
fi

echo -e "${YELLOW}📝 Описание: ${DESCRIPTION}${NC}"

# Создаем имя ветки
BRANCH_NAME="v${NEW_VERSION}"
echo -e "${BLUE}🌿 Создание ветки: ${BRANCH_NAME}${NC}"

# Проверяем статус Git
if ! git status &>/dev/null; then
    echo -e "${RED}❌ Это не Git репозиторий или Git не инициализирован${NC}"
    exit 1
fi

# Проверяем, есть ли удаленный репозиторий
if ! git remote get-url origin &>/dev/null; then
    echo -e "${RED}❌ Удаленный репозиторий origin не настроен${NC}"
    echo -e "${YELLOW}💡 Добавьте удаленный репозиторий: git remote add origin <URL>${NC}"
    exit 1
fi

# Добавляем все изменения
echo -e "${BLUE}📦 Добавление файлов в Git...${NC}"
git add .

# Проверяем, есть ли изменения для коммита
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  Нет изменений для коммита${NC}"
else
    echo -e "${GREEN}✅ Найдены изменения для коммита${NC}"
fi

# Создаем коммит
COMMIT_MESSAGE="v${NEW_VERSION}: ${DESCRIPTION}"
echo -e "${BLUE}💾 Создание коммита: ${COMMIT_MESSAGE}${NC}"
git commit -m "$COMMIT_MESSAGE" || echo -e "${YELLOW}⚠️  Коммит пропущен (нет изменений)${NC}"

# Создаем и переключаемся на новую ветку
if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
    echo -e "${YELLOW}⚠️  Ветка ${BRANCH_NAME} уже существует, переключаемся на неё${NC}"
    git checkout $BRANCH_NAME
else
    echo -e "${BLUE}🌿 Создание новой ветки ${BRANCH_NAME}${NC}"
    git checkout -b $BRANCH_NAME
fi

# Пушим изменения
echo -e "${BLUE}🚀 Отправка изменений на GitHub...${NC}"
git push -u origin $BRANCH_NAME

# Создаем тег для версии (избегаем конфликта имен с веткой)
TAG_NAME="release-v${NEW_VERSION}"
echo -e "${BLUE}🏷️  Создание тега ${TAG_NAME}${NC}"
git tag -a $TAG_NAME -m "Release v${NEW_VERSION}: ${DESCRIPTION}"
git push origin $TAG_NAME

echo -e "${GREEN}🎉 Успешно! Проект опубликован:${NC}"
echo -e "${GREEN}    • Версия: ${NEW_VERSION}${NC}"
echo -e "${GREEN}    • Ветка: ${BRANCH_NAME}${NC}"
echo -e "${GREEN}    • Тег: ${TAG_NAME}${NC}"
echo -e "${GREEN}    • Описание: ${DESCRIPTION}${NC}"

echo -e "${BLUE}🔗 Ссылки:${NC}"
echo -e "${BLUE}    • Ветка: $(git remote get-url origin | sed 's/\.git$//')/tree/${BRANCH_NAME}${NC}"
echo -e "${BLUE}    • Релиз: $(git remote get-url origin | sed 's/\.git$//')/releases/tag/${TAG_NAME}${NC}"

echo -e "${GREEN}✨ Готово!${NC}"