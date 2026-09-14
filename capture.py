"""Захват экрана и определение активного окна."""

import sys
import time
from pathlib import Path

from PySide6.QtGui import QPixmap, QImage, QGuiApplication

import mss


_dxcam_instance = None

BROWSER_EXES = {
    "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe",
    "brave.exe", "vivaldi.exe", "yandex.exe", "browser.exe",
    "chromium.exe", "iexplore.exe", "safari.exe",
}


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


def _get_process_name_by_hwnd(hwnd) -> str:
    if sys.platform != "win32":
        return ""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return ""

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value
        )
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            ok = kernel32.QueryFullProcessImageNameW(
                h, 0, buf, ctypes.byref(size)
            )
            if ok:
                return Path(buf.value).name.lower()
        finally:
            kernel32.CloseHandle(h)
    except Exception as e:
        print("process name error:", e)
    return ""


def _has_multiple_monitors() -> bool:
    try:
        return len(QGuiApplication.screens()) > 1
    except Exception:
        return False


def capture_all_monitors() -> QPixmap:
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
        print("mss all-monitors error:", e)
    return None


def capture_primary_monitor() -> QPixmap:
    multi = _has_multiple_monitors()

    if not multi:
        cam = _get_dxcam()
        if cam is not None:
            try:
                frame = cam.grab()
                if frame is None:
                    time.sleep(0.05)
                    frame = cam.grab()
                if frame is not None:
                    h, w, _ = frame.shape
                    mid = frame[h // 2, w // 2]
                    if int(mid[0]) + int(mid[1]) + int(mid[2]) > 30:
                        img = QImage(
                            frame.data, w, h, w * 4,
                            QImage.Format_ARGB32,
                        ).copy()
                        return QPixmap.fromImage(img)
            except Exception as e:
                print("dxcam grab error:", e)

    try:
        with mss.mss() as sct:
            mons = sct.monitors
            if multi and len(mons) > 1:
                mon = mons[1]
            else:
                mon = mons[0]
            shot = sct.grab(mon)
            img = QImage(
                shot.raw, shot.width, shot.height,
                shot.width * 4, QImage.Format_RGB32,
            ).copy()
            return QPixmap.fromImage(img)
    except Exception as e:
        print("mss primary error:", e)

    return None


def is_fullscreen_window_active() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False

        proc = _get_process_name_by_hwnd(hwnd)
        if proc in BROWSER_EXES:
            return False

        cls_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buf, 256)
        cls = cls_buf.value.lower()
        if cls in ("progman", "workerw", "shell_traywnd"):
            return False

        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)

        if w < screen_w - 8 or h < screen_h - 8:
            return False

        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        if style & WS_CAPTION:
            return False

        return True
    except Exception as e:
        print("fullscreen check error:", e)
        return False
