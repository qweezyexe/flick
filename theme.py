"""Цвета и QSS-стили Flick."""

import base64

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


# ─── SVG-галочка для чекбокса (в base64, без файлов) ───
_CHECK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="none" stroke="white" stroke-width="3.4" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="20 6 9 17 4 12"/></svg>'
)
_CHECK_B64 = base64.b64encode(_CHECK_SVG.encode()).decode()
_CHECK_URI = f"data:image/svg+xml;base64,{_CHECK_B64}"


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
    font-family: "Segoe UI Variable Display", "Segoe UI", "SF Pro Display", Inter, sans-serif;
}}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: rgba(168, 85, 247, 0.45);
    border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: rgba(168, 85, 247, 0.75); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QFrame#TitleBar {{ background: transparent; }}
QLabel#TitleBarLogo {{ background: transparent; }}
QLabel#TitleBarText {{ color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent; }}
QLabel#TitleBarAuthor {{ color: {TEXT_MUTED}; font-size: 11px; background: transparent; }}
QPushButton#CloseBtn {{
    background: transparent; border: none; color: {TEXT_MUTED};
    font-size: 18px; border-radius: 8px; padding: 0; font-weight: 400;
}}
QPushButton#CloseBtn:hover {{ background: #ff5f57; color: #ffffff; }}
QPushButton#CloseBtn:pressed {{ background: #d94b43; }}

QFrame#Card {{
    background: rgba(26, 20, 40, 0.72);
    border: 1px solid {BORDER}; border-radius: 18px;
}}
QFrame#HeroCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #c084fc, stop:0.5 #a855f7, stop:1 #6d28d9);
    border: none; border-radius: 20px;
}}
QFrame#WarnCard {{
    background: rgba(245, 158, 11, 0.10);
    border: 1px solid rgba(245, 158, 11, 0.45);
    border-radius: 14px;
}}
QLabel#WarnIcon {{
    background: rgba(245, 158, 11, 0.20);
    border: 1px solid rgba(245, 158, 11, 0.55);
    border-radius: 8px; color: #fbbf24; font-size: 18px; font-weight: 700;
}}
QLabel#WarnTitle {{
    color: #fbbf24; font-size: 13px; font-weight: 700;
    background: transparent; letter-spacing: 0.02em;
}}
QLabel#WarnBody {{ color: rgba(251, 191, 36, 0.85); font-size: 12px; background: transparent; }}

QLabel#SectionLabel {{
    color: {TEXT}; font-size: 12px; font-weight: 700;
    letter-spacing: 0.08em; background: transparent;
}}
QLabel#Hint {{ color: {TEXT_MUTED}; font-size: 12px; background: transparent; }}
QLabel#HotkeyLabel {{ color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent; }}
QLabel#Version {{ color: {TEXT_MUTED}; font-size: 11px; background: transparent; letter-spacing: 0.04em; }}

QLabel#HeroName {{
    color: #ffffff; font-size: 26px; font-weight: 800;
    letter-spacing: -0.02em; background: transparent;
}}
QLabel#HeroTag {{ color: rgba(255,255,255,0.88); font-size: 13px; background: transparent; }}
QLabel#HeroAuthor {{ color: rgba(255,255,255,0.72); font-size: 11px; background: transparent; letter-spacing: 0.04em; }}
QLabel#HeroBadge {{
    color: #ffffff; font-size: 11px; font-weight: 700;
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 999px; padding: 5px 14px; letter-spacing: 0.03em;
}}

QLineEdit {{
    background: rgba(15, 11, 22, 0.75);
    border: 1px solid {BORDER}; border-radius: 12px;
    padding: 12px 16px; color: {TEXT}; font-size: 14px;
    selection-background-color: {ACCENT}; selection-color: #ffffff;
    font-family: 'JetBrains Mono', 'Cascadia Code', Consolas, monospace;
    letter-spacing: 0.02em;
}}
QLineEdit:hover {{ border: 1px solid {BORDER_2}; }}
QLineEdit:focus {{ border: 1px solid {ACCENT}; background: rgba(15, 11, 22, 0.95); }}
QLineEdit[recording="true"] {{
    border: 2px solid {ACCENT_HOVER};
    background: rgba(168, 85, 247, 0.15); color: #ffffff;
}}

QPushButton {{
    background: rgba(45, 36, 56, 0.7);
    border: 1px solid {BORDER}; border-radius: 12px;
    padding: 12px 22px; color: {TEXT};
    font-weight: 600; font-size: 13px; min-height: 22px;
}}
QPushButton:hover {{ background: rgba(61, 52, 80, 0.9); border: 1px solid {BORDER_2}; }}
QPushButton:pressed {{ background: {ACCENT_SOFT}; }}

QPushButton#Primary {{
    background-color: {ACCENT}; border: 1px solid {ACCENT};
    color: #ffffff; font-weight: 700; padding: 12px 28px; min-height: 22px;
}}
QPushButton#Primary:hover {{ background-color: {ACCENT_HOVER}; border: 1px solid {ACCENT_HOVER}; }}
QPushButton#Primary:pressed {{ background-color: {ACCENT_PRESSED}; border: 1px solid {ACCENT_PRESSED}; }}

QPushButton#Browse {{
    background: rgba(45, 36, 56, 0.7); border: 1px solid {BORDER};
    padding: 11px 20px; min-width: 90px; font-weight: 600;
}}
QPushButton#Browse:hover {{
    background: rgba(168, 85, 247, 0.15);
    border: 1px solid {ACCENT}; color: {ACCENT_HOVER};
}}
QPushButton#ClearHotkey {{
    background: rgba(45, 36, 56, 0.7); border: 1px solid {BORDER};
    border-radius: 12px; padding: 0; font-size: 20px;
    font-weight: 400; color: {TEXT_MUTED};
    min-width: 46px; max-width: 46px; min-height: 46px;
}}
QPushButton#ClearHotkey:hover {{
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444; color: #fca5a5;
}}
QPushButton#ClearHotkey:pressed {{ background: rgba(239, 68, 68, 0.3); }}

QCheckBox {{
    color: {TEXT};
    font-size: 13px;
    spacing: 10px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 22px;
    height: 22px;
    border-radius: 6px;
    border: 1px solid {BORDER_2};
    background: rgba(15, 11, 22, 0.75);
}}
QCheckBox::indicator:hover {{
    border: 1px solid {ACCENT};
    background: rgba(168, 85, 247, 0.10);
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border: 1px solid {ACCENT_HOVER};
    image: url("{_CHECK_URI}");
}}
QCheckBox::indicator:checked:hover {{
    background-color: {ACCENT_HOVER};
}}
"""


TRAY_MENU_QSS = f"""
QMenu {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 10px; padding: 6px;
}}
QMenu::item {{ padding: 8px 22px 8px 14px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACCENT}; color: white; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
"""