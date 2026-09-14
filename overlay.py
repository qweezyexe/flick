"""Полноэкранный оверлей с редактором."""

import sys
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QHBoxLayout, QFrame,
    QColorDialog, QSlider, QFileDialog, QMessageBox,
    QGraphicsOpacityEffect, QApplication, QSystemTrayIcon,
)
from PySide6.QtGui import (
    QPainter, QPen, QColor, QGuiApplication, QPixmap,
)
from PySide6.QtCore import (
    Qt, QRect, QPoint, QSize, QStandardPaths,
    Signal, Slot, QPropertyAnimation, QEasingCurve, QTimer,
)

from state import (
    Item, EditorState, PEN_KINDS, NUMBER_SIZE_MIN, NUMBER_SIZE_MAX,
    NUMBER_SIZE_STEP, NUMBER_VALUE_MIN, NUMBER_VALUE_MAX,
    APP_NAME, compute_text_rect, number_radius,
)
from icons import make_icon
from capture import capture_all_monitors
from upload import upload_to_catbox
from tools import draw_item
import theme


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


def _compute_dpi_scale() -> float:
    try:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return 1.0
        dpi = screen.logicalDotsPerInch()
        scale = dpi / 96.0
        return max(1.0, min(2.5, scale))
    except Exception:
        return 1.0


def default_save_dir() -> str:
    loc = QStandardPaths.writableLocation(
        QStandardPaths.PicturesLocation)
    return loc or str(Path.home())


def resolve_save_dir(cfg) -> str:
    d = (cfg.get("save_dir") or "").strip()
    if d and Path(d).is_dir():
        return d
    return default_save_dir()


