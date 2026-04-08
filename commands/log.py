from context import DB_PATH, get_conn
from result import Result
from pathlib import Path
from datetime import datetime


def add_entry(command: str, detail: str = "", db_path: Path = DB_PATH) -> None:
    """Appelé par bot.py après chaque commande pour journaliser."""
    conn = get_conn(db_path)
    conn.execute(
        "INSERT INTO logs (timestamp, command, detail) VALUES (?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), command, detail),
    )
    conn.commit()
    conn.close()


def handle(ctx, user_input: str, db_path: Path = DB_PATH) -> Result:
    sub = user_input.removeprefix("/log").strip()
    if sub == "clear":
        return _clear(db_path)
    return _show(sub, db_path)


def _show(filter_cmd: str = "", db_path: Path = DB_PATH) -> Result:
    conn = get_conn(db_path)
    if filter_cmd:
        rows = conn.execute(
            "SELECT timestamp, command, detail FROM logs WHERE command = ? ORDER BY id DESC LIMIT 50",
            (f"/{filter_cmd.lstrip('/')}",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT timestamp, command, detail FROM logs ORDER BY id DESC LIMIT 50"
        ).fetchall()
    conn.close()

    if not rows:
        return Result.success("📭 Aucune entrée dans le journal.")

    lines = ["📋 Journal des actions (50 dernières) :"]
    for ts, cmd, detail in rows:
        line = f"  [{ts}] {cmd}"
        if detail:
            line += f"  — {detail}"
        lines.append(line)
    return Result.success("\n".join(lines))


def _clear(db_path: Path = DB_PATH) -> Result:
    conn = get_conn(db_path)
    conn.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    return Result.success("🗑️  Journal effacé.")
