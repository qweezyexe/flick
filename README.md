<!--
  Flick — README
  Если хочешь, замени ссылки на скриншоты и бейдж лицензии.
-->

<div align="center">

# ⚡ Flick

**Скриншоты на лету.**

Лёгкий скриншотер для Windows с оверлеем, редактором и поддержкой игр.

[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)](https://github.com/qweezyexe/flick)
[![Version](https://img.shields.io/badge/version-1.2.0-7C3AED)](https://github.com/qweezyexe/flick/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-6D28D9)](LICENSE)

[🌐 Сайт](https://flick-screens.netlify.app) · [⬇️ Скачать](https://github.com/qweezyexe/flick/releases) · [🐛 Сообщить о баге](https://github.com/qweezyexe/flick/issues) · [💜 Автор](https://github.com/qweezyexe)

</div>

---

## 🎬 Что это

**Flick** — минималистичный скриншотер для Windows в тёмно-фиолетовой теме.  
Один хоткей — и экран затемняется, ты выделяешь область, рисуешь стрелку, ставишь цифру, а картинка уже в буфере.

Работает даже в играх — через **DXGI Desktop Duplication API**, тот же механизм, что у OBS и Windows Game Bar.

> **Посмотреть вживую:** [flick-screens.netlify.app](https://flick-screens.netlify.app)

---

## 📖 Оглавление

- [✨ Возможности](#-возможности)
- [🚀 Установка](#-установка)
- [⌨️ Горячие клавиши](#️-горячие-клавиши)
- [🛠️ Сборка из исходников](#️-сборка-из-исходников)
- [📁 Структура проекта](#-структура-проекта)
- [🧰 Технологии](#-технологии)
- [❓ FAQ](#-faq)
- [🤝 Contributing](#-contributing)
- [📄 Лицензия](#-лицензия)

---

## ✨ Возможности

| | |
|---|---|
| 🎮 **Работает в играх** | Захват через DXGI Desktop Duplication. DirectX 11/12, Vulkan, Borderless Fullscreen |
| ⌨️ **3 глобальных хоткея** | Оверлей, полный экран в буфер, полный экран в файл — каждый на своё сочетание |
| 🖱 **Выделение области** | Плавное затемнение, фиолетовая рамка, угловые маркеры |
| ✏️ **4 кисти** | Ручка, маркер, текстовыделитель, неоновая со свечением |
| ▢ **Фигуры** | Прямоугольник и стрелка |
| 🔢 **Умная нумерация** | Клик → 1 → 2 → 3. Колесо над цифрой меняет значение |
| 📝 **Текст** | Поле ввода прямо на холсте |
| 🖐 **Drag & Drop** | Цифры и текст перетаскиваются мышью |
| 🎨 **Цвета** | 8 предустановленных + свой через системный диалог |
| 📏 **Толщина** | Слайдер или колесо мыши |
| 💾 **Буфер и файл** | `Ctrl+C` / `Enter` в буфер, `Ctrl+S` в PNG / JPEG |
| ↩️ **Отмена** | `Ctrl+Z` и `Delete` для объекта под курсором |
| 🖥 **Мультимониторы** | Оверлей — все экраны, F8/F9 — основной монитор |
| 🌙 **Тёмная тема** | Скруглённые углы, плавные анимации, аккуратные иконки |
| 🚀 **Single instance** | При повторном запуске показывает «уже запущен» и не плодит трей |

---

## 🚀 Установка

### Готовый установщик (рекомендуется)

1. Скачай архив **`Flick-v1.2.0-Windows.zip`** с [сайта](https://flick-screens.netlify.app) или из [Releases](https://github.com/qweezyexe/flick/releases)
2. Распакуй архив (правый клик → «Извлечь всё»)
3. Запусти **`Flick-Setup-1.2.0-by-qweezy.exe`**
4. Следуй мастеру установки
5. Нажми **F7**

> Python и библиотеки не нужны — всё внутри.

### Из исходников

```bash
git clone https://github.com/qweezyexe/flick.git
cd flick

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
