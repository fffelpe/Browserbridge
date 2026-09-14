import json
import sqlite3
import tempfile
import time
from pathlib import Path
import importlib.util

BRIDGE = Path(__file__).resolve().parents[1] / "native-host" / "bridge.py"
spec = importlib.util.spec_from_file_location("browserbridge_native", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def make_profile(root: Path):
    profile = root / "Default"
    profile.mkdir(parents=True)

    bookmarks = {
        "roots": {
            "bookmark_bar": {
                "type": "folder",
                "name": "Bookmarks bar",
                "children": [
                    {
                        "type": "folder",
                        "name": "Notícias",
                        "children": [
                            {
                                "type": "url",
                                "name": "Mozilla",
                                "url": "https://www.mozilla.org/"
                            }
                        ]
                    }
                ]
            }
        }
    }
    (profile / "Bookmarks").write_text(json.dumps(bookmarks), encoding="utf-8")

    db = sqlite3.connect(profile / "History")
    db.executescript("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY,
            url LONGVARCHAR,
            title LONGVARCHAR
        );
        CREATE TABLE visits (
            id INTEGER PRIMARY KEY,
            url INTEGER,
            visit_time INTEGER
        );
    """)

    now_ms = int(time.time() * 1000)
    chrome_time = bridge.chrome_time_from_unix_ms(now_ms)

    db.execute(
        "INSERT INTO urls(id, url, title) VALUES (1, ?, ?)",
        ("https://example.com/", "Example")
    )
    db.execute(
        "INSERT INTO visits(id, url, visit_time) VALUES (1, 1, ?)",
        (chrome_time,)
    )
    db.commit()
    db.close()

    return profile, now_ms


def test_readers():
    with tempfile.TemporaryDirectory() as td:
        profile, now_ms = make_profile(Path(td))
        bookmarks = bridge.read_bookmarks("chrome", profile)
        history = bridge.read_history("chrome", profile, now_ms - 10_000)

        assert len(bookmarks) == 1
        assert bookmarks[0]["url"] == "https://www.mozilla.org/"
        assert bookmarks[0]["folderPath"][-1] == "Notícias"

        assert len(history) == 1
        assert history[0]["url"] == "https://example.com/"
        assert abs(history[0]["visitTime"] - now_ms) < 2000


if __name__ == "__main__":
    test_readers()
    print("OK: leitores de favoritos e histórico passaram no teste.")
