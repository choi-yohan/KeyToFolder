#!/usr/bin/env python3
"""Local image sorter. Run Python 3.10+ app.py; no web upload or cloud service."""
import argparse
from collections import OrderedDict
import errno
import hashlib
import io
import json
import mimetypes
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import webbrowser
import signal

ROOT = Path(__file__).resolve().parent
def settings_path():
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "KeyToFolder" / "settings.json"


SETTINGS = settings_path()
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp", ".tif", ".tiff", ".ico", ".svg"}
KEYS = "1234567890abcdefghijklmnopqrstuvwxyz" + "-=[];',./"
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.RLock()
THUMBNAILS = OrderedDict()
THUMB_LOCK = threading.Lock()
try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None


def within(path, folder):
    return path == folder or folder in path.parents


def fingerprint(path):
    s = path.stat()
    return [s.st_size, s.st_mtime_ns]


def move_file(source, destination):
    """Do not replace an existing destination, including a dangling symlink."""
    if source.is_symlink() or not source.is_file():
        raise ValueError("원본 파일이 없거나 링크 파일입니다. 목록을 새로고침해 주세요.")
    if os.path.lexists(destination):
        raise ValueError("목적지에 같은 이름의 파일이 있습니다. 덮어쓰지 않았습니다.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError as e:
        if e.errno == errno.EEXIST:
            raise ValueError("목적지에 같은 이름의 파일이 있습니다.") from e
        if e.errno not in {errno.EXDEV, errno.EPERM, errno.EOPNOTSUPP, errno.ENOTSUP}:
            raise
        # Exclusive creation protects files on another volume, too.
        with destination.open("xb") as output:
            try:
                with source.open("rb") as original:
                    shutil.copyfileobj(original, output, 1024 * 1024)
            except BaseException:
                output.close()
                destination.unlink(missing_ok=True)
                raise
        try:
            shutil.copystat(source, destination)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    try:
        source.unlink()
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


class State:
    def __init__(self):
        self.config = {"source": "", "recursive": False, "mappings": {}, "history": [], "language": None}
        self.files = []
        self.by_id = {}
        self.revision = 0
        self.index = 0
        self.total = 0
        existing_settings = SETTINGS
        if existing_settings.exists():
            try:
                saved = json.loads(existing_settings.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    self.config.update(saved)
            except (OSError, ValueError):
                pass
        mappings = self.config.get("mappings", {})
        if not isinstance(mappings, dict):
            mappings = {}
        if "\\" in mappings and "/" not in mappings:
            mappings["/"] = mappings["\\"]
        self.config["mappings"] = {
            k: v for k, v in mappings.items()
            if k in KEYS and isinstance(v, dict) and v.get("path")
        }
        if self.config.get("language") not in {"ko-KR", "en-US"}:
            self.config["language"] = None
        if not isinstance(self.config.get("history"), list):
            self.config["history"] = []
        if self.config["source"]:
            try:
                self.scan()
            except (OSError, ValueError):
                pass

    def save(self):
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        temporary = SETTINGS.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(SETTINGS)

    def scan(self):
        source = Path(self.config["source"]).expanduser().resolve()
        if not source.is_dir():
            raise ValueError("이미지가 있는 폴더를 선택해 주세요.")
        exclude = [Path(m["path"]).expanduser().resolve() for m in self.config["mappings"].values()]
        found = []
        for current, directories, names in os.walk(source, followlinks=False):
            here = Path(current)
            directories[:] = sorted([
                d for d in directories if not d.startswith(".")
                and not (here / d).is_symlink()
                and not any(within((here / d).resolve(), target) for target in exclude)
            ])
            for name in names:
                p = here / name
                if p.suffix.lower() in EXTENSIONS and not name.startswith(".") and not p.is_symlink():
                    found.append(p)
            if not self.config["recursive"]:
                break
        self.files = sorted(found, key=lambda p: str(p.relative_to(source)).casefold())
        self.by_id = {hashlib.sha256(str(p).encode()).hexdigest(): p for p in self.files}
        self.revision += 1
        self.index = 0
        self.total = len(self.files)

    def current(self):
        return self.files[self.index] if self.files else None

    def last_move(self):
        if not self.config["history"]:
            return None
        item = self.config["history"][-1]
        destination = Path(item["destination"])
        identity = hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
        try:
            available = (not destination.is_symlink() and destination.is_file()
                         and fingerprint(destination) == item["fingerprint"])
        except OSError:
            available = False
        return {"id": identity, "name": destination.name,
                "source": item["source"], "destination": item["destination"],
                "available": available}

    def summary(self):
        p = self.current()
        image = None
        if p:
            image = {"id": hashlib.sha256(str(p).encode()).hexdigest(), "name": p.name,
                     "relative": str(p.relative_to(Path(self.config["source"]).expanduser().resolve())),
                     "extension": p.suffix[1:].upper()}
        return {"source": self.config["source"], "recursive": self.config["recursive"],
                "language": self.config["language"],
                "revision": self.revision,
                "mappings": self.config["mappings"], "remaining": len(self.files),
                "position": self.index + 1 if p else 0, "total": self.total,
                "image": image, "canUndo": bool(self.config["history"]),
                "lastMove": self.last_move(),
                "pillow": Image is not None}

    def act(self, action, data):
        if action == "language":
            if data.get("language") not in {"ko-KR", "en-US"}:
                raise ValueError("Unsupported language. Choose Korean or English.")
            self.config["language"] = data["language"]
            self.save()
        elif action == "source":
            if not data.get("path", "").strip():
                raise ValueError("이미지가 있는 폴더를 선택해 주세요.")
            source = Path(data["path"]).expanduser().resolve()
            if not source.is_dir():
                raise ValueError("선택한 폴더를 찾을 수 없습니다.")
            self.config["source"] = str(source)
            self.config["recursive"] = bool(data.get("recursive", False))
            self.scan()
            self.save()
        elif action == "mappings":
            mapped = {}
            for key, item in data.get("mappings", {}).items():
                if key not in KEYS:
                    raise ValueError("지원하는 영문자, 숫자 또는 특수문자 키를 사용해 주세요.")
                if not item.get("path", "").strip():
                    continue
                p = Path(item["path"]).expanduser().resolve()
                if not p.is_dir():
                    raise ValueError(f"목적지 폴더를 찾을 수 없습니다: {p}")
                if self.config["source"] and p == Path(self.config["source"]).expanduser().resolve():
                    raise ValueError("원본 폴더와 목적지 폴더는 서로 달라야 합니다.")
                mapped[key] = {"path": str(p), "label": item.get("label", "").strip() or p.name}
            self.config["mappings"] = mapped
            if self.config["source"]:
                self.scan()
            self.save()
        elif action == "select":
            p = self.by_id.get(data.get("id"))
            if p is None:
                raise ValueError("이미지가 변경되었습니다. 화면을 확인하고 다시 눌러 주세요.")
            self.index = self.files.index(p)
        elif action == "navigate":
            if self.files:
                self.index = max(0, min(len(self.files) - 1, self.index + int(data.get("delta", 1))))
        elif action == "refresh":
            self.scan()
        elif action == "move":
            p = self.current()
            if not p:
                raise ValueError("분류할 이미지가 없습니다.")
            if data.get("id") != hashlib.sha256(str(p).encode()).hexdigest():
                raise ValueError("이미지가 변경되었습니다. 화면을 확인하고 다시 눌러 주세요.")
            mapping = self.config["mappings"].get(data.get("key"))
            if not mapping:
                raise ValueError("이 키에는 목적지 폴더가 지정되지 않았습니다.")
            destdir = Path(mapping["path"]).resolve()
            if not destdir.is_dir():
                raise ValueError("목적지 폴더에 접근할 수 없습니다.")
            destination = destdir / p.name
            self.config["history"].append({"source": str(p), "destination": str(destination),
                                           "fingerprint": fingerprint(p)})
            # Persist the undo path before the move so an interrupted save does not lose it.
            self.save()
            try:
                move_file(p, destination)
            except BaseException:
                self.config["history"].pop()
                self.save()
                raise
            self.files.pop(self.index)
            self.by_id.pop(hashlib.sha256(str(p).encode()).hexdigest(), None)
            self.revision += 1
            self.index = min(self.index, max(0, len(self.files) - 1))
            self.config["history"] = self.config["history"][-1000:]
            self.save()
        elif action == "undo":
            if not self.config["history"]:
                raise ValueError("되돌릴 이동이 없습니다.")
            item = self.config["history"][-1]
            p, dest = Path(item["destination"]), Path(item["source"])
            if not p.is_file():
                raise ValueError("이동한 파일을 찾을 수 없습니다. 목적지 폴더를 확인해 주세요.")
            if fingerprint(p) != item["fingerprint"]:
                raise ValueError("이동 후 파일이 수정되었습니다. 직접 확인해 주세요.")
            move_file(p, dest)
            self.config["history"].pop()
            if self.config["source"] and within(dest, Path(self.config["source"]).resolve()):
                self.scan()
                if dest in self.files:
                    self.index = self.files.index(dest)
            self.save()
        else:
            raise ValueError("알 수 없는 작업입니다.")
        return self.summary()


STATE = State()

EN_ERRORS = {
    "원본 파일이 없거나 링크 파일입니다. 목록을 새로고침해 주세요.": "The source file is missing or is a symbolic link. Refresh the list.",
    "목적지에 같은 이름의 파일이 있습니다. 덮어쓰지 않았습니다.": "A file with this name already exists in the destination. Nothing was overwritten.",
    "목적지에 같은 이름의 파일이 있습니다.": "A file with this name already exists in the destination.",
    "이미지가 있는 폴더를 선택해 주세요.": "Choose a folder containing images.",
    "선택한 폴더를 찾을 수 없습니다.": "The selected folder could not be found.",
    "지원하는 영문자, 숫자 또는 특수문자 키를 사용해 주세요.": "Use a supported letter, number, or punctuation key.",
    "원본 폴더와 목적지 폴더는 서로 달라야 합니다.": "The source and destination folders must be different.",
    "분류할 이미지가 없습니다.": "There are no images to sort.",
    "이미지가 변경되었습니다. 화면을 확인하고 다시 눌러 주세요.": "The image changed. Check the preview and press the key again.",
    "이 키에는 목적지 폴더가 지정되지 않았습니다.": "No destination folder is assigned to this key.",
    "목적지 폴더에 접근할 수 없습니다.": "The destination folder is not accessible.",
    "되돌릴 이동이 없습니다.": "There are no moves to undo.",
    "이동한 파일을 찾을 수 없습니다. 목적지 폴더를 확인해 주세요.": "The moved file could not be found. Check the destination folder.",
    "이동 후 파일이 수정되었습니다. 직접 확인해 주세요.": "The file was modified after the move. Please check it manually.",
    "알 수 없는 작업입니다.": "Unknown action.",
    "접근할 수 없습니다.": "Access denied.",
    "이미지가 변경되었습니다.": "The image changed.",
    "TIFF 미리보기에는 Pillow가 필요합니다.": "TIFF previews require Pillow.",
    "페이지를 찾을 수 없습니다.": "Page not found.",
    "요청이 너무 큽니다.": "The request is too large.",
    "폴더 선택 창을 열 수 없습니다. 폴더 경로를 직접 입력해 주세요.": "The folder picker could not be opened. Enter the folder path instead.",
}


def localized_error(message):
    if STATE.config["language"] == "ko-KR":
        return message
    prefix = "목적지 폴더를 찾을 수 없습니다: "
    if message.startswith(prefix):
        return "Destination folder not found: " + message[len(prefix):]
    return EN_ERRORS.get(message, message)


def thumbnail(path):
    """Small first-frame previews when Pillow is available; native browser fallback."""
    if Image is None or path.suffix.lower() == ".svg":
        return path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    key = (str(path), *fingerprint(path))
    with THUMB_LOCK:
        if key in THUMBNAILS:
            THUMBNAILS.move_to_end(key)
            return THUMBNAILS[key]
    try:
        with Image.open(path) as original:
            original.draft("RGB", (240, 240))
            preview = ImageOps.exif_transpose(original)
            preview.thumbnail((240, 240))
            output = io.BytesIO()
            preview.convert("RGBA" if "A" in preview.getbands() else "RGB").save(output, "PNG")
            result = output.getvalue(), "image/png"
    except (OSError, ValueError):
        return path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with THUMB_LOCK:
        THUMBNAILS[key] = result
        while len(THUMBNAILS) > 160:
            THUMBNAILS.popitem(last=False)
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, code, content, content_type="application/json; charset=utf-8", cache="no-store"):
        if isinstance(content, dict) and "error" in content:
            content = {**content, "error": localized_error(content["error"])}
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(content)

    def allowed(self, query=None):
        supplied = self.headers.get("X-Sorter-Token") or (query or {}).get("token", [""])[0]
        return secrets.compare_digest(supplied, TOKEN)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/":
            page = (ROOT / "ui.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)
            return self.send(200, page.encode(), "text/html; charset=utf-8")
        if not self.allowed(q):
            return self.send(403, {"error": "접근할 수 없습니다."})
        try:
            if u.path == "/undo-thumbnail":
                with LOCK:
                    last = STATE.last_move()
                    if not last or not last["available"] or q.get("id", [""])[0] != last["id"]:
                        return self.send(404, {"error": "이미지가 변경되었습니다."})
                    content, mime = thumbnail(Path(last["destination"]))
                return self.send(200, content, mime)
            if u.path == "/thumbnail":
                with LOCK:
                    p = STATE.by_id.get(q.get("id", [""])[0])
                if p is None:
                    return self.send(404, {"error": "이미지가 변경되었습니다."})
                content, mime = thumbnail(p)
                return self.send(200, content, mime, cache="private, max-age=3600")
            with LOCK:
                if u.path == "/api/state":
                    return self.send(200, STATE.summary())
                if u.path == "/api/files":
                    start = max(0, int(q.get("start", [0])[0]))
                    limit = max(1, min(200, int(q.get("limit", [60])[0])))
                    items = [{"id": hashlib.sha256(str(p).encode()).hexdigest(),
                              "name": p.name, "index": start + i}
                             for i, p in enumerate(STATE.files[start:start + limit])]
                    return self.send(200, {"revision": STATE.revision,
                                           "total": len(STATE.files), "items": items})
                if u.path == "/image":
                    p = STATE.current()
                    if not p or q.get("id", [""])[0] != hashlib.sha256(str(p).encode()).hexdigest():
                        return self.send(404, {"error": "이미지가 변경되었습니다."})
                    suffix = p.suffix.lower()
                    if suffix in {".tif", ".tiff"}:
                        if Image is None:
                            return self.send(415, {"error": "TIFF 미리보기에는 Pillow가 필요합니다."})
                        with Image.open(p) as original:
                            preview = ImageOps.exif_transpose(original)
                            preview.thumbnail((2560, 2560))
                            out = io.BytesIO()
                            preview.convert("RGBA" if "A" in preview.getbands() else "RGB").save(out, "PNG")
                            return self.send(200, out.getvalue(), "image/png")
                    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
                    return self.send(200, p.read_bytes(), mime)
            return self.send(404, {"error": "페이지를 찾을 수 없습니다."})
        except (OSError, ValueError) as e:
            return self.send(400, {"error": str(e)})

    def do_POST(self):
        if not self.allowed():
            return self.send(403, {"error": "접근할 수 없습니다."})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 65536:
                return self.send(413, {"error": "요청이 너무 큽니다."})
            data = json.loads(self.rfile.read(size) or b"{}")
            action = self.path.removeprefix("/api/")
            if action == "pick":
                return self.send(200, {"path": pick_folder()})
            with LOCK:
                result = STATE.act(action, data)
            return self.send(200, result)
        except (OSError, ValueError, KeyError, TypeError) as e:
            return self.send(400, {"error": str(e)})


def pick_folder():
    prompt = "폴더를 선택해 주세요" if STATE.config["language"] == "ko-KR" else "Choose a folder"
    if sys.platform == "darwin":
        result = subprocess.run(["osascript", "-e", f'POSIX path of (choose folder with prompt "{prompt}")'], capture_output=True, text=True)
        return result.stdout.strip() if not result.returncode else ""
    script = ('import tkinter as tk; from tkinter import filedialog; '
              'root=tk.Tk(); root.withdraw(); '
              f'path=filedialog.askdirectory(title="{prompt}"); '
              'root.destroy(); print(path)')
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                            encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if result.returncode:
        raise ValueError("폴더 선택 창을 열 수 없습니다. 폴더 경로를 직접 입력해 주세요.")
    return result.stdout.strip()


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required. Download it from https://www.python.org/downloads/")
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    # Let in-flight moves and settings writes finish before an app-window quit.
    server.daemon_threads = False
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown, daemon=True).start())
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"KeyToFolder: {url}", flush=True)
    print("종료하려면 이 터미널에서 Ctrl+C를 누르세요." if STATE.config["language"] == "ko-KR"
          else "Press Ctrl+C in this terminal to stop the app.", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        signal.signal(signal.SIGTERM, previous_sigterm)


if __name__ == "__main__":
    main()
