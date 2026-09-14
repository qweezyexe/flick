"""Обёртка над pynput для глобальных хоткеев."""

from pynput import keyboard


class HotkeyManager:
    def __init__(self, mapping=None):
        self._mapping = dict(mapping or {})
        self._listener = None

    def start(self):
        self.stop()
        if not self._mapping:
            return
        try:
            self._listener = keyboard.GlobalHotKeys(self._mapping)
            self._listener.start()
        except Exception as e:
            print("Hotkey error:", e)

    def stop(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def update(self, mapping):
        self._mapping = dict(mapping)
        self.start()
