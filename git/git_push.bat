@echo off
setlocal enabledelayedexpansion

REM Скрипт автоматического пуша проекта на Git с увеличением версии
REM Использование: git\git_push.bat [описание изменений]

REM Устанавливаем кодировку для корректного отображения русских символов
chcp 65001 >nul

echo 🚀 Запуск автоматического пуша проекта OtpuskPass Bot

REM Проверяем, что мы в корне проекта
if not exist "version.txt" (
    echo ❌ Файл version.txt не найден. Запустите скрипт из корня проекта.
    exit /b 1
)

REM Читаем текущую версию
set /p CURRENT_VERSION=<version.txt
set CURRENT_VERSION=!CURRENT_VERSION: =!
echo 📋 Текущая версия: !CURRENT_VERSION!

REM Парсим версию (формат x.y.z)
for /f "tokens=1-3 delims=." %%a in ("!CURRENT_VERSION!") do (
    set "major=%%a"
    set "minor=%%b"
    set "patch=%%c"
)

REM Увеличиваем patch версию
set /a new_patch=!patch!+1
set NEW_VERSION=!major!.!minor!.!new_patch!

echo 🆙 Новая версия: !NEW_VERSION!

REM Обновляем version.txt
echo !NEW_VERSION!> version.txt
echo ✅ Версия обновлена в version.txt

REM Генерируем описание изменений
if "%~1"=="" (
    call :generate_smart_description
    set "DESCRIPTION=!SMART_DESC!"
) else (
    set "DESCRIPTION=%~1"
)

echo 📝 Описание: !DESCRIPTION!

REM Создаем имя ветки
set BRANCH_NAME=v!NEW_VERSION!
echo 🌿 Создание ветки: !BRANCH_NAME!

REM Проверяем статус Git
git status >nul 2>&1
if errorlevel 1 (
    echo ❌ Это не Git репозиторий или Git не инициализирован
    exit /b 1
)

REM Проверяем, есть ли удаленный репозиторий
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo ❌ Удаленный репозиторий origin не настроен
    echo 💡 Добавьте удаленный репозиторий: git remote add origin ^<URL^>
    exit /b 1
)

REM Добавляем все изменения
echo 📦 Добавление файлов в Git...
git add .

REM Проверяем, есть ли изменения для коммита
git diff --cached --quiet >nul 2>&1
if errorlevel 1 (
    echo ✅ Найдены изменения для коммита
) else (
    echo ⚠️  Нет изменений для коммита
)

REM Создаем коммит
set COMMIT_MESSAGE=v!NEW_VERSION!: !DESCRIPTION!
echo 💾 Создание коммита: !COMMIT_MESSAGE!
git commit -m "!COMMIT_MESSAGE!" 2>nul || echo ⚠️  Коммит пропущен (нет изменений)

REM Проверяем, существует ли ветка
git show-ref --verify --quiet refs/heads/!BRANCH_NAME! >nul 2>&1
if errorlevel 1 (
    echo 🌿 Создание новой ветки !BRANCH_NAME!
    git checkout -b !BRANCH_NAME!
) else (
    echo ⚠️  Ветка !BRANCH_NAME! уже существует, переключаемся на неё
    git checkout !BRANCH_NAME!
)

REM Пушим изменения
echo 🚀 Отправка изменений на GitHub...
git push -u origin !BRANCH_NAME!

REM Создаем тег для версии
set TAG_NAME=release-v!NEW_VERSION!
echo 🏷️  Создание тега !TAG_NAME!
git tag -a !TAG_NAME! -m "Release v!NEW_VERSION!: !DESCRIPTION!"
git push origin !TAG_NAME!

echo.
echo 🎉 Успешно! Проект опубликован:
echo    • Версия: !NEW_VERSION!
echo    • Ветка: !BRANCH_NAME!
echo    • Тег: !TAG_NAME!
echo    • Описание: !DESCRIPTION!

REM Получаем URL репозитория
for /f "usebackq tokens=*" %%i in (`git remote get-url origin 2^>nul`) do set "REPO_URL=%%i"
set "REPO_URL=!REPO_URL:.git=!"

echo.
echo 🔗 Ссылки:
echo    • Ветка: !REPO_URL!/tree/!BRANCH_NAME!
echo    • Релиз: !REPO_URL!/releases/tag/!TAG_NAME!

echo.
echo ✨ Готово!
exit /b 0

REM Функция генерации описания изменений
:generate_smart_description
set SMART_DESC=

REM Анализируем измененные файлы
git diff --cached --name-only > %TEMP%\git_changes.txt 2>nul

REM Проверяем основные категории изменений
findstr /i "src\\main.py" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Внесены ключевые изменения в основной модуль бота, улучшена логика запуска и обработки команд. Добавлено расширенное логирование отслеживания активности."
    goto :desc_done
)

findstr /i "src\\web" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Обновления в веб-приложении Mini App управления подпиской и профилем. Добавлены новые API-эндпоинты и улучшена обработка запросов."
    goto :desc_done
)

findstr /i "src\\database" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Внесены изменения в структуру базы данных и миграции. Обновлены модели поддержки новых функций подписки и бронирования."
    goto :desc_done
)

findstr /i "src\\services\\ton_payment.py" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Усовершенствована логика обработки платежей в TON. Обновлены механизмы расчета суммы и создания транзакций."
    goto :desc_done
)

findstr /i "src\\services\\gemini_service.py" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Обновлена интеграция с Gemini API точной обработки запросов пользователей и формирования ответов."
    goto :desc_done
)

findstr /i "src\\utils" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Добавлены или обновлены вспомогательные функции различных операций бота, включая генерацию кодов и форматирование данных."
    goto :desc_done
)

findstr /i "requirements.txt" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Обновлен список зависимостей проекта. Добавлены новые библиотеки или обновлены версии существующих."
    goto :desc_done
)

findstr /i "README.md" %TEMP%\git_changes.txt >nul 2>&1
if not errorlevel 1 (
    set "SMART_DESC=Обновлена основная документация проекта README.md с актуальной информацией о функциях и установке."
    goto :desc_done
)

REM Подсчитываем количество измененных файлов
git diff --cached --name-status 2>nul | find /c "A" > %TEMP%\added_count.txt
git diff --cached --name-status 2>nul | find /c "M" > %TEMP%\modified_count.txt
set /p ADDED_COUNT=<%TEMP%\added_count.txt
set /p MODIFIED_COUNT=<%TEMP%\modified_count.txt
del %TEMP%\added_count.txt %TEMP%\modified_count.txt >nul 2>&1

if !ADDED_COUNT! gtr 3 (
    set "SMART_DESC=Добавлены новые компоненты и модули, расширяющие функциональность бота. Проведена значительная доработка системы."
    goto :desc_done
)

if !MODIFIED_COUNT! gtr 5 (
    set "SMART_DESC=Масштабные обновления кодовой базы с улучшениями производительности и надежности. Проведен рефакторинг и оптимизация."
    goto :desc_done
)

REM По умолчанию
set "SMART_DESC=Выполнены точечные исправления и оптимизации повышения стабильности работы системы. Устранены мелкие ошибки."

:desc_done
del %TEMP%\git_changes.txt >nul 2>&1
exit /b

