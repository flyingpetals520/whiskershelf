"""
ws_common.py — shared helpers for the whiskershelf-tag CLI scripts.
Reuses the same shape as whiskershelf-search/scripts/ws_common.py but is
shipped separately so the two skills can be evolved independently.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_BASE = os.environ.get("WHISKERSHELF_BASE", "http://127.0.0.1:8080")
DEFAULT_TIMEOUT = float(os.environ.get("WHISKERSHELF_TIMEOUT", "10"))


class WhiskershelfError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


def check_server_reachable(base: str, timeout: float = 1.0) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(base)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, ""
    except (OSError, socket.timeout) as e:
        return False, f"{type(e).__name__}: {e}"


def request(method: str, path: str, *, base: str = DEFAULT_BASE,
            body: dict[str, Any] | None = None, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    url = base.rstrip("/") + path
    data: bytes | None = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raw = ""
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        try:
            err = json.loads(raw).get("error", raw) if raw else f"HTTP {e.code}"
        except json.JSONDecodeError:
            err = raw or f"HTTP {e.code}"
        raise WhiskershelfError(str(err), status=e.code, body=raw) from e
    except urllib.error.URLError as e:
        raise WhiskershelfError(
            f"Cannot reach WhiskerShelf at {base}. Is the app running? ({e.reason})"
        ) from e
    except (socket.timeout, TimeoutError) as e:
        raise WhiskershelfError(f"Timed out connecting to {base} ({e})") from e


def require_server(base: str) -> None:
    ok, why = check_server_reachable(base)
    if not ok:
        print(
            f"[whiskershelf-tag] Cannot reach WhiskerShelf at {base} ({why}).\n"
            f"  Ask the user to start the app (run 'python app.py' or double-click start.bat).",
            file=sys.stderr,
        )
        sys.exit(2)
