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
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller Pillow

echo "[3/4] Генерируем flick.ico..."
if [ ! -f flick.ico ]; then
    python3 make_icon.py
fi

echo "[4/4] Собираем бинарник..."
pyinstaller \
    --noconfirm \
    --clean \
    --onefile \
    --windowed \
    --name Flick.exe \
    --icon flick.ico \
    --distpath dist \
    --workpath build \
    --specpath . \
    main.py

echo
echo "============================================"
echo "Готово: dist/Flick.exe"
echo "============================================"