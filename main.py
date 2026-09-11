"""
Flick — скриншоты и аннотации
by qweezy.exe
"""

import sys
import math
import json
from dataclasses import dataclass, field
from typing import List
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLabel, QFrame, QLineEdit, QPushButton,
    QMessageBox, QColorDialog, QSlider, QFileDialog,
    QGraphicsOpacityEffect, QScrollArea,
)
from PySide6.QtGui import (
    QIcon, QAction, QFont, QFontMetrics, QPainter, QPen, QColor,
    QPixmap, QImage, QGuiApplication, QPainterPath,
    QLinearGradient, QRadialGradient, QBrush, QDesktopServices,
)
from PySide6.QtCore import (
    Qt, QObject, Signal, Slot, QRect, QPoint, QPointF, QSize,
    QStandardPaths, QPropertyAnimation, QEasingCurve, QRectF, QUrl,
    QTimer,
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket

import mss
from pynput import keyboard


# ═══════════════════════════════════════════════════════════════════
#  КОНФИГ
# ═══════════════════════════════════════════════════════════════════

CONFIG_PATH = Path.home() / ".config" / "flick" / "config.json"

DEFAULT_HOTKEYS = {
    "screenshot":       "<f7>",
    "fullscreen_copy":  "<f8>",
    "fullscreen_save":  "<f9>",
}

HOTKEY_LABELS = {
    "screenshot":       "Сделать скриншот (открыть оверлей)",
    "fullscreen_copy":  "Полный экран → буфер",
    "fullscreen_save":  "Полный экран → файл",
}

HOTKEY_ORDER = ["screenshot", "fullscreen_copy", "fullscreen_save"]

DEFAULTS = {
    "hotkeys": dict(DEFAULT_HOTKEYS),
    "color": "#a855f7",
    "thickness": 3,
    "number_size": 18,
    "save_dir": "",
}


def config_load():
    cfg = {
        "hotkeys": dict(DEFAULT_HOTKEYS),
        "color": DEFAULTS["color"],
        "thickness": DEFAULTS["thickness"],
        "number_size": DEFAULTS["number_size"],
        "save_dir": DEFAULTS["save_dir"],
    }
    if not CONFIG_PATH.exists():
        return cfg
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return cfg

    if "hotkey" in data and "hotkeys" not in data:
        data["hotkeys"] = dict(DEFAULT_HOTKEYS)
        data["hotkeys"]["screenshot"] = data.pop("hotkey")
    data.pop("hotkey", None)

    if isinstance(data.get("hotkeys"), dict):
        cfg["hotkeys"] = {**DEFAULT_HOTKEYS, **data["hotkeys"]}
    for k in ("color", "thickness", "number_size", "save_dir"):
        if k in data:
            cfg[k] = data[k]
    return cfg


def config_save(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def default_save_dir() -> str:
    loc = QStandardPaths.writableLocation(
        QStandardPaths.PicturesLocation)
    return loc or str(Path.home())


def resolve_save_dir(cfg) -> str:
    d = (cfg.get("save_dir") or "").strip()
    if d and Path(d).is_dir():
        return d
    return default_save_dir()


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


# ═══════════════════════════════════════════════════════════════════
#  ТЕМА / БРЕНДИНГ
# ═══════════════════════════════════════════════════════════════════

APP_NAME = "Flick"
APP_TAGLINE = "Скриншоты и аннотации"
APP_VERSION = "1.1.0"
APP_AUTHOR = "qweezy.exe"
APP_AUTHOR_URL = ""

SINGLE_INSTANCE_KEY = "Flick-SingleInstance-qweezy-2026"

ACCENT = "#a855f7"
ACCENT_HOVER = "#c084fc"
ACCENT_PRESSED = "#7c3aed"
ACCENT_SOFT = "#2a1f3d"

BG_DEEP = "#0f0b16"
BG = "#16111f"
SURFACE = "#241d32"
SURFACE_2 = "#2d2438"
BORDER = "#3d3450"
BORDER_2 = "#4a3f5f"
TEXT = "#ece7f5"
TEXT_MUTED = "#9d95b0"


TOOLBAR_QSS = f"""
QFrame#Toolbar {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QPushButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 0;
}}
QPushButton:hover {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
}}
QPushButton:checked {{
    background: {ACCENT};
    border: 1px solid {ACCENT_HOVER};
}}
QPushButton:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton#Primary {{
    background: {ACCENT};
    color: white;
    padding: 6px 14px;
    font-weight: bold;
    border-radius: 8px;
}}
QPushButton#Primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#Primary:pressed {{ background: {ACCENT_PRESSED}; }}
QLabel {{ color: {TEXT_MUTED}; }}
QSlider::groove:horizontal {{
    height: 4px; background: {BORDER}; border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 14px; background: {ACCENT_HOVER}; border-radius: 7px;
    margin: -6px 0;
}}
QSlider::handle:horizontal:hover {{ background: #d8b4fe; }}
QFrame#Sep {{ color: {BORDER}; background: {BORDER}; max-width: 1px; }}
"""


SETTINGS_QSS = f"""
QWidget#Root {{
    background: transparent;
    color: {TEXT};
    font-family: "Segoe UI Variable Display", "Segoe UI",
                 "SF Pro Display", Inter, sans-serif;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(168, 85, 247, 0.45);
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(168, 85, 247, 0.75);
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QFrame#TitleBar {{
    background: transparent;
}}
QLabel#TitleBarLogo {{
    background: transparent;
}}
QLabel#TitleBarText {{
    color: {TEXT};
    font-size: 13px;
    font-weight: 600;
    background: transparent;
}}
QLabel#TitleBarAuthor {{
    color: {TEXT_MUTED};
    font-size: 11px;
    background: transparent;
}}
QPushButton#CloseBtn {{
    background: transparent;
    border: none;
    color: {TEXT_MUTED};
    font-size: 18px;
    border-radius: 8px;
    padding: 0;
    font-weight: 400;
}}
QPushButton#CloseBtn:hover {{
    background: #ff5f57;
    color: #ffffff;
}}
QPushButton#CloseBtn:pressed {{
    background: #d94b43;
}}

QFrame#Card {{
    background: rgba(26, 20, 40, 0.72);
    border: 1px solid {BORDER};
    border-radius: 18px;
}}
QFrame#HeroCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #c084fc, stop:0.5 #a855f7, stop:1 #6d28d9);
    border: none;
    border-radius: 20px;
}}

QLabel#SectionLabel {{
    color: {TEXT};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    background: transparent;
}}
QLabel#Hint {{
    color: {TEXT_MUTED};
    font-size: 12px;
    background: transparent;
}}
QLabel#CurrentKey {{
    color: #d8b4fe;
    font-size: 13px;
    font-weight: 600;
    background: transparent;
    padding: 10px 14px;
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 10px;
    background: rgba(168, 85, 247, 0.08);
}}
QLabel#Version {{
    color: {TEXT_MUTED};
    font-size: 11px;
    background: transparent;
    letter-spacing: 0.04em;
}}
QLabel#HotkeyLabel {{
    color: {TEXT};
    font-size: 13px;
    font-weight: 600;
    background: transparent;
}}

QLabel#HeroName {{
    color: #ffffff;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: transparent;
}}
QLabel#HeroTag {{
    color: rgba(255,255,255,0.88);
    font-size: 13px;
    background: transparent;
}}
QLabel#HeroAuthor {{
    color: rgba(255,255,255,0.72);
    font-size: 11px;
    background: transparent;
    letter-spacing: 0.04em;
}}
QLabel#HeroBadge {{
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 999px;
    padding: 5px 14px;
    letter-spacing: 0.03em;
}}

QLineEdit {{
    background: rgba(15, 11, 22, 0.75);
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 12px 16px;
    color: {TEXT};
    font-size: 14px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    font-family: 'JetBrains Mono', 'Cascadia Code', Consolas, monospace;
    letter-spacing: 0.02em;
}}
QLineEdit:hover {{
    border: 1px solid {BORDER_2};
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
    background: rgba(15, 11, 22, 0.95);
}}
QLineEdit[recording="true"] {{
    border: 2px solid {ACCENT_HOVER};
    background: rgba(168, 85, 247, 0.15);
    color: #ffffff;
}}

QPushButton {{
    background: rgba(45, 36, 56, 0.7);
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 11px 20px;
    color: {TEXT};
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background: rgba(61, 52, 80, 0.9);
    border: 1px solid {BORDER_2};
}}
QPushButton:pressed {{
    background: {ACCENT_SOFT};
}}
QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #c084fc, stop:0.5 #a855f7, stop:1 #7c3aed);
    border: none;
    color: #ffffff;
    font-weight: 700;
    padding: 12px 26px;
}}
QPushButton#Primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d8b4fe, stop:0.5 #c084fc, stop:1 #a855f7);
}}
QPushButton#Primary:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton#Browse {{
    background: rgba(45, 36, 56, 0.7);
    border: 1px solid {BORDER};
    padding: 11px 20px;
    min-width: 90px;
    font-weight: 600;
}}
QPushButton#Browse:hover {{
    background: rgba(168, 85, 247, 0.15);
    border: 1px solid {ACCENT};
    color: {ACCENT_HOVER};
}}
QPushButton#ClearHotkey {{
    background: rgba(45, 36, 56, 0.7);
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0;
    font-size: 20px;
    font-weight: 400;
    color: {TEXT_MUTED};
    min-width: 46px;
    max-width: 46px;
}}
QPushButton#ClearHotkey:hover {{
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
}}
QPushButton#ClearHotkey:pressed {{
    background: rgba(239, 68, 68, 0.3);
}}
"""


TRAY_MENU_QSS = f"""
QMenu {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 22px 8px 14px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {ACCENT};
    color: white;
}}
QMenu::separator {{
    height: 1px; background: {BORDER}; margin: 4px 8px;
}}
"""


# ═══════════════════════════════════════════════════════════════════
#  ЗАХВАТ ЭКРАНА
# ═══════════════════════════════════════════════════════════════════

_dxcam_instance = None


def _get_dxcam():
    global _dxcam_instance
    if _dxcam_instance is not None:
        return _dxcam_instance if _dxcam_instance is not False else None
    try:
        import dxcam
        cam = dxcam.create(output_color="BGRA")
        _dxcam_instance = cam if cam is not None else False
    except Exception as e:
        print("dxcam unavailable:", e)
        _dxcam_instance = False
    return _dxcam_instance if _dxcam_instance is not False else None


def capture_fullscreen() -> QPixmap:
    """Захват экрана. Сначала mss (надёжно), потом dxcam (для игр)."""
    # 1) mss — работает везде
    try:
        with mss.mss() as sct:
            mon = sct.monitors[0]
            shot = sct.grab(mon)
            img = QImage(
                shot.raw, shot.width, shot.height,
                shot.width * 4, QImage.Format_RGB32,
            ).copy()
            return QPixmap.fromImage(img)
    except Exception as e:
        print("mss error:", e)

    # 2) dxcam — фолбэк для игр
    cam = _get_dxcam()
    if cam is not None:
        try:
            frame = cam.grab()
            if frame is None:
                import time
                time.sleep(0.05)
                frame = cam.grab()
            if frame is not None:
                h, w, _ = frame.shape
                img = QImage(
                    frame.data, w, h, w * 4,
                    QImage.Format_ARGB32,
                ).copy()
                return QPixmap.fromImage(img)
        except Exception as e:
            print("dxcam grab error:", e)

    return None


# ═══════════════════════════════════════════════════════════════════
#  ИКОНКИ
# ═══════════════════════════════════════════════════════════════════

def _draw_icon(p: QPainter, kind: str, color: QColor):
    stroke = 2.0
    p.setPen(QPen(color, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)

    if kind == "select":
        path = QPainterPath()
        path.moveTo(5, 3)
        path.lineTo(5, 19.5)
        path.lineTo(9.3, 14.8)
        path.lineTo(12.8, 21)
        path.lineTo(15.7, 19.6)
        path.lineTo(12.2, 13.4)
        path.lineTo(18.5, 13.4)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        p.drawPath(path)

    elif kind == "pen":
        body = QPainterPath()
        body.moveTo(3.5, 20.5)
        body.lineTo(4.5, 15.5)
        body.lineTo(15.5, 4.5)
        body.lineTo(19.5, 8.5)
        body.lineTo(8.5, 19.5)
        body.closeSubpath()
        p.drawPath(body)
        p.drawLine(QPointF(13.5, 6.5), QPointF(17.5, 10.5))

    elif kind == "marker":
        p.setPen(QPen(color, 4.2, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(6.5, 17.5), QPointF(17.5, 6.5))

    elif kind == "highlighter":
        p.setPen(QPen(color, 6.5, Qt.SolidLine, Qt.FlatCap))
        p.drawLine(QPointF(5, 17), QPointF(19, 7))

    elif kind == "neon":
        path = QPainterPath()
        path.moveTo(12, 3)
        path.quadTo(12.5, 11.5, 21, 12)
        path.quadTo(12.5, 12.5, 12, 21)
        path.quadTo(11.5, 12.5, 3, 12)
        path.quadTo(11.5, 11.5, 12, 3)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        p.drawPath(path)

    elif kind == "rect":
        p.drawRoundedRect(QRectF(4, 5, 16, 14), 2.5, 2.5)

    elif kind == "arrow":
        p.drawLine(QPointF(5, 19), QPointF(19, 5))
        head = QPainterPath()
        head.moveTo(19, 5)
        head.lineTo(11.5, 5.5)
        head.lineTo(18.5, 12.5)
        head.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        p.drawPath(head)

    elif kind == "text":
        p.setPen(QPen(color, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawLine(QPointF(5, 6.5), QPointF(19, 6.5))
        p.drawLine(QPointF(12, 6.5), QPointF(12, 19))

    elif kind == "number":
        p.setPen(QPen(color, 1.9, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        p.drawLine(QPointF(10, 10), QPointF(12.2, 8))
        p.drawLine(QPointF(12.2, 8), QPointF(12.2, 16))
        p.drawLine(QPointF(9, 16), QPointF(15.5, 16))

    elif kind == "copy":
        p.drawRoundedRect(QRectF(4, 4, 12, 12), 1.8, 1.8)
        p.drawRoundedRect(QRectF(8.5, 8.5, 12, 12), 1.8, 1.8)

    elif kind == "save":
        path = QPainterPath()
        path.moveTo(5, 4)
        path.lineTo(16, 4)
        path.lineTo(20, 8)
        path.lineTo(20, 20)
        path.lineTo(4, 20)
        path.lineTo(4, 5)
        path.closeSubpath()
        p.drawPath(path)
        p.drawRect(QRectF(7.5, 13, 9, 7))
        p.drawRect(QRectF(8.5, 4, 7, 5))

    elif kind == "folder":
        path = QPainterPath()
        path.moveTo(3, 6)
        path.lineTo(10, 6)
        path.lineTo(12, 9)
        path.lineTo(21, 9)
        path.lineTo(21, 19)
        path.lineTo(3, 19)
        path.closeSubpath()
        p.drawPath(path)

    elif kind == "settings":
        p.drawEllipse(QPointF(12, 12), 3.2, 3.2)
        p.setPen(QPen(color, 2.2, Qt.SolidLine, Qt.RoundCap))
        for i in range(8):
            a = i * math.pi / 4
            x1 = 12 + math.cos(a) * 6
            y1 = 12 + math.sin(a) * 6
            x2 = 12 + math.cos(a) * 8.8
            y2 = 12 + math.sin(a) * 8.8
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _logo_pixmap(size: int) -> QPixmap:
    dpr = 2
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)

    s = float(size)
    cx = cy = s / 2.0
    r = s / 2.0 - s * 0.03

    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0.0, QColor("#c084fc"))
    grad.setColorAt(0.45, QColor("#a855f7"))
    grad.setColorAt(1.0, QColor("#6d28d9"))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(QPointF(cx, cy), r, r)

    gloss = QRadialGradient(QPointF(cx, cy - r * 0.45),
                            r * 1.25,
                            QPointF(cx, cy - r * 0.45))
    gloss.setColorAt(0.0, QColor(255, 255, 255, 90))
    gloss.setColorAt(0.55, QColor(255, 255, 255, 0))
    gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(gloss))
    p.drawEllipse(QPointF(cx, cy), r, r)

    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(255, 255, 255, 55), max(1.0, s * 0.02)))
    p.drawEllipse(QPointF(cx, cy), r - s * 0.015, r - s * 0.015)

    f = QFont()
    f.setBold(True)
    f.setPixelSize(int(size * 0.62))
    f.setFamily("Segoe UI")
    f.setStyleHint(QFont.SansSerif)
    p.setFont(f)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, "F")

    spark_cx = s * 0.78
    spark_cy = s * 0.22
    spark_r = s * 0.12
    spark_path = QPainterPath()
    spark_path.moveTo(spark_cx, spark_cy - spark_r)
    spark_path.quadTo(spark_cx + spark_r * 0.18, spark_cy - spark_r * 0.18,
                      spark_cx + spark_r, spark_cy)
    spark_path.quadTo(spark_cx + spark_r * 0.18, spark_cy + spark_r * 0.18,
                      spark_cx, spark_cy + spark_r)
    spark_path.quadTo(spark_cx - spark_r * 0.18, spark_cy + spark_r * 0.18,
                      spark_cx - spark_r, spark_cy)
    spark_path.quadTo(spark_cx - spark_r * 0.18, spark_cy - spark_r * 0.18,
                      spark_cx, spark_cy - spark_r)
    spark_path.closeSubpath()

    spark_glow = QRadialGradient(QPointF(spark_cx, spark_cy),
                                 spark_r * 2.2,
                                 QPointF(spark_cx, spark_cy))
    spark_glow.setColorAt(0.0, QColor(255, 255, 255, 130))
    spark_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(spark_glow))
    p.drawEllipse(QPointF(spark_cx, spark_cy),
                  spark_r * 2.2, spark_r * 2.2)

    p.setBrush(QColor("#ffffff"))
    p.drawPath(spark_path)

    p.end()
    return pm


def make_icon(kind: str, color: str = TEXT, size: int = 22) -> QIcon:
    if kind == "logo":
        return QIcon(_logo_pixmap(size))
    dpr = 2
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 24.0, size / 24.0)
    _draw_icon(p, kind, QColor(color))
    p.end()
    return QIcon(pm)


