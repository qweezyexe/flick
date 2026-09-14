"""Генерирует flick.ico рядом с main.py.
Требует Pillow: pip install Pillow
"""
import sys
from io import BytesIO
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QBuffer, QIODevice


def run():
    app = QApplication.instance() or QApplication(sys.argv)

    import main as flick

    pm = flick._logo_pixmap(256)
    img = pm.toImage()

    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    if not img.save(buf, "PNG"):
        print("Не удалось сериализовать QImage в PNG")
        sys.exit(1)
    buf.close()
    png_bytes = bytes(buf.data())

    try:
        from PIL import Image
    except ImportError:
        print("Установи Pillow: pip install Pillow")
        sys.exit(1)

    pil = Image.open(BytesIO(png_bytes)).convert("RGBA")
    out = Path(__file__).resolve().parent / "flick.ico"

    pil.save(
        out,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64),
               (48, 48), (32, 32), (16, 16)],
    )
    print(f"OK: {out}")


if __name__ == "__main__":
    run()
