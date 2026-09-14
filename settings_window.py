"""Окно настроек Flick."""

import math
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QLineEdit, QPushButton, QMessageBox, QFileDialog,
    QGraphicsOpacityEffect, QScrollArea, QCheckBox, QSizePolicy,
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QPen, QRadialGradient,
    QBrush, QDesktopServices, QFont, QFontMetrics,
)
from PySide6.QtCore import (
    Qt, Signal, QPointF, QRectF, QPropertyAnimation,
    QEasingCurve, QUrl, QTimer, QStandardPaths,
)

from pynput import keyboard

from config import (
    DEFAULT_HOTKEYS, HOTKEY_LABELS, HOTKEY_ORDER, save as config_save,
)
from state import APP_NAME, APP_VERSION, APP_AUTHOR, pretty_hotkey
from icons import _logo_pixmap, app_icon
import theme


def default_save_dir() -> str:
    loc = QStandardPaths.writableLocation(
        QStandardPaths.PicturesLocation)
    return loc or str(Path.home())


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


class FlickCheckBox(QCheckBox):
    """Чекбокс с собственной отрисовкой галочки. Всё центрируется
    внутри виджета: и квадратик, и текст."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        box_size = 22
        spacing = 10

        # Измеряем текст
        f = QFont()
        f.setPointSize(9)
        fm = QFontMetrics(f)
        text_w = fm.horizontalAdvance(self.text())
        text_h = fm.height()

        # Общая ширина содержимого
        content_w = box_size + spacing + text_w
        content_h = max(box_size, text_h)

        # Левый верхний угол содержимого — центрируем
        start_x = (self.width() - content_w) / 2.0
        start_y = (self.height() - content_h) / 2.0

        box_x = start_x
        box_y = start_y + (content_h - box_size) / 2.0
        rect = QRectF(box_x, box_y, box_size, box_size)
        radius = 6.0

        checked = self.isChecked()
        hovered = self.underMouse()

        # Фон и рамка квадратика
        if checked:
            fill = QColor("#a855f7")
            if hovered:
                fill = QColor("#c084fc")
            border = QColor("#c084fc")
        else:
            fill = QColor(15, 11, 22, 190)
            if hovered:
                fill = QColor(168, 85, 247, 25)
                border = QColor("#a855f7")
            else:
                border = QColor("#4a3f5f")

        p.setPen(QPen(border, 1.5))
        p.setBrush(fill)
        p.drawRoundedRect(rect, radius, radius)

        # Галочка
        if checked:
            path = QPainterPath()
            path.moveTo(rect.left() + box_size * 0.22,
                        rect.top() + box_size * 0.52)
            path.lineTo(rect.left() + box_size * 0.44,
                        rect.top() + box_size * 0.72)
            path.lineTo(rect.left() + box_size * 0.80,
                        rect.top() + box_size * 0.30)

            pen = QPen(QColor("#ffffff"), 2.4, Qt.SolidLine,
                       Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

        # Текст
        text_x = box_x + box_size + spacing
        text_rect = QRectF(text_x, start_y, text_w, content_h)
        p.setPen(QColor("#ece7f5"))
        p.setFont(f)
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.update()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.update()

    def enterEvent(self, e):
        super().enterEvent(e)
        self.update()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.update()


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
        self.resize(660, 1000)
        self.setStyleSheet(theme.SETTINGS_QSS)

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
        root.setContentsMargins(24, 16, 24, 24)
        root.setSpacing(14)

        # Titlebar
        titlebar = QFrame()
        titlebar.setObjectName("TitleBar")
        titlebar.setFixedHeight(44)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(10)

        tb_logo = QLabel()
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
        ht = QLabel("Скриншоты и аннотации")
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

        # Hotkeys
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

        # Behavior
        card_behavior = QFrame()
        card_behavior.setObjectName("Card")
        cb = QVBoxLayout(card_behavior)
        cb.setContentsMargins(22, 18, 22, 18)
        cb.setSpacing(10)

        sb = QLabel("ПОВЕДЕНИЕ")
        sb.setObjectName("SectionLabel")
        sb.setAlignment(Qt.AlignCenter)
        cb.addWidget(sb)

        self.cb_fullscreen = FlickCheckBox(
            "В играх делать полный скриншот сразу в буфер"
        )
        self.cb_fullscreen.setChecked(
            self.cfg.get("auto_fullscreen_in_games", True)
        )
        cb.addWidget(self.cb_fullscreen)

        hint_behavior = QLabel(
            "Если включено: F7 в полноэкранной игре сразу копирует "
            "основной монитор в буфер, минуя оверлей.\n"
            "Браузеры в F11-fullscreen распознаются отдельно — "
            "для них F7 открывает обычный оверлей."
        )
        hint_behavior.setObjectName("Hint")
        hint_behavior.setWordWrap(True)
        hint_behavior.setAlignment(Qt.AlignCenter)
        cb.addWidget(hint_behavior)

        root.addWidget(card_behavior)

        # Warning
        card_warn = QFrame()
        card_warn.setObjectName("WarnCard")
        cw = QHBoxLayout(card_warn)
        cw.setContentsMargins(20, 16, 20, 16)
        cw.setSpacing(14)

        warn_icon = QLabel("⚠")
        warn_icon.setObjectName("WarnIcon")
        warn_icon.setFixedSize(32, 32)
        warn_icon.setAlignment(Qt.AlignCenter)
        cw.addWidget(warn_icon, 0, Qt.AlignTop)

        wtxt = QVBoxLayout()
        wtxt.setSpacing(4)

        wtitle = QLabel("Важно знать")
        wtitle.setObjectName("WarnTitle")
        wtxt.addWidget(wtitle)

        wbody = QLabel(
            "F10 и Ctrl+L в оверлее загружают скрин на публичный "
            "хостинг (catbox.moe). Любой, кто знает ссылку, увидит "
            "картинку. Не делай так со скринами паролей, карт, "
            "личных данных.\n\n"
            "В полноэкранных играх (Exclusive Fullscreen) оверлей "
            "поверх игры может не отрисоваться — работает "
            "в Borderless Fullscreen.\n\n"
            "При нескольких мониторах F8 и F9 снимают только "
            "основной экран, а оверлей (F7) покрывает все."
        )
        wbody.setObjectName("WarnBody")
        wbody.setWordWrap(True)
        wtxt.addWidget(wbody)

        cw.addLayout(wtxt, 1)
        root.addWidget(card_warn)

        # Folder
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

        h2 = QLabel(f"По умолчанию: {default_save_dir()}")
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
            ("Ctrl+L",              "загрузить как ссылку"),
            ("Ctrl+Z",              "отменить последний элемент"),
            ("Delete",              "удалить объект под курсором"),
            ("Esc",                 "закрыть"),
            ("ПКМ",                 "отменить текущий штрих"),
        ]
        for i, (key, action) in enumerate(items):
            k = QLabel(key)
            k.setStyleSheet(
                f"color:{theme.ACCENT_HOVER}; font-weight:600; "
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

        root.addSpacing(6)

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(12)

        b_reset = QPushButton("Сбросить всё")
        b_reset.setCursor(Qt.PointingHandCursor)
        b_reset.setMinimumHeight(46)
        b_reset.setMinimumWidth(160)
        b_reset.clicked.connect(self._reset_all)
        btns.addWidget(b_reset)

        btns.addStretch()

        b_cancel = QPushButton("Отмена")
        b_cancel.setCursor(Qt.PointingHandCursor)
        b_cancel.setMinimumHeight(46)
        b_cancel.setMinimumWidth(120)
        b_cancel.clicked.connect(self.close)
        btns.addWidget(b_cancel)

        b_save = QPushButton("Сохранить")
        b_save.setObjectName("Primary")
        b_save.setCursor(Qt.PointingHandCursor)
        b_save.setMinimumHeight(46)
        b_save.setMinimumWidth(160)
        b_save.clicked.connect(self._save)
        btns.addWidget(b_save)
        root.addLayout(btns)

        root.addSpacing(4)

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
            self.cb_fullscreen.setChecked(True)

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
        self.cfg["auto_fullscreen_in_games"] = self.cb_fullscreen.isChecked()
        config_save(self.cfg)
        self.saved.emit(self.cfg)
        self.close()