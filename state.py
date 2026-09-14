"""Состояние редактора, элементы, константы."""

from dataclasses import dataclass, field

from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import QRect, QSize


APP_NAME = "Flick"
APP_TAGLINE = "Скриншоты и аннотации"
APP_VERSION = "1.5.0"
APP_AUTHOR = "qweezy.exe"

SINGLE_INSTANCE_KEY = "Flick-SingleInstance-qweezy-2026"

PEN_KINDS = {"pen", "marker", "highlighter", "neon"}

BRUSHES = {
    "pen":         {"alpha": 255, "scale": 1.0},
    "marker":      {"alpha": 150, "scale": 2.5},
    "highlighter": {"alpha": 70,  "scale": 5.0},
    "neon":        {"alpha": 255, "scale": 1.2, "glow": True},
}

NUMBER_SIZE_MIN = 8
NUMBER_SIZE_MAX = 72
NUMBER_SIZE_STEP = 2
NUMBER_VALUE_MIN = 1
NUMBER_VALUE_MAX = 999


@dataclass
class Item:
    kind: str
    color: str
    width: int
    points: list = field(default_factory=list)
    text: str = ""
    font_size: int = 18


@dataclass
class EditorState:
    tool: str = "select"
    color: str = "#a855f7"
    width: int = 3
    number_size: int = 18
    number_counter: int = 1


def pretty_hotkey(hk: str) -> str:
    parts = []
    for p in hk.split("+"):
        p = p.strip()
        if not p:
            continue
        name = p.strip("<>").upper()
        if name == "CTRL":
            name = "Ctrl"
        elif name == "SHIFT":
            name = "Shift"
        elif name == "ALT":
            name = "Alt"
        elif name == "CMD":
            name = "Win"
        elif name == "PRINT_SCREEN":
            name = "PrtSc"
        elif name == "PAGE_UP":
            name = "PgUp"
        elif name == "PAGE_DOWN":
            name = "PgDn"
        parts.append(name)
    return " + ".join(parts)


def compute_text_rect(item: Item) -> QRect:
    f = QFont()
    f.setPointSize(item.font_size)
    f.setBold(True)
    fm = QFontMetrics(f)
    w = fm.horizontalAdvance(item.text)
    h = fm.height()
    return QRect(item.points[0], QSize(w, h))


def number_radius(item: Item) -> int:
    return item.font_size + 4
