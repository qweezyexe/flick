"""Загрузка и сохранение конфига Flick."""

import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "flick" / "config.json"

DEFAULT_HOTKEYS = {
    "screenshot":       "<f7>",
    "fullscreen_copy":  "<f8>",
    "fullscreen_save":  "<f9>",
    "screenshot_link":  "<f10>",
}

HOTKEY_LABELS = {
    "screenshot":       "Сделать скриншот (открыть оверлей)",
    "fullscreen_copy":  "Полный экран \u2192 буфер",
    "fullscreen_save":  "Полный экран \u2192 файл",
    "screenshot_link":  "Скриншот \u2192 ссылка в буфер",
}

HOTKEY_ORDER = ["screenshot", "fullscreen_copy",
                "fullscreen_save", "screenshot_link"]

DEFAULTS = {
    "hotkeys": dict(DEFAULT_HOTKEYS),
    "color": "#a855f7",
    "thickness": 3,
    "number_size": 18,
    "save_dir": "",
    "auto_fullscreen_in_games": True,
}


def load():
    cfg = {
        "hotkeys": dict(DEFAULT_HOTKEYS),
        "color": DEFAULTS["color"],
        "thickness": DEFAULTS["thickness"],
        "number_size": DEFAULTS["number_size"],
        "save_dir": DEFAULTS["save_dir"],
        "auto_fullscreen_in_games": DEFAULTS["auto_fullscreen_in_games"],
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
    for k in ("color", "thickness", "number_size", "save_dir",
              "auto_fullscreen_in_games"):
        if k in data:
            cfg[k] = data[k]
    return cfg


def save(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )
