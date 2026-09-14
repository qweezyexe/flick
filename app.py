"""Главный класс приложения — трей, хоткеи, обработка событий."""

import sys
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox,
)
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtCore import Qt, QObject, Signal, Slot, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

import config
from state import (
    APP_NAME, APP_VERSION, APP_AUTHOR, SINGLE_INSTANCE_KEY,
    EditorState, pretty_hotkey,
)
from icons import make_icon, app_icon
from capture import (
    capture_primary_monitor, is_fullscreen_window_active, _get_dxcam,
)
from upload import upload_to_catbox
from hotkeys import HotkeyManager
from overlay import Overlay, resolve_save_dir, default_save_dir
from settings_window import SettingsWindow
import theme


class App(QObject):
    trigger_shot = Signal()
    trigger_full_copy = Signal()
    trigger_full_save = Signal()
    trigger_shot_link = Signal()
    link_uploaded = Signal(object)

    def __init__(self):
        super().__init__()

        self.cfg = config.load()
        self.state = EditorState(
            color=self.cfg.get("color", "#a855f7"),
            width=self.cfg.get("thickness", 3),
            number_size=self.cfg.get("number_size", 18),
        )

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationVersion(APP_VERSION)
        self.app.setOrganizationName(APP_AUTHOR)
        self.app.setWindowIcon(app_icon())
        self.app.setStyle("Fusion")

        QTimer.singleShot(100, _get_dxcam)

        if self._is_already_running():
            QMessageBox.information(
                None, APP_NAME,
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

        self.hotkeys = HotkeyManager({})
        self._start_hotkeys()

        self.trigger_shot.connect(self._take_shot, Qt.QueuedConnection)
        self.trigger_full_copy.connect(self._fullscreen_copy,
                                       Qt.QueuedConnection)
        self.trigger_full_save.connect(self._fullscreen_save,
                                       Qt.QueuedConnection)
        self.trigger_shot_link.connect(self._take_shot_link,
                                       Qt.QueuedConnection)
        self.link_uploaded.connect(self._on_link_uploaded,
                                   Qt.QueuedConnection)

        self.overlay = None
        self.settings_win = None

    def _is_already_running(self) -> bool:
        sock = QLocalSocket()
        sock.connectToServer(SINGLE_INSTANCE_KEY)
        if sock.waitForConnected(300):
            sock.write(b"show")
            sock.flush()
            sock.waitForBytesWritten(200)
            sock.disconnectFromServer()
            return True
        return False

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
        menu.setStyleSheet(theme.TRAY_MENU_QSS)

        a_shot = QAction(
            make_icon("select", theme.TEXT, 14),
            f"Сделать скрин ({self._hk('screenshot')})", menu
        )
        a_shot.triggered.connect(self._take_shot)
        menu.addAction(a_shot)

        a_fc = QAction(
            make_icon("copy", theme.TEXT, 14),
            f"Полный экран → буфер ({self._hk('fullscreen_copy')})", menu
        )
        a_fc.triggered.connect(self._fullscreen_copy)
        menu.addAction(a_fc)

        a_fs = QAction(
            make_icon("save", theme.TEXT, 14),
            f"Полный экран → файл ({self._hk('fullscreen_save')})", menu
        )
        a_fs.triggered.connect(self._fullscreen_save)
        menu.addAction(a_fs)

        a_link = QAction(
            make_icon("link", theme.TEXT, 14),
            f"Скрин → ссылка ({self._hk('screenshot_link')})", menu
        )
        a_link.triggered.connect(self._take_shot_link)
        menu.addAction(a_link)

        menu.addSeparator()

        a_set = QAction(make_icon("settings", theme.TEXT, 14),
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
            f"<td style='color:#9d95b0;'>"
            f"{config.HOTKEY_LABELS[k]}</td></tr>"
            for k in config.HOTKEY_ORDER
        )
        QMessageBox.information(
            None, f"О {APP_NAME}",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            f"<p>Скриншоты и аннотации</p>"
            f"<p style='color:#9d95b0;'>by <b>{APP_AUTHOR}</b></p>"
            f"<table>{rows}</table>"
            f"<p style='margin-top:10px;'>"
            f"Папка сохранения: "
            f"<b>{resolve_save_dir(self.cfg)}</b></p>",
        )

    def _start_hotkeys(self):
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
        if hk.get("screenshot_link"):
            mapping[hk["screenshot_link"]] = (
                lambda: self.trigger_shot_link.emit()
            )
        self.hotkeys.update(mapping)

    @Slot()
    def _take_shot(self):
        if self.overlay and self.overlay.isVisible():
            return

        if self.cfg.get("auto_fullscreen_in_games", True) \
                and is_fullscreen_window_active():
            pm = capture_primary_monitor()
            if pm is not None:
                QGuiApplication.clipboard().setImage(pm.toImage())
                self.tray.showMessage(
                    APP_NAME,
                    "Полный экран скопирован в буфер (режим игры)",
                    QSystemTrayIcon.Information, 1800,
                )
                return

        self.overlay = Overlay(self.cfg, self.state)
        self.overlay.closed.connect(self._on_overlay_closed)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()
        self.overlay.setFocus(Qt.ActiveWindowFocusReason)

    @Slot()
    def _fullscreen_copy(self):
        pm = capture_primary_monitor()
        if pm is None:
            self.tray.showMessage(
                APP_NAME, "Не удалось захватить экран",
                QSystemTrayIcon.Warning, 2000,
            )
            return
        QGuiApplication.clipboard().setImage(pm.toImage())
        self.tray.showMessage(
            APP_NAME, "Основной монитор скопирован в буфер",
            QSystemTrayIcon.Information, 1800,
        )

    @Slot()
    def _fullscreen_save(self):
        pm = capture_primary_monitor()
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

    @Slot()
    def _take_shot_link(self):
        print("[F10] Запущено", flush=True)

        pm = capture_primary_monitor()
        if pm is None:
            print("[F10] capture_primary_monitor вернул None", flush=True)
            self.tray.showMessage(
                APP_NAME, "Не удалось захватить экран",
                QSystemTrayIcon.Warning, 2000,
            )
            return

        print(f"[F10] Скрин сделан: {pm.width()}x{pm.height()}", flush=True)

        self.tray.showMessage(
            APP_NAME, "Загружаю скрин на сервер…",
            QSystemTrayIcon.Information, 1500,
        )
        print("[F10] Уведомление 'Загружаю...' показано", flush=True)

        image = pm.toImage()

        def worker():
            print("[F10] Поток загрузки запущен", flush=True)
            try:
                url = upload_to_catbox(image)
                print(f"[F10] Загрузка завершена, url={url}", flush=True)
            except Exception as e:
                import traceback
                print(f"[F10] Исключение при загрузке: {e}", flush=True)
                traceback.print_exc()
                url = None
            self.link_uploaded.emit(url)
            print("[F10] Сигнал link_uploaded отправлен", flush=True)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(object)
    def _on_link_uploaded(self, url):
        print(f"[F10] _on_link_uploaded получен url={url}", flush=True)
        if url is None:
            print("[F10] Загрузка не удалась — показываю ошибку", flush=True)
            self.tray.showMessage(
                APP_NAME,
                "Не удалось загрузить. Проверь интернет.",
                QSystemTrayIcon.Warning, 2500,
            )
            return
        QGuiApplication.clipboard().setText(url)
        print(f"[F10] URL скопирован в буфер: {url}", flush=True)
        self.tray.showMessage(
            APP_NAME,
            f"Ссылка скопирована:\n{url[:70]}…",
            QSystemTrayIcon.Information, 3000,
        )

    def _on_overlay_closed(self):
        self.overlay = None
        config.save(self.cfg)

    def _open_settings(self):
        self.settings_win = SettingsWindow(self.cfg)
        self.settings_win.saved.connect(self._on_settings_saved)
        self.settings_win.show()
        self.settings_win.raise_()
        self.settings_win.activateWindow()

    def _on_settings_saved(self, cfg):
        self.cfg = cfg
        self.state.color = cfg.get("color", self.state.color)
        self.state.width = cfg.get("thickness", self.state.width)
        self.state.number_size = cfg.get("number_size",
                                         self.state.number_size)
        self._start_hotkeys()
        self._build_menu()
        self.tray.showMessage(
            APP_NAME,
            f"Настройки сохранены.\n"
            f"Скрин: {self._hk('screenshot')}   "
            f"Буфер: {self._hk('fullscreen_copy')}   "
            f"Файл: {self._hk('fullscreen_save')}   "
            f"Ссылка: {self._hk('screenshot_link')}",
            QSystemTrayIcon.Information, 2500,
        )

    def run(self):
        return self.app.exec()