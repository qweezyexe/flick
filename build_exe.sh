#!/usr/bin/env bash
set -e

echo "============================================"
echo "  Flick — сборка standalone"
echo "============================================"

if [ -d ".venv" ]; then
    echo "[1/4] Активируем .venv"
    source .venv/bin/activate
else
    echo "[1/4] .venv не найден — используем текущее окружение"
fi

echo "[2/4] Устанавливаем зависимости..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller Pillow

echo "[3/4] Генерируем flick.ico..."
[ -f flick.ico ] || python make_icon.py

echo "[4/4] Собираем бинарник..."
pyinstaller --noconfirm --clean \
    --onefile \
    --windowed \
    --name Flick \
    --icon flick.ico \
    main.py

echo
echo "============================================"
echo "Готово! Файл: dist/Flick"
echo "============================================"
