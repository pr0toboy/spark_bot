from context import DB_PATH, get_conn
from result import Result
from pathlib import Path
from datetime import datetime


def handle(ctx, user_input: str, db_path: Path = DB_PATH) -> Result:
    sub = user_input.removeprefix("/note").strip()

    if sub == "list":
        return _list(db_path)
    if sub.startswith("delete "):
        return _delete(sub.removeprefix("delete ").strip(), db_path)
    if sub:
        return _add(sub, db_path)

    # mode interactif
    print("📝 Ta note :")
    content = input("› ").strip()
    if not content:
        return Result.error("❌ Note vide, rien enregistré.")
    return _add(content, db_path)


def _add(content: str, db_path: Path = DB_PATH) -> Result:
    conn = get_conn(db_path)
    conn.execute(
        "INSERT INTO notes (timestamp, content) VALUES (?, ?)",
        (datetime.now().isoformat(timespec="seconds"), content),
    )
    conn.commit()
    conn.close()
    return Result.success(f"📝 Note enregistrée : « {content} »")


def _list(db_path: Path = DB_PATH) -> Result:
    conn = get_conn(db_path)
    rows = conn.execute(
        "SELECT id, timestamp, content FROM notes ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()

    if not rows:
        return Result.success("📭 Aucune note enregistrée.")

    lines = ["📋 Tes notes :"]
    for note_id, ts, content in rows:
        lines.append(f"  [{note_id}] {ts}  {content}")
    return Result.success("\n".join(lines))


def _delete(id_str: str, db_path: Path = DB_PATH) -> Result:
    if not id_str.isdigit():
        return Result.error("❌ Usage : /note delete <id>")
    conn = get_conn(db_path)
    cursor = conn.execute("DELETE FROM notes WHERE id = ?", (int(id_str),))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return Result.error(f"❌ Note #{id_str} introuvable.")
    return Result.success(f"🗑️  Note #{id_str} supprimée.")
