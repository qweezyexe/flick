<div align="center">

# Flick

**Скриншоты и аннотации на лету.**

_by qweezy.exe_

[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.6+-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/license-MIT-a855f7)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-9d95b0)]()

</div>

---

## Возможности

|  |  |
|---|---|
| **Глобальный хоткей** | По умолчанию **F7**, меняется в настройках |
| **Выделение области** | Плавное затемнение, фиолетовая рамка, угловые маркеры |
| **4 кисти** | Ручка, маркер, текстовыделитель, неоновая |
| **Фигуры** | Прямоугольник и стрелка |
| **Умная нумерация** | Клик — 1, 2, 3… Колесо над цифрой меняет значение |
| **Текст** | Клик — и поле ввода прямо на холсте |
| **Drag & Drop** | Цифры и текст перетаскиваются мышью |
| **Цвета** | 8 предустановленных + свой через системный диалог |
| **Толщина** | Слайдер или колесо мыши |
| **Копировать / Сохранить** | Ctrl+C / Enter в буфер, Ctrl+S в PNG/JPEG |
| **Отмена** | Ctrl+Z и Delete для объекта под курсором |
| **Тёмно-фиолетовая тема** | Скруглённые углы, мягкие анимации |
| **Мультимониторы** | Захват всего виртуального экрана |

## Установка

### Из исходников

```bash
git clone https://github.com/qweezy-exe/flick.git
cd flick
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

### Готовый .exe

1. Скачай `Flick-Setup-1.0.0-by-qweezy.exe` из Releases.
2. Запусти мастер установки.
3. Программа свернётся в трей, нажми **F7**.

## Горячие клавиши

### Глобальные

| Клавиша | Действие |
|---|---|
| **F7** | Сделать скриншот (настраивается) |

### В оверлее

| Клавиша | Действие |
|---|---|
| **ЛКМ** по цифре / тексту | Перетащить объект |
| **Колесо** над цифрой | Изменить её значение (1 -> 2 -> 3) |
| **Колесо** + инструмент «Цифра» | Размер следующей цифры |
| **Колесо** в любом другом месте | Толщина кисти |
| **Enter** / **Ctrl+C** | Скопировать в буфер и закрыть |
| **Ctrl+S** | Сохранить файл |
| **Ctrl+Z** | Отменить последний элемент |
| **Delete** | Удалить цифру/текст под курсором |
| **Esc** | Закрыть оверлей |
| **ПКМ** | Отменить текущий штрих |

## Сборка .exe

### Windows

```bat
build.bat
```

### Linux / macOS

```bash
chmod +x build_exe.sh
./build_exe.sh
```

### Установщик (Inno Setup)

1. Установи [Inno Setup](https://jrsoftware.org/isdl.php).
2. Открой `Flick.iss` в Inno Setup Compiler.
3. **Build -> Compile** (F9).
4. Готовый установщик: `installer/Flick-Setup-1.0.0-by-qweezy.exe`.

## Конфиг

Настройки хранятся в:

- **Windows**: `%USERPROFILE%\.config\flick\config.json`
- **Linux / macOS**: `~/.config/flick/config.json`

```json
{
  "hotkey": "<f7>",
  "color": "#a855f7",
  "thickness": 3,
  "number_size": 18,
  "save_dir": ""
}
```

## Стек

- **PySide6** — UI (Qt 6)
- **mss** — быстрый захват экрана
- **pynput** — глобальные хоткеи
- **Pillow** — генерация .ico

## Лицензия

[MIT](LICENSE)

<div align="center">

Сделано с 💜 **by qweezy.exe**

</div>