def app_icon() -> QIcon:
    return make_icon("logo", ACCENT, 32)


# ═══════════════════════════════════════════════════════════════════
#  OVERLAY
# ═══════════════════════════════════════════════════════════════════

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


def _fade_in(widget, duration: int = 200):
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    widget._fade_anim = anim


class Overlay(QWidget):
    closed = Signal()

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.current_color = cfg.get("color", ACCENT)
        self.current_width = cfg.get("thickness", 3)
        self.tool = "select"
        self.number_counter = 1
        self.number_size = cfg.get("number_size", 18)

        # Обычное окно без рамки, поверх всех.
        # БЕЗ WA_TranslucentBackground — иначе на Windows клики
        # уходят в окна под оверлеем.
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)

        bg = capture_fullscreen()

        geo = QRect()
        for s in QGuiApplication.screens():
            geo = geo.united(s.geometry())
        self.setGeometry(geo)

        if bg is None:
            bg = QPixmap(geo.width() or 1920, geo.height() or 1080)
            bg.fill(QColor("#0f0b16"))
        self.bg = bg

        self.sel_start = None
        self.sel_end = None
        self.items: List[Item] = []
        self.active_item = None
        self.text_edit = None
        self.text_pos = QPoint(0, 0)
        self.toolbar = None
        self.tool_buttons = {}
        self.color_buttons = []
        self.number_btn = None

        self.hovered_item: Item = None
        self.drag_item: Item = None
        self.drag_offset = QPoint(0, 0)
        self.drag_moved = False

        # Защита от повторных mousePress во время drag
        self._mouse_pressed = False

    # ─── Фокус ───
    def showEvent(self, e):
        super().showEvent(e)
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)

    # ─── Paint ───
    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.bg)
        sel = self._selection()

        if sel:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 140))
            for r in self._outside_rects(self.rect(), sel):
                p.drawRect(r)
            p.drawPixmap(sel, self.bg, sel)

            p.setPen(QPen(QColor(ACCENT), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRect(sel)

            p.setPen(Qt.NoPen)
            p.setBrush(QColor(ACCENT))
            hs = 5
            for pt in (sel.topLeft(), sel.topRight(),
                       sel.bottomLeft(), sel.bottomRight()):
                p.drawEllipse(pt, hs, hs)
        else:
            p.fillRect(self.rect(), QColor(0, 0, 0, 120))

        for it in self.items:
            self._draw_item(p, it)

        highlight = self.drag_item or self.hovered_item
        if highlight is not None:
            if highlight.kind == "number":
                r = highlight.font_size + 4 + 4
                p.setPen(QPen(QColor("#ffffff"), 1.5, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(highlight.points[0], r, r)
            elif highlight.kind == "text":
                r = self._text_rect(highlight).adjusted(-3, -3, 3, 3)
                p.setPen(QPen(QColor("#ffffff"), 1.5, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawRect(r)

        if self.active_item:
            self._draw_item(p, self.active_item)

    def _draw_item(self, p, it: Item):
        if it.kind in PEN_KINDS:
            self._draw_stroke(p, it)
        elif it.kind == "rect" and len(it.points) >= 2:
            p.setPen(QPen(QColor(it.color), it.width, Qt.SolidLine,
                          Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRect(it.points[0], it.points[-1]).normalized())
        elif it.kind == "arrow" and len(it.points) >= 2:
            p.setPen(QPen(QColor(it.color), it.width, Qt.SolidLine,
                          Qt.RoundCap, Qt.RoundJoin))
            self._draw_arrow(p, it.points[0], it.points[-1], it.width)
        elif it.kind == "text":
            f = QFont()
            f.setPointSize(it.font_size)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor(it.color))
            fm = p.fontMetrics()
            rect = QRect(it.points[0],
                         QSize(fm.horizontalAdvance(it.text), fm.height()))
            p.drawText(rect, Qt.AlignLeft | Qt.AlignTop, it.text)
        elif it.kind == "number":
            self._draw_number(p, it)

    def _draw_number(self, p, it: Item):
        radius = it.font_size + 4
        center = it.points[0]
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(it.color))
        p.drawEllipse(center, radius, radius)
        f = QFont()
        f.setPointSize(it.font_size)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#ffffff"))
        r = QRect(center.x() - radius, center.y() - radius,
                  radius * 2, radius * 2)
        p.drawText(r, Qt.AlignCenter, it.text)

    def _draw_stroke(self, p, it: Item):
        cfg = BRUSHES.get(it.kind, BRUSHES["pen"])
        if cfg.get("glow"):
            for mult, alpha in ((3.0, 60), (2.0, 120), (1.0, 255)):
                c = QColor(it.color)
                c.setAlpha(alpha)
                p.setPen(QPen(c,
                              max(1, int(it.width * cfg["scale"] * mult)),
                              Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                for i in range(1, len(it.points)):
                    p.drawLine(it.points[i - 1], it.points[i])
        else:
            c = QColor(it.color)
            c.setAlpha(cfg["alpha"])
            cap = Qt.FlatCap if it.kind == "highlighter" else Qt.RoundCap
            w = max(1, int(it.width * cfg["scale"]))
            p.setPen(QPen(c, w, Qt.SolidLine, cap, Qt.RoundJoin))
            for i in range(1, len(it.points)):
                p.drawLine(it.points[i - 1], it.points[i])

    def _draw_arrow(self, p, a, b, width):
        p.drawLine(a, b)
        angle = math.atan2(b.y() - a.y(), b.x() - a.x())
        size = max(10, width * 4)
        for da in (math.radians(150), -math.radians(150)):
            x = b.x() + size * math.cos(angle + da)
            y = b.y() + size * math.sin(angle + da)
            p.drawLine(b, QPoint(int(x), int(y)))

    def _selection(self):
        if self.sel_start and self.sel_end:
            return QRect(self.sel_start, self.sel_end).normalized()
        return None

    def _outside_rects(self, full, sel):
        return [
            QRect(full.left(), full.top(),
                  full.width(), sel.top() - full.top()),
            QRect(full.left(), sel.bottom() + 1,
                  full.width(), full.bottom() - sel.bottom()),
            QRect(full.left(), sel.top(),
                  sel.left() - full.left(), sel.height()),
            QRect(sel.right() + 1, sel.top(),
                  full.right() - sel.right(), sel.height()),
        ]

    def _text_rect(self, it: Item) -> QRect:
        f = QFont()
        f.setPointSize(it.font_size)
        f.setBold(True)
        fm = QFontMetrics(f)
        w = fm.horizontalAdvance(it.text)
        h = fm.height()
        return QRect(it.points[0], QSize(w, h))

    def _hit_test_number(self, pos: QPoint):
        for it in reversed(self.items):
            if it.kind != "number":
                continue
            dx = pos.x() - it.points[0].x()
            dy = pos.y() - it.points[0].y()
            r = it.font_size + 4
            if dx * dx + dy * dy <= r * r:
                return it
        return None

    def _hit_test_draggable(self, pos: QPoint):
        for it in reversed(self.items):
            if it.kind == "number":
                dx = pos.x() - it.points[0].x()
                dy = pos.y() - it.points[0].y()
                r = it.font_size + 4
                if dx * dx + dy * dy <= r * r:
                    return it
            elif it.kind == "text":
                rect = self._text_rect(it).adjusted(-3, -3, 3, 3)
                if rect.contains(pos):
                    return it
        return None

    def mousePressEvent(self, e):
        if self._mouse_pressed:
            return
        self._mouse_pressed = True

        pos = e.position().toPoint()

        if e.button() == Qt.RightButton:
            if self.text_edit:
                self._commit_text()
                return
            if self.active_item:
                self.active_item = None
                self.update()
                return
            self.close()
            return

        if e.button() != Qt.LeftButton:
            return

        hit = self._hit_test_draggable(pos)
        if hit is not None:
            self.drag_item = hit
            self.drag_offset = QPoint(
                pos.x() - hit.points[0].x(),
                pos.y() - hit.points[0].y(),
            )
            self.drag_moved = False
            self.setCursor(Qt.ClosedHandCursor)
            return

        sel = self._selection()

        if self.tool == "select" or not sel:
            if not sel or not sel.contains(pos):
                self.sel_start = pos
                self.sel_end = pos
                if self.toolbar:
                    self.toolbar.hide()
                    self.toolbar.deleteLater()
                    self.toolbar = None
                self.update()
                return

        if self.tool in PEN_KINDS:
            self.active_item = Item(self.tool, self.current_color,
                                    self.current_width, [pos])
        elif self.tool in ("rect", "arrow"):
            self.active_item = Item(self.tool, self.current_color,
                                    self.current_width, [pos, pos])
        elif self.tool == "text":
            self._start_text_edit(pos)
        elif self.tool == "number":
            item = Item("number", self.current_color, self.current_width,
                        [pos], text=str(self.number_counter))
            item.font_size = self.number_size
            self.items.append(item)
            self.number_counter += 1
            self._update_number_tooltip()
            self.update()
        self.update()

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()

        if self.drag_item is not None:
            self.drag_item.points[0] = QPoint(
                pos.x() - self.drag_offset.x(),
                pos.y() - self.drag_offset.y(),
            )
            self.drag_moved = True
            self.update()
            return

        if self.active_item:
            if self.active_item.kind in PEN_KINDS:
                self.active_item.points.append(pos)
            elif len(self.active_item.points) >= 2:
                self.active_item.points[-1] = pos
            self.update()
            return

        if self.sel_start and not self.toolbar:
            self.sel_end = pos
            self.update()
            return

        hovered = self._hit_test_draggable(pos) if self.items else None
        if hovered is not self.hovered_item:
            self.hovered_item = hovered
            self._refresh_cursor()
            self.update()

    def mouseReleaseEvent(self, e):
        self._mouse_pressed = False

        if self.drag_item is not None:
            self.drag_item = None
            self._refresh_cursor()
            self.update()
            return

        if self.active_item:
            self.items.append(self.active_item)
            self.active_item = None
            self.update()
        elif self.sel_start and self.sel_end and not self.toolbar:
            sel = self._selection()
            if sel.width() > 5 and sel.height() > 5:
                self._show_toolbar(sel)

    def leaveEvent(self, e):
        if self.drag_item is not None:
            return
        if self.hovered_item is not None:
            self.hovered_item = None
            self.update()

    def _refresh_cursor(self):
        if self.drag_item is not None:
            self.setCursor(Qt.ClosedHandCursor)
        elif self.hovered_item is not None:
            self.setCursor(Qt.OpenHandCursor)
        elif self.tool == "text":
            self.setCursor(Qt.IBeamCursor)
        elif self.tool == "number":
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        if delta == 0:
            return
        direction = 1 if delta > 0 else -1
        pos = e.position().toPoint()

        hovered = self._hit_test_number(pos)
        if hovered is not None and hovered.text.isdigit():
            val = int(hovered.text) + direction
            val = max(NUMBER_VALUE_MIN, min(NUMBER_VALUE_MAX, val))
            if str(val) != hovered.text:
                hovered.text = str(val)
                self._recompute_counter()
                self._update_number_tooltip()
                self.update()
            e.accept()
            return

        if self.tool == "number":
            step = NUMBER_SIZE_STEP * direction
            new_size = max(NUMBER_SIZE_MIN,
                           min(NUMBER_SIZE_MAX, self.number_size + step))
            if new_size != self.number_size:
                self.number_size = new_size
                self.cfg["number_size"] = new_size
                self._update_number_tooltip()
                self.update()
            e.accept()
            return

        new_w = max(1, min(20, self.current_width + direction))
        if new_w != self.current_width:
            self._set_width(new_w)
            if self.toolbar and self.toolbar.isVisible():
                self.slider.blockSignals(True)
                self.slider.setValue(new_w)
                self.slider.blockSignals(False)
        e.accept()

    def keyPressEvent(self, e):
        mods = e.modifiers()
        ctrl = bool(mods & Qt.ControlModifier)

        if e.key() == Qt.Key_Escape:
            if self.text_edit:
                edit = self.text_edit
                self.text_edit = None
                edit.deleteLater()
                return
            self.close()
        elif e.key() == Qt.Key_C and ctrl:
            self._copy_to_clipboard()
        elif e.key() == Qt.Key_S and ctrl:
            self._save_to_file()
        elif e.key() in (Qt.Key_Return, Qt.Key_Enter):
            if not self.text_edit:
                self._copy_to_clipboard()
        elif e.key() == Qt.Key_Z and ctrl:
            if self.items:
                self.items.pop()
                self._recompute_counter()
                self._update_number_tooltip()
                self.update()
        elif e.key() == Qt.Key_Delete and self.hovered_item is not None:
            if self.hovered_item in self.items:
                self.items.remove(self.hovered_item)
                self.hovered_item = None
                self._recompute_counter()
                self._update_number_tooltip()
                self.update()

    def _recompute_counter(self):
        nums = [int(it.text) for it in self.items
                if it.kind == "number" and it.text.isdigit()]
        self.number_counter = (max(nums) + 1) if nums else 1

    def _update_number_tooltip(self):
        if self.number_btn is not None:
            self.number_btn.setToolTip(
                f"Цифра — следующий: {self.number_counter}, "
                f"размер {self.number_size} (крутите колесо)"
            )

    def _show_toolbar(self, sel):
        self.toolbar = QFrame(self)
        self.toolbar.setObjectName("Toolbar")
        self.toolbar.setStyleSheet(TOOLBAR_QSS)

        lay = QHBoxLayout(self.toolbar)
        lay.setContentsMargins(10, 7, 10, 7)
        lay.setSpacing(3)

        tools = [
            ("select", "Выделение"),
            ("pen", "Ручка"),
            ("marker", "Маркер"),
            ("highlighter", "Текстовыделитель"),
            ("neon", "Неон"),
            ("rect", "Прямоугольник"),
            ("arrow", "Стрелка"),
            ("text", "Текст"),
            ("number", "Цифра"),
        ]
        self.tool_buttons = {}
        self.number_btn = None
        for name, tip in tools:
            b = QPushButton()
            b.setIcon(make_icon(name, TEXT, 18))
            b.setIconSize(QSize(18, 18))
            b.setCheckable(True)
            b.setChecked(name == "select")
            b.setFixedSize(34, 34)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, n=name: self._set_tool(n))
            lay.addWidget(b)
            self.tool_buttons[name] = b
            if name == "number":
                self.number_btn = b

        lay.addWidget(self._vsep())

        self.color_buttons = []
        palette = [ACCENT, "#ec4899", "#ef4444", "#f59e0b",
                   "#10b981", "#3b82f6", "#ffffff", "#000000"]
        for c in palette:
            b = QPushButton()
            b.setFixedSize(22, 22)
            b.setStyleSheet(self._swatch_style(c, c == self.current_color))
            b.setToolTip(c)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, col=c: self._set_color(col))
            lay.addWidget(b)
            self.color_buttons.append((b, c))

        b_custom = QPushButton("…")
        b_custom.setStyleSheet(
            f"color:{TEXT}; background:{SURFACE_2}; "
            f"border:1px solid {BORDER}; border-radius:11px;"
        )
        b_custom.setFixedSize(22, 22)
        b_custom.setToolTip("Свой цвет…")
        b_custom.setCursor(Qt.PointingHandCursor)
        b_custom.clicked.connect(self._pick_color)
        lay.addWidget(b_custom)

        lay.addWidget(self._vsep())

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 20)
        self.slider.setValue(self.current_width)
        self.slider.setFixedWidth(90)
        self.slider.setToolTip("Толщина кисти")
        self.slider.valueChanged.connect(self._set_width)
        lay.addWidget(self.slider)

        lay.addWidget(self._vsep())

        b_copy = QPushButton()
        b_copy.setIcon(make_icon("copy", TEXT, 18))
        b_copy.setIconSize(QSize(18, 18))
        b_copy.setFixedSize(34, 34)
        b_copy.setToolTip("Копировать (Ctrl+C / Enter)")
        b_copy.setCursor(Qt.PointingHandCursor)
        b_copy.clicked.connect(self._copy_to_clipboard)
        lay.addWidget(b_copy)

        b_save = QPushButton("Сохранить")
        b_save.setObjectName("Primary")
        b_save.setIcon(make_icon("save", "#ffffff", 16))
        b_save.setIconSize(QSize(16, 16))
        b_save.setToolTip("Сохранить файл (Ctrl+S)")
        b_save.setCursor(Qt.PointingHandCursor)
        b_save.clicked.connect(self._save_to_file)
        lay.addWidget(b_save)

        self.toolbar.adjustSize()
        tw, th = self.toolbar.width(), self.toolbar.height()
        x = max(8, min(sel.left(), self.width() - tw - 8))
        y = sel.top() - th - 10
        if y < 8:
            y = sel.bottom() + 10
        self.toolbar.move(x, y)
        self.toolbar.show()
        self.toolbar.raise_()

        pos_anim = QPropertyAnimation(self.toolbar, b"pos", self.toolbar)
        pos_anim.setDuration(220)
        pos_anim.setStartValue(self.toolbar.pos())
        pos_anim.setEndValue(QPoint(x, y))
        pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        pos_anim.start(QPropertyAnimation.DeleteWhenStopped)
        self.toolbar._pos_anim = pos_anim

        _fade_in(self.toolbar, 220)
        self._set_tool("select")
        self._update_number_tooltip()

    def _vsep(self):
        sep = QFrame()
        sep.setObjectName("Sep")
        sep.setFixedWidth(1)
        return sep

    def _swatch_style(self, color, active):
        border = ACCENT if active else BORDER
        w = 2 if active else 1
        return (f"background:{color}; border-radius:11px; "
                f"border:{w}px solid {border};")

    def _set_tool(self, name):
        self.tool = name
        for n, b in self.tool_buttons.items():
            b.setChecked(n == name)
        self._refresh_cursor()

    def _set_color(self, col):
        self.current_color = col
        self.cfg["color"] = col
        for b, c in self.color_buttons:
            b.setStyleSheet(self._swatch_style(c, c == col))

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self.current_color), self,
                                    "Выберите цвет")
        if col.isValid():
            self._set_color(col.name())

    def _set_width(self, v):
        self.current_width = v
        self.cfg["thickness"] = v

    def _start_text_edit(self, pos):
        if self.text_edit:
            self._commit_text()
        self.text_pos = pos
        self.text_edit = QLineEdit(self)
        self.text_edit.setStyleSheet(
            f"background: rgba(15,11,22,200); color:{TEXT}; "
            f"border: 1px dashed {ACCENT}; border-radius:6px; "
            f"padding: 4px 8px; font-size: 14px;"
        )
        self.text_edit.setMinimumWidth(180)
        self.text_edit.move(pos)
        self.text_edit.show()
        self.text_edit.setFocus()
        _fade_in(self.text_edit, 150)
        self.text_edit.returnPressed.connect(self._commit_text)
        self.text_edit.editingFinished.connect(self._commit_text)

    def _commit_text(self):
        if not self.text_edit:
            return
        edit = self.text_edit
        self.text_edit = None
        txt = edit.text().strip()
        edit.deleteLater()
        if txt:
            item = Item("text", self.current_color, self.current_width,
                        [self.text_pos], text=txt)
            item.font_size = 12 + self.current_width * 2
            self.items.append(item)
            self.update()

    def _compute_crop_rect(self):
        sel = self._selection()
        rect = QRect(sel) if sel else QRect()
        for it in self.items:
            if it.kind == "text":
                rect = rect.united(self._text_rect(it))
            elif it.kind == "number":
                r = it.font_size + 4
                rect = rect.united(QRect(
                    it.points[0].x() - r, it.points[0].y() - r,
                    r * 2, r * 2,
                ))
            else:
                for pt in it.points:
                    rect = rect.united(QRect(pt, QSize(1, 1)))
        if rect.isNull() or rect.width() < 2 or rect.height() < 2:
            return None
        return rect.intersected(self.rect())

    def _render_result(self):
        rect = self._compute_crop_rect()
        if not rect:
            return None
        result = self.bg.copy(rect).toImage()
        p = QPainter(result)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(-rect.topLeft())
        for it in self.items:
            self._draw_item(p, it)
        p.end()
        return result

    def _copy_to_clipboard(self):
        img = self._render_result()
        if img is None:
            self.close()
            return
        QGuiApplication.clipboard().setImage(img)
        self.close()

    def _save_to_file(self):
        img = self._render_result()
        if img is None:
            self.close()
            return
        out_dir = Path(resolve_save_dir(self.cfg))
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            out_dir = Path(default_save_dir())
        name = f"flick_{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        default_path = str(out_dir / name)
        self.hide()
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить скриншот", default_path,
                "PNG (*.png);;JPEG (*.jpg);;Все файлы (*)"
            )
        finally:
            self.show()
        if not path:
            return
        if not img.save(path):
            QMessageBox.warning(self, "Ошибка",
                                "Не удалось сохранить файл")
            return
        self.close()

    def closeEvent(self, e):
        self.closed.emit()
        super().closeEvent(e)


# ═══════════════════════════════════════════════════════════════════
#  АНИМИРОВАННЫЙ ФОН НАСТРОЕК
# ═══════════════════════════════════════════════════════════════════

class BlobBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._phase = 0.0
        self._radius = 22.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(55)

    def _tick(self):
        if not self.isVisible():
            return
        self._phase = (self._phase + 0.0085) % (2 * math.pi)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = float(self.width()), float(self.height())
        if w < 4 or h < 4:
            return

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h),
                            self._radius, self._radius)
        p.setClipPath(path)

        p.fillRect(self.rect(), QColor("#0f0b16"))

        blobs = [
            (0.18, 0.10, 0.55, "#7c3aed", 0.0),
            (0.88, 0.42, 0.50, "#a855f7", math.pi * 0.7),
            (0.52, 0.98, 0.48, "#6d28d9", math.pi * 1.35),
        ]
        diag = (w * w + h * h) ** 0.5
        for bx, by, size, color, off in blobs:
            ph = self._phase + off
            cx = (bx + 0.055 * math.sin(ph)) * w
            cy = (by + 0.045 * math.cos(ph * 0.85)) * h
            r = size * diag * 0.5

            grad = QRadialGradient(QPointF(cx, cy), r)
            c1 = QColor(color)
            c1.setAlpha(115)
            grad.setColorAt(0.0, c1)
            c2 = QColor(color)
            c2.setAlpha(0)
            grad.setColorAt(1.0, c2)

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(cx, cy), r, r)

        vignette = QRadialGradient(
            QPointF(w * 0.5, h * 0.35),
            max(w, h) * 0.9,
            QPointF(w * 0.5, h * 0.35),
        )
        vignette.setColorAt(0.0, QColor(15, 11, 22, 0))
        vignette.setColorAt(1.0, QColor(15, 11, 22, 140))
        p.setBrush(QBrush(vignette))
        p.drawRect(self.rect())

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(61, 52, 80, 180), 1))
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1),
                          self._radius, self._radius)


