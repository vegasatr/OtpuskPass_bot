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

# Основная остановка
log "🔄 УМНАЯ ОЧИСТКА перед запуском..."
stop_all_processes
clear_webhook
log "⏳ Ждём 10 секунд для полной очистки..."
sleep 10

echo "📁 Переходим в директорию проекта: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Создаем новую tmux сессию
log "🔧 Создаем новую tmux сессию: $SESSION_NAME"
tmux new-session -d -s $SESSION_NAME

# Окно 1: Основной бот
log "🚀 Запускаем основной бот..."
tmux rename-window -t $SESSION_NAME:0 'main-bot'
tmux send-keys -t $SESSION_NAME:0 "cd '$PROJECT_DIR'" C-m
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