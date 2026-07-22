@echo off
%SystemRoot%\System32\chcp.com 65001 >nul
title Установка и запуск Skyrim LLM Voice Mod
color 0A

echo ===================================================
echo   Привет! Добро пожаловать в установщик мода
echo   Skyrim Local LLM Voice.
echo ===================================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Python не найден в системе.
    echo Пожалуйста, скачайте и установите Python 3.10 или 3.11 с сайта python.org
    echo При установке обязательно поставьте галочку "Add Python to PATH"!
    pause
    exit /b
)

echo [OK] Python найден.
echo.

cd server

:: Проверка и создание виртуального окружения
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ИНФО] Создание виртуального окружения venv. Это займет пару минут...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение.
        pause
        exit /b
    )
    echo [OK] Виртуальное окружение создано.
) ELSE (
    echo [OK] Виртуальное окружение найдено.
)

echo.
echo [ИНФО] Активация окружения и проверка библиотек...
call venv\Scripts\activate.bat

:: Обновление pip и установка зависимостей
python -m pip install --upgrade pip >nul 2>&1
echo [ИНФО] Установка необходимых библиотек (может занять время при первом запуске)...
pip install -r requirements.txt

echo.
echo ===================================================
echo   Всё готово! Запуск меню...
echo ===================================================
timeout /t 2 >nul

:: Запуск консольного приложения
python src\launcher.py

pause