class Overlay(QWidget):
    closed = Signal()
    upload_done = Signal(object)

    def __init__(self, cfg, state: EditorState):
        super().__init__()
        self.cfg = cfg
        self.state = state
        self._scale = _compute_dpi_scale()

        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)

        bg = capture_all_monitors()

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
        self.items = []
        self.active_item = None
        self.text_edit = None
        self.text_pos = QPoint(0, 0)
        self.toolbar = None
        self.tool_buttons = {}
        self.color_buttons = []
        self.number_btn = None

        self.hovered_item = None
        self.drag_item = None
        self.drag_offset = QPoint(0, 0)
        self._mouse_pressed = False

        self.upload_done.connect(self._on_upload_done, Qt.QueuedConnection)

    def showEvent(self, e):
        super().showEvent(e)
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)
        self._force_topmost()
        QTimer.singleShot(50, self._force_topmost)

    def _force_topmost(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            hwnd = int(self.winId())
            user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
            self.raise_()
            self.activateWindow()
            self.setFocus(Qt.ActiveWindowFocusReason)
        except Exception as e:
            print("SetWindowPos error:", e)

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

            p.setPen(QPen(QColor(theme.ACCENT), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRect(sel)

            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.ACCENT))
            hs = int(5 * self._scale)
            for pt in (sel.topLeft(), sel.topRight(),
                       sel.bottomLeft(), sel.bottomRight()):
                p.drawEllipse(pt, hs, hs)
        else:
            p.fillRect(self.rect(), QColor(0, 0, 0, 120))

        for it in self.items:
            draw_item(p, it)

        highlight = self.drag_item or self.hovered_item
        if highlight is not None:
            if highlight.kind == "number":
                r = number_radius(highlight) + 4
                p.setPen(QPen(QColor("#ffffff"), 1.5, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(highlight.points[0], r, r)
            elif highlight.kind == "text":
                r = compute_text_rect(highlight).adjusted(-3, -3, 3, 3)
                p.setPen(QPen(QColor("#ffffff"), 1.5, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawRect(r)

        if self.active_item:
            draw_item(p, self.active_item)

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

    def _hit_test_number(self, pos):
        for it in reversed(self.items):
            if it.kind != "number":
                continue
            dx = pos.x() - it.points[0].x()
            dy = pos.y() - it.points[0].y()
            r = number_radius(it)
            if dx * dx + dy * dy <= r * r:
                return it
        return None

    def _hit_test_draggable(self, pos):
        for it in reversed(self.items):
            if it.kind == "number":
                dx = pos.x() - it.points[0].x()
                dy = pos.y() - it.points[0].y()
                r = number_radius(it)
                if dx * dx + dy * dy <= r * r:
                    return it
            elif it.kind == "text":
                rect = compute_text_rect(it).adjusted(-3, -3, 3, 3)
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
            self.setCursor(Qt.ClosedHandCursor)
            return

        sel = self._selection()

        if self.state.tool == "select" or not sel:
            if not sel or not sel.contains(pos):
                self.sel_start = pos
                self.sel_end = pos
                if self.toolbar:
                    self.toolbar.hide()
                    self.toolbar.deleteLater()
                    self.toolbar = None
                self.update()
                return

        if self.state.tool in PEN_KINDS:
            self.active_item = Item(self.state.tool, self.state.color,
                                    self.state.width, [pos])
        elif self.state.tool in ("rect", "arrow"):
            self.active_item = Item(self.state.tool, self.state.color,
                                    self.state.width, [pos, pos])
        elif self.state.tool == "text":
            self._start_text_edit(pos)
        elif self.state.tool == "number":
            item = Item("number", self.state.color, self.state.width,
                        [pos], text=str(self.state.number_counter))
            item.font_size = self.state.number_size
            self.items.append(item)
            self.state.number_counter += 1
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
        elif self.state.tool == "text":
            self.setCursor(Qt.IBeamCursor)
        elif self.state.tool == "number":
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

        if self.state.tool == "number":
            step = NUMBER_SIZE_STEP * direction
            new_size = max(NUMBER_SIZE_MIN,
                           min(NUMBER_SIZE_MAX,
                               self.state.number_size + step))
            if new_size != self.state.number_size:
                self.state.number_size = new_size
                self.cfg["number_size"] = new_size
                self._update_number_tooltip()
                self.update()
            e.accept()
            return

        new_w = max(1, min(20, self.state.width + direction))
        if new_w != self.state.width:
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
        elif e.key() == Qt.Key_L and ctrl:
            self._upload_to_link()
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
        self.state.number_counter = (max(nums) + 1) if nums else 1

    def _update_number_tooltip(self):
        if self.number_btn is not None:
            self.number_btn.setToolTip(
                f"Цифра — следующий: {self.state.number_counter}, "
                f"размер {self.state.number_size}"
            )

    def _show_toolbar(self, sel):
        s = self._scale
        self.toolbar = QFrame(self)
        self.toolbar.setObjectName("Toolbar")
        self.toolbar.setStyleSheet(theme.TOOLBAR_QSS)

        lay = QHBoxLayout(self.toolbar)
        m = int(10 * s)
        lay.setContentsMargins(m, int(7 * s), m, int(7 * s))
        lay.setSpacing(max(2, int(3 * s)))

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

        btn_size = int(34 * s)
        icon_size = int(18 * s)

        self.tool_buttons = {}
        self.number_btn = None
        for name, tip in tools:
            b = QPushButton()
            b.setIcon(make_icon(name, theme.TEXT, icon_size))
            b.setIconSize(QSize(icon_size, icon_size))
            b.setCheckable(True)
            b.setChecked(name == "select")
            b.setFixedSize(btn_size, btn_size)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, n=name: self._set_tool(n))
            lay.addWidget(b)
            self.tool_buttons[name] = b
            if name == "number":
                self.number_btn = b

        lay.addWidget(self._vsep())

        swatch = int(22 * s)
        self.color_buttons = []
        palette = [theme.ACCENT, "#ec4899", "#ef4444", "#f59e0b",
                   "#10b981", "#3b82f6", "#ffffff", "#000000"]
        for c in palette:
            b = QPushButton()
            b.setFixedSize(swatch, swatch)
            b.setStyleSheet(self._swatch_style(c, c == self.state.color))
            b.setToolTip(c)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, col=c: self._set_color(col))
            lay.addWidget(b)
            self.color_buttons.append((b, c))

        b_custom = QPushButton("…")
        b_custom.setStyleSheet(
            f"color:{theme.TEXT}; background:{theme.SURFACE_2}; "
            f"border:1px solid {theme.BORDER}; "
            f"border-radius:{swatch//2}px;"
        )
        b_custom.setFixedSize(swatch, swatch)
        b_custom.setToolTip("Свой цвет…")
        b_custom.setCursor(Qt.PointingHandCursor)
        b_custom.clicked.connect(self._pick_color)
        lay.addWidget(b_custom)

        lay.addWidget(self._vsep())

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 20)
        self.slider.setValue(self.state.width)
        self.slider.setFixedWidth(int(90 * s))
        self.slider.setToolTip("Толщина кисти")
        self.slider.valueChanged.connect(self._set_width)
        lay.addWidget(self.slider)

        lay.addWidget(self._vsep())

        b_copy = QPushButton()
        b_copy.setIcon(make_icon("copy", theme.TEXT, icon_size))
        b_copy.setIconSize(QSize(icon_size, icon_size))
        b_copy.setFixedSize(btn_size, btn_size)
        b_copy.setToolTip("Копировать (Ctrl+C / Enter)")
        b_copy.setCursor(Qt.PointingHandCursor)
        b_copy.clicked.connect(self._copy_to_clipboard)
        lay.addWidget(b_copy)

        b_link = QPushButton()
        b_link.setIcon(make_icon("link", theme.TEXT, icon_size))
        b_link.setIconSize(QSize(icon_size, icon_size))
        b_link.setFixedSize(btn_size, btn_size)
        b_link.setToolTip("Загрузить как ссылку (Ctrl+L)")
        b_link.setCursor(Qt.PointingHandCursor)
        b_link.clicked.connect(self._upload_to_link)
        lay.addWidget(b_link)

        b_save = QPushButton("Сохранить")
        b_save.setObjectName("Primary")
        b_save.setIcon(make_icon("save", "#ffffff", int(16 * s)))
        b_save.setIconSize(QSize(int(16 * s), int(16 * s)))
        b_save.setToolTip("Сохранить файл (Ctrl+S)")
        b_save.setCursor(Qt.PointingHandCursor)
        b_save.setMinimumHeight(btn_size)
        b_save.clicked.connect(self._save_to_file)
        lay.addWidget(b_save)

        self.toolbar.adjustSize()
        tw, th = self.toolbar.width(), self.toolbar.height()
        x = max(8, min(sel.left(), self.width() - tw - 8))
        y = sel.top() - th - int(10 * s)
        if y < 8:
            y = sel.bottom() + int(10 * s)
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
        border = theme.ACCENT if active else theme.BORDER
        w = 2 if active else 1
        radius = int(11 * self._scale)
        return (f"background:{color}; border-radius:{radius}px; "
                f"border:{w}px solid {border};")

    def _set_tool(self, name):
        self.state.tool = name
        for n, b in self.tool_buttons.items():
            b.setChecked(n == name)
        self._refresh_cursor()

    def _set_color(self, col):
        self.state.color = col
        self.cfg["color"] = col
        for b, c in self.color_buttons:
            b.setStyleSheet(self._swatch_style(c, c == col))

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self.state.color), self,
                                    "Выберите цвет")
        if col.isValid():
            self._set_color(col.name())

    def _set_width(self, v):
        self.state.width = v
        self.cfg["thickness"] = v

    def _start_text_edit(self, pos):
        if self.text_edit:
            self._commit_text()
        self.text_pos = pos
        self.text_edit = QLineEdit(self)
        self.text_edit.setStyleSheet(
            f"background: rgba(15,11,22,200); color:{theme.TEXT}; "
            f"border: 1px dashed {theme.ACCENT}; border-radius:6px; "
            f"padding: 4px 8px; font-size: {int(14 * self._scale)}px;"
        )
        self.text_edit.setMinimumWidth(int(180 * self._scale))
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
            item = Item("text", self.state.color, self.state.width,
                        [self.text_pos], text=txt)
            item.font_size = 12 + self.state.width * 2
            self.items.append(item)
            self.update()

    def _compute_crop_rect(self):
        sel = self._selection()
        rect = QRect(sel) if sel else QRect()
        for it in self.items:
            if it.kind == "text":
                rect = rect.united(compute_text_rect(it))
            elif it.kind == "number":
                r = number_radius(it)
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
            draw_item(p, it)
        p.end()
        return result

    def _copy_to_clipboard(self):
        img = self._render_result()
        if img is None:
            self.close()
            return
        QGuiApplication.clipboard().setImage(img)
        self.close()

    def _upload_to_link(self):
        print("[Ctrl+L] Запущено", flush=True)
        img = self._render_result()
        if img is None:
            print("[Ctrl+L] _render_result вернул None", flush=True)
            self.close()
            return

        print(f"[Ctrl+L] Рендер: {img.width()}x{img.height()}", flush=True)
        self.hide()

        def worker():
            print("[Ctrl+L] Поток загрузки запущен", flush=True)
            try:
                url = upload_to_catbox(img)
                print(f"[Ctrl+L] Загрузка завершена, url={url}", flush=True)
            except Exception as e:
                import traceback
                print(f"[Ctrl+L] Исключение: {e}", flush=True)
                traceback.print_exc()
                url = None
            self.upload_done.emit(url)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(object)
    def _on_upload_done(self, url):
        print(f"[Ctrl+L] _on_upload_done url={url}", flush=True)
        if url:
            QGuiApplication.clipboard().setText(url)
            self._tray_msg(f"Ссылка скопирована:\n{url[:70]}…", True)
        else:
            self._tray_msg("Не удалось загрузить. Проверь интернет.", False)
        self.close()

    def _tray_msg(self, text, ok=True):
        try:
            app = QApplication.instance()
            if app is None:
                return
            for w in app.topLevelWidgets():
                if hasattr(w, "tray"):
                    w.tray.showMessage(
                        APP_NAME, text,
                        QSystemTrayIcon.Information if ok
                        else QSystemTrayIcon.Warning,
                        3000,
                    )
                    break
        except Exception:
            pass

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