# ═══════════════════════════════════════════════════════════════════
#  ПОЛЕ ВВОДА ГОРЯЧЕЙ КЛАВИШИ
# ═══════════════════════════════════════════════════════════════════

class HotkeyEdit(QLineEdit):
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._recording = False
        self._original = ""
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(46)
        self._refresh_placeholder()

    def set_value(self, hk: str):
        self.setText(hk or "")
        self._refresh_placeholder()

    def value(self) -> str:
        return self.text().strip()

    def _refresh_placeholder(self):
        if self._recording:
            self.setPlaceholderText("● Нажмите комбинацию…")
        elif not self.text().strip():
            self.setPlaceholderText("Кликните для записи")

    def _set_recording_prop(self, rec: bool):
        self.setProperty("recording", "true" if rec else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _start_recording(self):
        if self._recording:
            return
        self._recording = True
        self._original = self.text()
        self.setText("")
        self._set_recording_prop(True)
        self._refresh_placeholder()
        self.setFocus()

    def _stop_recording(self, cancel: bool = False):
        if not self._recording:
            return
        if cancel:
            self.setText(self._original)
        self._recording = False
        self._set_recording_prop(False)
        self._refresh_placeholder()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._start_recording()
        super().mousePressEvent(e)

    def focusOutEvent(self, e):
        if self._recording:
            self._stop_recording(cancel=True)
        super().focusOutEvent(e)

    def keyPressEvent(self, e):
        if not self._recording:
            self._start_recording()

        key = e.key()
        mods = e.modifiers()

        if key == Qt.Key_Escape:
            self._stop_recording(cancel=True)
            return

        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            self._show_modifier_preview(mods)
            return

        parts = []
        if mods & Qt.ControlModifier:
            parts.append("<ctrl>")
        if mods & Qt.ShiftModifier:
            parts.append("<shift>")
        if mods & Qt.AltModifier:
            parts.append("<alt>")
        if mods & Qt.MetaModifier:
            parts.append("<cmd>")

        name = self._map_key(key)
        if not name:
            return

        parts.append(name)
        text = "+".join(parts)
        self.setText(text)
        self._stop_recording(cancel=False)
        self.changed.emit(text)

    def keyReleaseEvent(self, e):
        if not self._recording:
            return
        mods = e.modifiers()
        if not (mods & (Qt.ControlModifier | Qt.ShiftModifier
                        | Qt.AltModifier | Qt.MetaModifier)):
            self._show_modifier_preview(Qt.NoModifier)

    def _show_modifier_preview(self, mods):
        parts = []
        if mods & Qt.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.AltModifier:
            parts.append("Alt")
        if mods & Qt.MetaModifier:
            parts.append("Win")
        if parts:
            self.setPlaceholderText("● " + " + ".join(parts) + " + …")
        else:
            self.setPlaceholderText("● Нажмите комбинацию…")

    def _map_key(self, key):
        if Qt.Key_F1 <= key <= Qt.Key_F35:
            return f"<f{key - Qt.Key_F1 + 1}>"
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).lower()
        if Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        return {
            Qt.Key_Print: "<print_screen>",
            Qt.Key_Insert: "<insert>",
            Qt.Key_Home: "<home>",
            Qt.Key_End: "<end>",
            Qt.Key_PageUp: "<page_up>",
            Qt.Key_PageDown: "<page_down>",
            Qt.Key_Space: "<space>",
            Qt.Key_Tab: "<tab>",
            Qt.Key_Return: "<enter>",
            Qt.Key_Backspace: "<backspace>",
            Qt.Key_Delete: "<delete>",
            Qt.Key_Left: "<left>",
            Qt.Key_Right: "<right>",
            Qt.Key_Up: "<up>",
            Qt.Key_Down: "<down>",
        }.get(key)


