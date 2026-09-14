#!/usr/bin/env python3
"""
BrowserBridge native host.

Protocol:
Firefox Native Messaging sends/receives:
  [4-byte little-endian length][UTF-8 JSON payload]

This host reads only bookmark/history databases from supported Chromium
profiles. It does not read passwords, cookies, form data, or tokens.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

HOST_VERSION = "0.1.0"
CHROMIUM_EPOCH_OFFSET_US = 11_644_473_600_000_000

SOURCE_LABELS = {
    "chrome": "Google Chrome",
    "edge": "Microsoft Edge",
    "brave": "Brave",
}


def send_message(message: Dict[str, Any]) -> None:
    raw = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(raw)))
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def read_message() -> Dict[str, Any]:
    header = sys.stdin.buffer.read(4)
    if len(header) != 4:
        raise EOFError("Mensagem nativa sem cabeçalho completo.")

    length = struct.unpack("<I", header)[0]
    if length > 64 * 1024 * 1024:
        raise ValueError("Mensagem recebida é grande demais.")

    payload = sys.stdin.buffer.read(length)
    if len(payload) != length:
        raise EOFError("Mensagem nativa incompleta.")

    return json.loads(payload.decode("utf-8"))


def chromium_roots() -> Dict[str, List[Path]]:
    home = Path.home()

    if sys.platform.startswith("win"):
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return {
            "chrome": [local / "Google" / "Chrome" / "User Data"],
            "edge": [local / "Microsoft" / "Edge" / "User Data"],
            "brave": [local / "BraveSoftware" / "Brave-Browser" / "User Data"],
        }

    if sys.platform == "darwin":
        app = home / "Library" / "Application Support"
        return {
            "chrome": [app / "Google" / "Chrome"],
            "edge": [app / "Microsoft Edge"],
            "brave": [app / "BraveSoftware" / "Brave-Browser"],
        }

    # Linux
    config = home / ".config"
    return {
        "chrome": [
            config / "google-chrome",
            config / "google-chrome-beta",
            config / "chromium",
        ],
        "edge": [
            config / "microsoft-edge",
            config / "microsoft-edge-beta",
        ],
        "brave": [
            config / "BraveSoftware" / "Brave-Browser",
        ],
    }


def profile_dirs(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []

    candidates: List[Path] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue

        if child.name == "Default" or child.name.startswith("Profile "):
            if (child / "Bookmarks").exists() or (child / "History").exists():
                candidates.append(child)

    # Alguns builds/perfis podem manter os arquivos diretamente na raiz.
    if (root / "Bookmarks").exists() or (root / "History").exists():
        candidates.append(root)

    return sorted(candidates, key=lambda p: (p.name != "Default", p.name))


def detect_sources() -> List[str]:
    roots = chromium_roots()
    detected = []

    for source, source_roots in roots.items():
        if any(list(profile_dirs(root)) for root in source_roots):
            detected.append(SOURCE_LABELS[source])

    return detected


def walk_bookmark_node(
    node: Dict[str, Any],
    source: str,
    profile_name: str,
    path: List[str],
    out: List[Dict[str, Any]],
) -> None:
    node_type = node.get("type")

    if node_type == "url":
        url = node.get("url")
        if not url:
            return

        out.append({
            "source": source,
            "sourceLabel": f"{SOURCE_LABELS[source]} — {profile_name}",
            "title": node.get("name") or url,
            "url": url,
            "folderPath": path,
        })
        return

    if node_type == "folder":
        name = node.get("name")
        next_path = path + ([name] if name else [])
        for child in node.get("children", []):
            walk_bookmark_node(child, source, profile_name, next_path, out)


def read_bookmarks(source: str, profile: Path) -> List[Dict[str, Any]]:
    path = profile / "Bookmarks"
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    roots = data.get("roots", {})
    out: List[Dict[str, Any]] = []

    root_labels = {
        "bookmark_bar": "Barra de favoritos",
        "other": "Outros favoritos",
        "synced": "Favoritos sincronizados",
    }

    for root_key, node in roots.items():
        if not isinstance(node, dict):
            continue

        label = root_labels.get(root_key, node.get("name") or root_key)
        for child in node.get("children", []):
            walk_bookmark_node(
                child,
                source,
                profile.name,
                [label],
                out,
            )

    return out


def chrome_time_from_unix_ms(unix_ms: int) -> int:
    return int(unix_ms) * 1000 + CHROMIUM_EPOCH_OFFSET_US


def unix_ms_from_chrome_time(chrome_us: int) -> int:
    return max(0, int((int(chrome_us) - CHROMIUM_EPOCH_OFFSET_US) / 1000))


def read_history(
    source: str,
    profile: Path,
    since_ms: int,
    limit: int = 20_000,
) -> List[Dict[str, Any]]:
    db_path = profile / "History"
    if not db_path.exists():
        return []

    # Chromium mantém o SQLite aberto. Copiar evita erros de lock.
    with tempfile.TemporaryDirectory(prefix="browserbridge-") as tmpdir:
        copied = Path(tmpdir) / "History"
        shutil.copy2(db_path, copied)

        conn = sqlite3.connect(f"file:{copied}?mode=ro", uri=True)
        try:
            since_chrome = chrome_time_from_unix_ms(since_ms)
            rows = conn.execute(
                """
                SELECT
                    urls.url,
                    urls.title,
                    visits.visit_time
                FROM visits
                JOIN urls ON urls.id = visits.url
                WHERE visits.visit_time >= ?
                  AND urls.url IS NOT NULL
                  AND urls.url != ''
                ORDER BY visits.visit_time ASC
                LIMIT ?
                """,
                (since_chrome, int(limit)),
            ).fetchall()
        finally:
            conn.close()

    return [
        {
            "source": source,
            "sourceLabel": f"{SOURCE_LABELS[source]} — {profile.name}",
            "url": url,
            "title": title or url,
            "visitTime": unix_ms_from_chrome_time(visit_time),
        }
        for url, title, visit_time in rows
        if url
    ]


def perform_sync(request: Dict[str, Any]) -> Dict[str, Any]:
    roots = chromium_roots()
    requested_sources = [
        source for source in request.get("sources", [])
        if source in SOURCE_LABELS
    ]

    include_bookmarks = bool(request.get("includeBookmarks", True))
    include_history = bool(request.get("includeHistory", True))
    history_since = int(request.get("historySince", 0) or 0)

    bookmarks: List[Dict[str, Any]] = []
    history: List[Dict[str, Any]] = []
    detected: List[str] = []
    warnings: List[str] = []

    for source in requested_sources:
        source_found = False

        for source_root in roots[source]:
            for profile in profile_dirs(source_root):
                source_found = True
                label = f"{SOURCE_LABELS[source]} ({profile.name})"
                if label not in detected:
                    detected.append(label)

                if include_bookmarks:
                    try:
                        bookmarks.extend(read_bookmarks(source, profile))
                    except Exception as exc:
                        warnings.append(
                            f"Favoritos: falha ao ler {label}: {exc}"
                        )

                if include_history:
                    try:
                        history.extend(
                            read_history(source, profile, history_since)
                        )
                    except Exception as exc:
                        warnings.append(
                            f"Histórico: falha ao ler {label}: {exc}"
                        )

        if not source_found:
            warnings.append(
                f"{SOURCE_LABELS[source]} não foi localizado neste computador."
            )

    return {
        "ok": True,
        "hostVersion": HOST_VERSION,
        "detected": detected,
        "bookmarks": bookmarks,
        "history": history,
        "warnings": warnings,
    }


def main() -> None:
    try:
        request = read_message()
        action = request.get("action")

        if action == "detect":
            send_message({
                "ok": True,
                "hostVersion": HOST_VERSION,
                "detected": detect_sources(),
            })
            return

        if action == "sync":
            send_message(perform_sync(request))
            return

        send_message({
            "ok": False,
            "error": f"Ação desconhecida: {action!r}",
        })
    except Exception as exc:
        send_message({
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        })


if __name__ == "__main__":
    main()
