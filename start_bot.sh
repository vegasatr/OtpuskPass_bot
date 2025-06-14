#!/bin/bash

set -e

echo "🤖 Запуск OtpuskPass бота в tmux..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Проверяем, что tmux установлен
if ! command -v tmux &> /dev/null; then
    error "tmux не установлен. Установите: sudo apt install tmux"
    exit 1
fi

# Переменные
SESSION_NAME="otpusk_bot"
PROJECT_DIR="/mnt/c/Users/vegas/.cursor/OtpuskPass_bot"

# Функция проверки и создания виртуального окружения
setup_virtual_environment() {
    log "🐍 Проверяем виртуальное окружение..."
    
    cd "$PROJECT_DIR"
    
    # Проверяем, существует ли виртуальное окружение
    if [ ! -d "venv" ]; then
        warning "⚠️ Виртуальное окружение не найдено - создаём новое..."
        
        # Проверяем наличие python3
        if ! command -v python3 &> /dev/null; then
            error "Python3 не установлен! Установите: sudo apt install python3 python3-venv python3-pip"
            exit 1
        fi
        
        # Создаём виртуальное окружение
        log "🔧 Создаём виртуальное окружение..."
        python3 -m venv venv
        
        if [ ! -d "venv" ]; then
            error "Не удалось создать виртуальное окружение!"
            exit 1
        fi
        
        log "✅ Виртуальное окружение создано"
    else
        log "✅ Виртуальное окружение найдено"
    fi
    
    # Проверяем основные зависимости
    log "🔍 Проверяем установленные зависимости..."
    
    local missing_packages=()
    local venv_python="venv/bin/python3"
    
    # Проверяем каждую критическую зависимость
    if ! $venv_python -c "import telegram" 2>/dev/null; then
        missing_packages+=("python-telegram-bot")
    fi
    
    if ! $venv_python -c "import sqlalchemy" 2>/dev/null; then
        missing_packages+=("sqlalchemy")
    fi
    
    if ! $venv_python -c "import requests" 2>/dev/null; then
        missing_packages+=("requests")
    fi
    
    # Если есть недостающие пакеты - устанавливаем все из requirements.txt
    if [ ${#missing_packages[@]} -gt 0 ]; then
        warning "⚠️ Обнаружены недостающие зависимости: ${missing_packages[*]}"
        
        # Проверяем наличие requirements.txt
        if [ -f "requirements.txt" ]; then
            log "📦 Устанавливаем зависимости из requirements.txt..."
            
            # Обновляем pip
            $venv_python -m pip install --upgrade pip
            
            # Устанавливаем зависимости
            $venv_python -m pip install -r requirements.txt
            
            # Проверяем установку ещё раз
            log "🔍 Проверяем установку зависимостей..."
            local still_missing=()
            
            for package in "${missing_packages[@]}"; do
                if ! $venv_python -c "import $package" 2>/dev/null; then
                    still_missing+=("$package")
                fi
            done
            
            if [ ${#still_missing[@]} -gt 0 ]; then
                error "❌ Не удалось установить: ${still_missing[*]}"
                error "Попробуйте установить вручную: pip install ${still_missing[*]}"
                exit 1
            fi
            
            log "✅ Все зависимости успешно установлены"
        else
            error "❌ Файл requirements.txt не найден!"
            error "Создайте файл requirements.txt или установите зависимости вручную"
            exit 1
        fi
    else
        log "✅ Все необходимые зависимости установлены"
    fi
    
    log "🎉 Виртуальное окружение готово к работе"
}

# Функция остановки всех процессов
stop_all_processes() {
    log "💀 ПОЛНАЯ ОЧИСТКА всех процессов и сессий..."
    
    # Получаем PID текущего скрипта для исключения
    local current_script_pid=$$
    log "🛡️ Защищаем текущий скрипт (PID: $current_script_pid)"
    
    # 1. УБИВАЕМ ВСЕ ПРОЦЕССЫ main.py
    warning "💀 Убиваем ВСЕ процессы main.py..."
    local main_pids=$(pgrep -f "python.*main\\.py" 2>/dev/null || true)
    if [ -n "$main_pids" ]; then
        warning "🔍 Найдены процессы main.py: $main_pids"
        for pid in $main_pids; do
            if [ "$pid" != "$current_script_pid" ]; then
                warning "💀 Убиваем main.py процесс: $pid"
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
    fi
    
    # 2. УБИВАЕМ ВСЕ TMUX СЕССИИ
    warning "🧹 Убиваем все tmux сессии..."
    tmux kill-session -t $SESSION_NAME 2>/dev/null || true
    
    # 3. УБИВАЕМ ОСТАВШИЕСЯ PYTHON ПРОЦЕССЫ С TELEGRAM
    warning "💀 Убиваем процессы telegram..."
    local telegram_pids=$(pgrep -f "telegram" 2>/dev/null || true)
    if [ -n "$telegram_pids" ]; then
        for pid in $telegram_pids; do
            if [ "$pid" != "$current_script_pid" ]; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
    fi
    
    sleep 3
    log "✅ Полная очистка завершена"
}

# Функция очистки webhook
clear_webhook() {
    log "🧹 Принудительная очистка Telegram webhook..."
    
    cd "$PROJECT_DIR"
    
    # Активируем виртуальное окружение
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Многократная попытка очистки webhook
    local attempts=0
    local max_attempts=5
    
    while [ $attempts -lt $max_attempts ]; do
        attempts=$((attempts + 1))
        log "🔄 Попытка очистки webhook #$attempts из $max_attempts..."
        
        if python3 src/bot/clear_webhook.py 2>/dev/null; then
            log "✅ Webhook успешно очищен!"
            return 0
        else
            warning "❌ Попытка #$attempts не удалась"
            if [ $attempts -lt $max_attempts ]; then
                sleep 3
            fi
        fi
    done
    
    warning "⚠️ Не удалось очистить webhook после $max_attempts попыток"
    warning "🔄 Продолжаем запуск бота..."
}

# Проверяем и настраиваем виртуальное окружение
setup_virtual_environment

# Основная остановка
log "🔄 УМНАЯ ОЧИСТКА перед запуском..."
stop_all_processes
clear_webhook
log "⏳ Ждём 5 секунд для полной очистки..."
sleep 5

echo "📁 Переходим в директорию проекта: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Создаем новую tmux сессию
log "🔧 Создаем новую tmux сессию: $SESSION_NAME"
tmux new-session -d -s $SESSION_NAME

# Окно 1: Основной бот
log "🚀 Запускаем основной бот..."
tmux rename-window -t $SESSION_NAME:0 'main-bot'
tmux send-keys -t $SESSION_NAME:0 "cd '$PROJECT_DIR'" C-m
tmux send-keys -t $SESSION_NAME:0 "source venv/bin/activate" C-m
tmux send-keys -t $SESSION_NAME:0 "PYTHONPATH=$PROJECT_DIR python3 src/main.py" C-m

# Окно 2: Мониторинг логов
log "📋 Создаем окно мониторинга..."
tmux new-window -t $SESSION_NAME -n 'logs'
tmux send-keys -t $SESSION_NAME:1 "cd '$PROJECT_DIR'" C-m
tmux send-keys -t $SESSION_NAME:1 "tail -f bot.log" C-m

# Окно 3: Терминал для команд
log "⌨️  Создаем рабочий терминал..."
tmux new-window -t $SESSION_NAME -n 'terminal'
tmux send-keys -t $SESSION_NAME:2 "cd '$PROJECT_DIR'" C-m
tmux send-keys -t $SESSION_NAME:2 "source venv/bin/activate" C-m

echo ""
echo "✅ Бот запущен в tmux сессии: $SESSION_NAME"
echo ""
echo "📖 Управление:"
echo "   tmux attach -t $SESSION_NAME     # Подключиться к сессии"
echo "   Ctrl+B, 0                       # Основной бот"
echo "   Ctrl+B, 1                       # Логи"
echo "   Ctrl+B, 2                       # Терминал"
echo "   Ctrl+B, d                       # Отсоединиться от сессии"
echo "   tmux kill-session -t $SESSION_NAME  # Остановить все"
echo ""
echo "🔗 Сессия готова для подключения:"
echo "   tmux attach -t $SESSION_NAME"

# Проверяем, запущен ли скрипт в автоматическом режиме (без TTY)
if [ -t 0 ]; then
    # Есть TTY - интерактивный режим
    echo "🔗 Подключаемся к сессии..."
    sleep 2
    tmux attach -t $SESSION_NAME
else
    # Нет TTY - автоматический режим
    echo "🤖 Автоматический режим - пропускаем подключение к tmux"
    echo "✅ Бот запущен успешно!"
fi 