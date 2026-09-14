@echo off
chcp 65001 >nul
title Flick — build by qweezy.exe
echo ============================================
echo   Flick — сборка  by qweezy.exe
echo ============================================
echo.

if exist ".venv\Scripts\activate.bat" (
    echo [1/5] Активируем .venv
    call .venv\Scripts\activate.bat
) else (
    echo [1/5] Создаём .venv...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

echo [2/5] Устанавливаем зависимости...
python -m pip install -q --upgrade pip
python -m pip install -q PySide6 mss pynput pyinstaller Pillow

echo [3/5] Генерируем иконку flick.ico...
if not exist "flick.ico" (
    python make_icon.py
)

echo [4/5] Собираем приложение (--onedir)...
pyinstaller --noconfirm --clean ^
    --onedir ^
    --windowed ^
    --name Flick ^
    --icon flick.ico ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --collect-submodules pynput ^
    --exclude-module tkinter ^
    --exclude-module PySide6.QtWebEngineCore ^
    --exclude-module PySide6.QtQuick ^
    --exclude-module PySide6.Qt3DCore ^
    main.py

echo.
echo ============================================
echo [5/5] Готово!
echo.
echo Программа: dist\Flick\Flick.exe
echo Установщик: открой Flick.iss в Inno Setup и нажми F9
echo Результат:  installer\Flick-Setup-1.0.0-by-qweezy.exe
echo ============================================
pause