# ═══════════════════════════════════════════════════════════════════
#  НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════════

class SettingsWindow(QWidget):
    saved = Signal(dict)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = dict(cfg)
        self.cfg["hotkeys"] = dict(cfg.get("hotkeys", DEFAULT_HOTKEYS))

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(f"{APP_NAME} — Настройки · by {APP_AUTHOR}")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(620, 780)
        self.resize(660, 860)
        self.setStyleSheet(SETTINGS_QSS)

        self.bg = BlobBackground(self)
        self.bg.lower()

        self._drag_pos = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        content.setObjectName("Root")
        content.setStyleSheet("background: transparent;")

        root = QVBoxLayout(content)
        root.setContentsMargins(24, 16, 24, 20)
        root.setSpacing(12)

        # Titlebar
        titlebar = QFrame()
        titlebar.setObjectName("TitleBar")
        titlebar.setFixedHeight(44)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(10)

        tb_logo = QLabel()
        tb_logo.setObjectName("TitleBarLogo")
        tb_logo.setPixmap(_logo_pixmap(26))
        tb_logo.setFixedSize(26, 26)
        tb.addWidget(tb_logo)

        tb_text = QLabel(f"{APP_NAME} — Настройки")
        tb_text.setObjectName("TitleBarText")
        tb.addWidget(tb_text)

        tb_author = QLabel(f"by {APP_AUTHOR}")
        tb_author.setObjectName("TitleBarAuthor")
        tb.addWidget(tb_author)

        tb.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        tb.addWidget(self.close_btn)

        root.addWidget(titlebar)

        # Hero
        hero = QFrame()
        hero.setObjectName("HeroCard")
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(24, 20, 24, 20)
        hl.setSpacing(18)

        hero_logo = QLabel()
        hero_logo.setPixmap(_logo_pixmap(60))
        hero_logo.setFixedSize(60, 60)
        hero_logo.setStyleSheet("background: transparent;")
        hl.addWidget(hero_logo)

        htxt = QVBoxLayout()
        htxt.setSpacing(2)
        hn = QLabel(APP_NAME)
        hn.setObjectName("HeroName")
        htxt.addWidget(hn)
        ht = QLabel(APP_TAGLINE)
        ht.setObjectName("HeroTag")
        htxt.addWidget(ht)
        ha = QLabel(f"by {APP_AUTHOR}")
        ha.setObjectName("HeroAuthor")
        htxt.addWidget(ha)
        hl.addLayout(htxt)
        hl.addStretch()

        badge = QLabel(f"v{APP_VERSION}")
        badge.setObjectName("HeroBadge")
        badge.setAlignment(Qt.AlignCenter)
        hl.addWidget(badge, 0, Qt.AlignTop)

        root.addWidget(hero)

        # Hotkeys card
        card1 = QFrame()
        card1.setObjectName("Card")
        c1 = QVBoxLayout(card1)
        c1.setContentsMargins(22, 18, 22, 18)
        c1.setSpacing(14)

        s1 = QLabel("ГОРЯЧИЕ КЛАВИШИ")
        s1.setObjectName("SectionLabel")
        c1.addWidget(s1)

        self.hotkey_edits = {}
        for key in HOTKEY_ORDER:
            lbl = QLabel(HOTKEY_LABELS[key])
            lbl.setObjectName("HotkeyLabel")
            c1.addWidget(lbl)

            row = QHBoxLayout()
            row.setSpacing(8)

            edit = HotkeyEdit()
            edit.set_value(self.cfg["hotkeys"].get(key, DEFAULT_HOTKEYS[key]))
            self.hotkey_edits[key] = edit
            row.addWidget(edit, 1)

            btn_reset = QPushButton("×")
            btn_reset.setObjectName("ClearHotkey")
            btn_reset.setFixedSize(46, 46)
            btn_reset.setCursor(Qt.PointingHandCursor)
            btn_reset.setToolTip(
                f"Сбросить к {pretty_hotkey(DEFAULT_HOTKEYS[key])}"
            )
            btn_reset.clicked.connect(
                lambda _, k=key: self._reset_one(k)
            )
            row.addWidget(btn_reset)

            c1.addLayout(row)

        hint1 = QLabel(
            "Кликните по полю и нажмите комбинацию. "
            "Esc или клик вне — отмена."
        )
        hint1.setObjectName("Hint")
        hint1.setWordWrap(True)
        c1.addWidget(hint1)

        root.addWidget(card1)

        # Folder card
        card2 = QFrame()
        card2.setObjectName("Card")
        c2 = QVBoxLayout(card2)
        c2.setContentsMargins(22, 18, 22, 18)
        c2.setSpacing(10)

        s2 = QLabel("ПАПКА ДЛЯ СОХРАНЕНИЯ СКРИНШОТОВ")
        s2.setObjectName("SectionLabel")
        c2.addWidget(s2)

        row = QHBoxLayout()
        row.setSpacing(10)

        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText(default_save_dir())
        self.dir_edit.setText(self.cfg.get("save_dir", ""))
        self.dir_edit.setMinimumHeight(44)
        row.addWidget(self.dir_edit, 1)

        b_browse = QPushButton("Обзор…")
        b_browse.setObjectName("Browse")
        b_browse.setCursor(Qt.PointingHandCursor)
        b_browse.setMinimumHeight(44)
        b_browse.clicked.connect(self._browse_dir)
        row.addWidget(b_browse)

        c2.addLayout(row)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        b_default = QPushButton("По умолчанию")
        b_default.setCursor(Qt.PointingHandCursor)
        b_default.setMinimumHeight(40)
        b_default.clicked.connect(self._reset_dir)
        row2.addWidget(b_default)

        b_open = QPushButton("Открыть папку")
        b_open.setCursor(Qt.PointingHandCursor)
        b_open.setMinimumHeight(40)
        b_open.clicked.connect(self._open_dir)
        row2.addWidget(b_open)

        row2.addStretch()
        c2.addLayout(row2)

        h2 = QLabel(
            f"По умолчанию: {default_save_dir()}\n"
            "Здесь будут появляться файлы при сохранении."
        )
        h2.setObjectName("Hint")
        h2.setWordWrap(True)
        c2.addWidget(h2)

        root.addWidget(card2)

        # Overlay hints
        card3 = QFrame()
        card3.setObjectName("Card")
        c3 = QVBoxLayout(card3)
        c3.setContentsMargins(22, 18, 22, 18)
        c3.setSpacing(10)

        s3 = QLabel("УПРАВЛЕНИЕ В ОВЕРЛЕЕ")
        s3.setObjectName("SectionLabel")
        c3.addWidget(s3)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        items = [
            ("ЛКМ по цифре/тексту", "перетащить объект"),
            ("Колесо над цифрой",   "изменить число"),
            ("Колесо + «Цифра»",    "размер следующей цифры"),
            ("Колесо (прочее)",     "толщина кисти"),
            ("Enter / Ctrl+C",      "копировать в буфер"),
            ("Ctrl+S",              "сохранить в файл"),
            ("Ctrl+Z",              "отменить последний элемент"),
            ("Delete",              "удалить объект под курсором"),
            ("Esc",                 "закрыть"),
            ("ПКМ",                 "отменить текущий штрих"),
        ]
        for i, (key, action) in enumerate(items):
            k = QLabel(key)
            k.setStyleSheet(
                f"color:{ACCENT_HOVER}; font-weight:600; "
                f"font-family: 'JetBrains Mono', 'Cascadia Code', "
                f"Consolas, monospace; font-size: 12px; "
                f"background: transparent;"
            )
            k.setFixedWidth(210)
            k.setFixedHeight(24)
            k.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(k, i, 0)

            a = QLabel(action)
            a.setObjectName("Hint")
            a.setWordWrap(False)
            a.setFixedHeight(24)
            a.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(a, i, 1)

        c3.addLayout(grid)
        root.addWidget(card3)

        root.addStretch()

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(10)

        b_reset = QPushButton("Сбросить всё")
        b_reset.setCursor(Qt.PointingHandCursor)
        b_reset.setMinimumHeight(44)
        b_reset.clicked.connect(self._reset_all)
        btns.addWidget(b_reset)

        btns.addStretch()

        b_cancel = QPushButton("Отмена")
        b_cancel.setCursor(Qt.PointingHandCursor)
        b_cancel.setMinimumHeight(44)
        b_cancel.clicked.connect(self.close)
        btns.addWidget(b_cancel)

        b_save = QPushButton("Сохранить")
        b_save.setObjectName("Primary")
        b_save.setCursor(Qt.PointingHandCursor)
        b_save.setMinimumHeight(44)
        b_save.setMinimumWidth(150)
        b_save.clicked.connect(self._save)
        btns.addWidget(b_save)
        root.addLayout(btns)

        ver = QLabel(f"v{APP_VERSION} · by {APP_AUTHOR}")
        ver.setObjectName("Version")
        ver.setAlignment(Qt.AlignCenter)
        root.addWidget(ver)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.bg.setGeometry(self.rect())

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 64:
            self._drag_pos = (e.globalPosition().toPoint()
                              - self.frameGeometry().topLeft())
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and (e.buttons() & Qt.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def _reset_one(self, key):
        if key in self.hotkey_edits:
            self.hotkey_edits[key].set_value(DEFAULT_HOTKEYS[key])

    def _browse_dir(self):
        start = self.dir_edit.text().strip() or default_save_dir()
        chosen = QFileDialog.getExistingDirectory(
            self, "Выберите папку для скриншотов", start)
        if chosen:
            self.dir_edit.setText(chosen)

    def _reset_dir(self):
        self.dir_edit.setText("")

    def _open_dir(self):
        d = self.dir_edit.text().strip() or default_save_dir()
        if Path(d).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(d))
        else:
            QMessageBox.information(
                self, "Папка не найдена",
                f"Путь не существует:\n{d}"
            )

    def _reset_all(self):
        r = QMessageBox.question(
            self, "Сброс настроек",
            "Вернуть все настройки к значениям по умолчанию?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            for k, edit in self.hotkey_edits.items():
                edit.set_value(DEFAULT_HOTKEYS[k])
            self.dir_edit.setText("")

    def showEvent(self, e):
        super().showEvent(e)
        self.bg.setGeometry(self.rect())
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(260)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._anim = anim

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            focused = self.focusWidget()
            if isinstance(focused, HotkeyEdit):
                return
            self.close()

    def _save(self):
        values = {}
        for key in HOTKEY_ORDER:
            edit = self.hotkey_edits[key]
            v = edit.value()
            if not v:
                QMessageBox.warning(
                    self, "Ошибка",
                    f"Не задана комбинация для «{HOTKEY_LABELS[key]}»."
                )
                return
            try:
                keyboard.HotKey.parse(v)
            except Exception as ex:
                QMessageBox.warning(
                    self, "Ошибка",
                    f"Неверная комбинация «{v}»: {ex}"
                )
                return
            values[key] = v

        used = {}
        for key, v in values.items():
            if v in used:
                QMessageBox.warning(
                    self, "Конфликт",
                    f"Комбинация «{pretty_hotkey(v)}» назначена "
                    f"на два действия:\n"
                    f"  • {HOTKEY_LABELS[used[v]]}\n"
                    f"  • {HOTKEY_LABELS[key]}"
                )
                return
            used[v] = key

        d = self.dir_edit.text().strip()
        if d and not Path(d).is_dir():
            r = QMessageBox.question(
                self, "Папка не существует",
                f"Папки по пути нет:\n{d}\n\nСоздать её?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes,
            )
            if r == QMessageBox.Yes:
                try:
                    Path(d).mkdir(parents=True, exist_ok=True)
                except Exception as ex:
                    QMessageBox.warning(
                        self, "Ошибка",
                        f"Не удалось создать папку:\n{ex}"
                    )
                    return
            else:
                return

        self.cfg["hotkeys"] = values
        self.cfg["save_dir"] = d
        config_save(self.cfg)
        self.saved.emit(self.cfg)
        self.close()


# ═══════════════════════════════════════════════════════════════════
#  ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════════════

def _is_already_running() -> bool:
    sock = QLocalSocket()
    sock.connectToServer(SINGLE_INSTANCE_KEY)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(200)
        sock.disconnectFromServer()
        return True
    return False


class App(QObject):
    trigger_shot = Signal()
    trigger_full_copy = Signal()
    trigger_full_save = Signal()

    def __init__(self):
        super().__init__()

        self.cfg = config_load()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationVersion(APP_VERSION)
        self.app.setOrganizationName(APP_AUTHOR)
        self.app.setWindowIcon(app_icon())
        self.app.setStyle("Fusion")

        QTimer.singleShot(100, _get_dxcam)

        if _is_already_running():
            QMessageBox.information(
                None,
                APP_NAME,
                f"{APP_NAME} уже запущен.\n\n"
                f"Ищи иконку в трее — рядом с часами.",
            )
            sys.exit(0)

        QLocalServer.removeServer(SINGLE_INSTANCE_KEY)
        self.server = QLocalServer()
        self.server.newConnection.connect(self._on_new_connection)
        if not self.server.listen(SINGLE_INSTANCE_KEY):
            print("Warning: single-instance server failed")

        self.tray = QSystemTrayIcon(app_icon())
        self.tray.setToolTip(f"{APP_NAME} · by {APP_AUTHOR}")
        self._build_menu()
        self.tray.show()

        self.hotkeys = None
        self._start_hotkeys()

        self.trigger_shot.connect(self._take_shot, Qt.QueuedConnection)
        self.trigger_full_copy.connect(self._fullscreen_copy,
                                       Qt.QueuedConnection)
        self.trigger_full_save.connect(self._fullscreen_save,
                                       Qt.QueuedConnection)

        self.overlay = None
        self.settings_win = None

    def _on_new_connection(self):
        while self.server.hasPendingConnections():
            conn = self.server.nextPendingConnection()
            conn.readyRead.connect(
                lambda c=conn: self._read_from_client(c)
            )
            conn.disconnected.connect(conn.deleteLater)

    def _read_from_client(self, conn):
        try:
            data = bytes(conn.readAll())
        except Exception:
            data = b""
        if b"show" in data:
            self.tray.showMessage(
                APP_NAME,
                "Программа уже запущена и работает в трее.",
                QSystemTrayIcon.Information, 2500,
            )
        try:
            conn.disconnectFromServer()
        except Exception:
            pass

    def _hk(self, key: str) -> str:
        return pretty_hotkey(
            self.cfg.get("hotkeys", {}).get(key, "")
        )

    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet(TRAY_MENU_QSS)

        a_shot = QAction(
            make_icon("select", TEXT, 14),
            f"Сделать скрин ({self._hk('screenshot')})",
            menu
        )
        a_shot.triggered.connect(self._take_shot)
        menu.addAction(a_shot)

        a_fc = QAction(
            make_icon("copy", TEXT, 14),
            f"Полный экран → буфер ({self._hk('fullscreen_copy')})",
            menu
        )
        a_fc.triggered.connect(self._fullscreen_copy)
        menu.addAction(a_fc)

        a_fs = QAction(
            make_icon("save", TEXT, 14),
            f"Полный экран → файл ({self._hk('fullscreen_save')})",
            menu
        )
        a_fs.triggered.connect(self._fullscreen_save)
        menu.addAction(a_fs)

        menu.addSeparator()

        a_set = QAction(make_icon("settings", TEXT, 14),
                        "Настройки…", menu)
        a_set.triggered.connect(self._open_settings)
        menu.addAction(a_set)

        menu.addSeparator()

        a_about = QAction(f"О {APP_NAME} — by {APP_AUTHOR}", menu)
        a_about.triggered.connect(self._show_about)
        menu.addAction(a_about)

        menu.addSeparator()

        a_quit = QAction("Выход", menu)
        a_quit.triggered.connect(self.app.quit)
        menu.addAction(a_quit)

        self.tray.setContextMenu(menu)

    def _show_about(self):
        hk = self.cfg.get("hotkeys", {})
        rows = "".join(
            f"<tr><td style='padding-right:14px; color:#c084fc;'>"
            f"{pretty_hotkey(hk.get(k, ''))}</td>"
            f"<td style='color:#9d95b0;'>{HOTKEY_LABELS[k]}</td></tr>"
            for k in HOTKEY_ORDER
        )
        QMessageBox.information(
            None,
            f"О {APP_NAME}",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            f"<p>{APP_TAGLINE}</p>"
            f"<p style='color:#9d95b0;'>by <b>{APP_AUTHOR}</b></p>"
            f"<table>{rows}</table>"
            f"<p style='margin-top:10px;'>"
            f"Папка сохранения: <b>{resolve_save_dir(self.cfg)}</b></p>",
        )

    def _start_hotkeys(self):
        if self.hotkeys:
            try:
                self.hotkeys.stop()
            except Exception:
                pass

        hk = self.cfg.get("hotkeys", {})
        mapping = {}
        if hk.get("screenshot"):
            mapping[hk["screenshot"]] = lambda: self.trigger_shot.emit()
        if hk.get("fullscreen_copy"):
            mapping[hk["fullscreen_copy"]] = (
                lambda: self.trigger_full_copy.emit()
            )
        if hk.get("fullscreen_save"):
            mapping[hk["fullscreen_save"]] = (
                lambda: self.trigger_full_save.emit()
            )

        if not mapping:
            return

        try:
            self.hotkeys = keyboard.GlobalHotKeys(mapping)
            self.hotkeys.start()
        except Exception as e:
            print("Hotkey error:", e)

    @Slot()
    def _take_shot(self):
        if self.overlay and self.overlay.isVisible():
            return
        self.overlay = Overlay(self.cfg)
        self.overlay.closed.connect(self._on_overlay_closed)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()
        self.overlay.setFocus(Qt.ActiveWindowFocusReason)

    @Slot()
    def _fullscreen_copy(self):
        pm = capture_fullscreen()
        if pm is None:
            self.tray.showMessage(
                APP_NAME, "Не удалось захватить экран",
                QSystemTrayIcon.Warning, 2000,
            )
            return
        QGuiApplication.clipboard().setImage(pm.toImage())
        self.tray.showMessage(
            APP_NAME, "Полный экран скопирован в буфер",
            QSystemTrayIcon.Information, 1800,
        )

    @Slot()
    def _fullscreen_save(self):
        pm = capture_fullscreen()
        if pm is None:
            self.tray.showMessage(
                APP_NAME, "Не удалось захватить экран",
                QSystemTrayIcon.Warning, 2000,
            )
            return
        out_dir = Path(resolve_save_dir(self.cfg))
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            out_dir = Path(default_save_dir())
        name = f"flick_full_{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        path = out_dir / name
        if pm.save(str(path)):
            self.tray.showMessage(
                APP_NAME, f"Сохранено: {name}",
                QSystemTrayIcon.Information, 1800,
            )
        else:
            self.tray.showMessage(
                APP_NAME, "Не удалось сохранить файл",
                QSystemTrayIcon.Warning, 2000,
            )

    def _on_overlay_closed(self):
        self.overlay = None
        config_save(self.cfg)

    def _open_settings(self):
        self.settings_win = SettingsWindow(self.cfg)
        self.settings_win.saved.connect(self._on_settings_saved)
        self.settings_win.show()
        self.settings_win.raise_()
        self.settings_win.activateWindow()

    def _on_settings_saved(self, cfg):
        self.cfg = cfg
        self._start_hotkeys()
        self._build_menu()
        self.tray.showMessage(
            APP_NAME,
            f"Настройки сохранены.\n"
            f"Скрин: {self._hk('screenshot')}   "
            f"Буфер: {self._hk('fullscreen_copy')}   "
            f"Файл: {self._hk('fullscreen_save')}",
            QSystemTrayIcon.Information, 2500,
        )

    def run(self):
        return self.app.exec()


if __name__ == "__main__":
    sys.exit(App().run())