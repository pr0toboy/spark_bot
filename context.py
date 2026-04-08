from dataclasses import dataclass, field
from pathlib import Path
import json
import sqlite3

DB_PATH = Path(__file__).parent / "data" / "spark.db"


def get_conn(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)"
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            command   TEXT NOT NULL,
            detail    TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            content   TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


@dataclass
class Context:
    name: str = ""
    memory: str = ""
    todo_list: dict = field(default_factory=dict)
    chat_history: list = field(default_factory=list)

    def save(self, db_path: Path = DB_PATH) -> None:
        conn = get_conn(db_path)
        rows = [
            ("name", self.name),
            ("memory", self.memory),
            ("todo_list", json.dumps(self.todo_list, ensure_ascii=False)),
            ("chat_history", json.dumps(self.chat_history, ensure_ascii=False)),
        ]
        conn.executemany(
            "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", rows
        )
        conn.commit()
        conn.close()

    @classmethod
    def load(cls, db_path: Path = DB_PATH) -> "Context":
        conn = get_conn(db_path)
        rows = dict(conn.execute("SELECT key, value FROM kv").fetchall())
        conn.close()
        return cls(
            name=rows.get("name", ""),
            memory=rows.get("memory", ""),
            todo_list=json.loads(rows.get("todo_list", "{}")),
            chat_history=json.loads(rows.get("chat_history", "[]")),
        )
