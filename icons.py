"""Flick — иконки приложения.

Модуль самодостаточный: рисует иконку в памяти через QPainter.
Не импортирует main.py, app.py и ничего из проекта,
поэтому его можно безопасно подключать откуда угодно.
"""

from PySide6.QtCore import Qt, QSize, QRectF, QPointF
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QLinearGradient,
    QBrush, QPen, QPainterPath, QFont, QPolygonF,
)


# ---------- цвета бренда ----------
C_LIGHT = QColor("#c084fc")   # светло-фиолетовый
C_MAIN  = QColor("#a855f7")   # основной
C_DARK  = QColor("#6d28d9")   # тёмный


def _draw_logo(size: int = 256) -> QPixmap:
    """Рисует круглый логотип с буквой F и звёздочкой."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)

    rect = QRectF(2, 2, size - 4, size - 4)

    # --- градиентный круг ---
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setColorAt(0.0, C_LIGHT)
    grad.setColorAt(0.5, C_MAIN)
    grad.setColorAt(1.0, C_DARK)

    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(rect)

    # --- лёгкий блик сверху ---
    shine = QLinearGradient(0, 0, 0, size)
    shine.setColorAt(0.0, QColor(255, 255, 255, 60))
    shine.setColorAt(0.5, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(shine))
    p.drawEllipse(rect.adjusted(size * 0.08, size * 0.06,
                                -size * 0.08, -size * 0.55))

    # --- буква F ---
    font = QFont()
    font.setFamily("Segoe UI")
    font.setWeight(QFont.Black)
    font.setPixelSize(int(size * 0.62))
    p.setFont(font)
    p.setPen(QColor(255, 255, 255, 255))

    f_rect = QRectF(0, -size * 0.02, size, size)
    p.drawText(f_rect, Qt.AlignCenter, "F")

    # --- звёздочка в правом верхнем углу ---
    sx, sy = size * 0.78, size * 0.22
    sr = size * 0.14
    k = 0.30

    star = QPolygonF([
        QPointF(sx,           sy - sr),
        QPointF(sx + sr * k,  sy - sr * k),
        QPointF(sx + sr,      sy),
        QPointF(sx + sr * k,  sy + sr * k),
        QPointF(sx,           sy + sr),
        QPointF(sx - sr * k,  sy + sr * k),
        QPointF(sx - sr,      sy),
        QPointF(sx - sr * k,  sy - sr * k),
    ])

    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 255))
    p.drawPolygon(star)

    p.end()
    return pm


def make_icon(size: int = 256) -> QIcon:
    """Создаёт QIcon с несколькими размерами (16…256).

    Возвращает готовую иконку для окна, трея и .exe.
    Может использоваться как `make_icon()` без аргументов.
    """
    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_draw_logo(s))
    return icon


def app_icon() -> QIcon:
    """Иконка приложения по умолчанию.

    Если рядом с проектом лежит flick.ico — используется он.
    Иначе рисуется встроенная иконка. Никогда не возвращает None,
    поэтому Qt-окна и трей не падают.
    """
    from pathlib import Path

    ico = Path(__file__).with_name("flick.ico")
    if ico.exists():
        icon = QIcon(str(ico))
        if not icon.isNull():
            return icon

    return make_icon()


# --- самопроверка: python icons.py ---
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    pm = _draw_logo(256)

    out = "flick_preview.png"
    pm.save(out, "PNG")
    print(f"[OK] Превью сохранено: {out}")

    # заодно запишем и .ico, если стоит Pillow
    try:
        from PIL import Image
        img = Image.open(out)
        img.save("flick.ico", format="ICO",
                 sizes=[(16, 16), (32, 32), (48, 48),
                        (64, 64), (128, 128), (256, 256)])
        print("[OK] Иконка сохранена: flick.ico")
    except ImportError:
        print("[i] Pillow не установлен — .ico не создан. "
              "Можно поставить: pip install Pillow")