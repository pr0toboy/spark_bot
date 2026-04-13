from dataclasses import dataclass, field
from pathlib import Path
import json
import sqlite3

DB_PATH = Path(__file__).parent / "data" / "spark.db"
DEFAULT_VAULT_PATH = Path(__file__).parent / "data" / "vault"


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
    api_key: str = ""
    groq_api_key: str = ""
    glm_api_key: str = ""
    anthropic_model: str = ""
    groq_model: str = ""
    glm_model: str = ""
    vault_path: str = ""
    tools_enabled: dict = field(default_factory=dict)
    skills: dict = field(default_factory=dict)

    def save(self, db_path: Path = DB_PATH) -> None:
        conn = get_conn(db_path)
        rows = [
            ("name", self.name),
            ("memory", self.memory),
            ("todo_list", json.dumps(self.todo_list, ensure_ascii=False)),
            ("chat_history", json.dumps(self.chat_history, ensure_ascii=False)),
            ("api_key", self.api_key),
            ("groq_api_key", self.groq_api_key),
            ("glm_api_key", self.glm_api_key),
            ("anthropic_model", self.anthropic_model),
            ("groq_model", self.groq_model),
            ("glm_model", self.glm_model),
            ("vault_path", self.vault_path),
            ("tools_enabled", json.dumps(self.tools_enabled)),
            ("skills", json.dumps(self.skills, ensure_ascii=False)),
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
            api_key=rows.get("api_key", ""),
            groq_api_key=rows.get("groq_api_key", ""),
            glm_api_key=rows.get("glm_api_key", ""),
            anthropic_model=rows.get("anthropic_model", ""),
            groq_model=rows.get("groq_model", ""),
            glm_model=rows.get("glm_model", ""),
            vault_path=rows.get("vault_path") or str(DEFAULT_VAULT_PATH),
            tools_enabled=json.loads(rows["tools_enabled"]) if rows.get("tools_enabled") else {"obsidian": True},
            skills=json.loads(rows.get("skills", "{}")),
        )
