"""
Flick — скриншоты и аннотации
by qweezy.exe

Точка входа.
"""

import sys
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

from app import App


def main():
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = App()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
