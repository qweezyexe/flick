"""Загрузка изображения на бесплатный хостинг.

Пробует несколько сервисов по очереди, пока один не ответит.
С нормальными HTTP-заголовками, чтобы хостинги не блокировали.
"""

import tempfile
from pathlib import Path

import requests
from PySide6.QtGui import QImage


# Браузерные заголовки — иначе многие хостинги отдают 403/412
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _try_litterbox(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            resp = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                headers=HEADERS,
                data={"reqtype": "fileupload", "time": "24h"},
                files={"fileToUpload": f},
                timeout=30,
            )
        if resp.status_code == 200:
            url = resp.text.strip()
            if url.startswith("http"):
                return url
            print("litterbox unexpected:", url[:200])
        else:
            print("litterbox HTTP:", resp.status_code)
    except Exception as e:
        print("litterbox error:", e)
    return None


def _try_catbox(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            resp = requests.post(
                "https://catbox.moe/user/api.php",
                headers=HEADERS,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=30,
            )
        if resp.status_code == 200:
            url = resp.text.strip()
            if url.startswith("http"):
                return url
            print("catbox unexpected:", url[:200])
        else:
            print("catbox HTTP:", resp.status_code)
    except Exception as e:
        print("catbox error:", e)
    return None


def _try_uguu(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            resp = requests.post(
                "https://uguu.se/upload.php",
                headers=HEADERS,
                files={"files[]": f},
                timeout=30,
            )
        if resp.status_code == 200:
            data = resp.json()
            files = data.get("files") or []
            if files:
                url = files[0].get("url", "")
                if url.startswith("http"):
                    return url
            print("uguu unexpected:", str(data)[:200])
        else:
            print("uguu HTTP:", resp.status_code)
    except Exception as e:
        print("uguu error:", e)
    return None


def _try_tmpfiles(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            resp = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                headers=HEADERS,
                files={"file": f},
                timeout=30,
            )
        if resp.status_code == 200:
            data = resp.json()
            url = data.get("data", {}).get("url", "")
            if url:
                direct = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                return direct
        else:
            print("tmpfiles HTTP:", resp.status_code)
    except Exception as e:
        print("tmpfiles error:", e)
    return None


def upload_to_catbox(image: QImage) -> str | None:
    """Пробует все хостинги по очереди, возвращает первую успешную ссылку."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        if not image.save(tmp_path, "PNG"):
            return None

        for fn in (_try_catbox, _try_litterbox, _try_uguu, _try_tmpfiles):
            url = fn(tmp_path)
            if url:
                return url

    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
    return None