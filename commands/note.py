import re
from context import DB_PATH, get_conn
from result import Result
from pathlib import Path
from datetime import datetime


def handle(ctx, user_input: str, db_path: Path = DB_PATH) -> Result:
    sub = user_input.removeprefix("/note").strip()

    if sub == "list":
        return _list(db_path)
    if sub == "export":
        return _export(ctx, db_path)
    if sub == "vault":
        vault = ctx.vault_path or "(non configuré)"
        return Result.success(f"📂 Vault actuel : {vault}")
    if sub.startswith("vault "):
        return _set_vault(ctx, sub.removeprefix("vault ").strip())
    if sub.startswith("delete "):
        return _delete(sub.removeprefix("delete ").strip(), db_path)
    if sub:
        return _add(sub, ctx, db_path)

    # mode interactif
    print("📝 Ta note :")
    content = input("› ").strip()
    if not content:
        return Result.error("❌ Note vide, rien enregistré.")
    return _add(content, ctx, db_path)


def _slug(content: str) -> str:
    slug = content[:50].strip()
    slug = re.sub(r'[\\/:*?"<>|]', "-", slug)
    slug = re.sub(r"\s+", " ", slug).strip()
    return slug


def _write_vault_note(vault_path: str, note_id: int, timestamp: str, content: str) -> None:
    vault = Path(vault_path).expanduser()
    vault.mkdir(parents=True, exist_ok=True)

    ts_safe = timestamp.replace(":", "-")
    filename = f"{ts_safe} {_slug(content)}.md"
    note_file = vault / filename

    frontmatter = (
        "---\n"
        f"id: {note_id}\n"
        f"created: {timestamp}\n"
        "tags:\n"
        "  - spark\n"
        "  - note\n"
        "---\n\n"
    )
    note_file.write_text(frontmatter + content)


def _add(content: str, ctx=None, db_path: Path = DB_PATH) -> Result:
    conn = get_conn(db_path)
    timestamp = datetime.now().isoformat(timespec="seconds")
    cursor = conn.execute(
        "INSERT INTO notes (timestamp, content) VALUES (?, ?)",
        (timestamp, content),
    )
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()

    vault_hint = ""
    if ctx and ctx.vault_path:
        _write_vault_note(ctx.vault_path, note_id, timestamp, content)
        vault_hint = " (→ Vault)"

    return Result.success(f"📝 Note enregistrée{vault_hint} : « {content} »")


def _set_vault(ctx, path: str) -> Result:
    if not path:
        return Result.error("❌ Usage : /note vault <chemin>")
    ctx.vault_path = path
    ctx.save()
    return Result.success(f"📂 Vault configuré : {path}")


def _export(ctx, db_path: Path = DB_PATH) -> Result:
    if not ctx.vault_path:
        return Result.error(
            "❌ Aucun vault configuré. Lance d'abord : /note vault <chemin>"
        )
    conn = get_conn(db_path)
    rows = conn.execute(
        "SELECT id, timestamp, content FROM notes ORDER BY id"
    ).fetchall()
    conn.close()

    if not rows:
        return Result.success("📭 Aucune note à exporter.")

    Path(ctx.vault_path).expanduser().mkdir(parents=True, exist_ok=True)
    for note_id, timestamp, content in rows:
        _write_vault_note(ctx.vault_path, note_id, timestamp, content)

    return Result.success(
        f"✅ {len(rows)} note(s) exportée(s) vers : {ctx.vault_path}"
    )


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
