import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.context import get_conn, Context, DB_PATH
from app.services.agent import init_tables as _agent_init
from app.routes.habit import _init_tables as _habit_init

router = APIRouter(prefix="/api/backup", tags=["backup"])

_VERSION = "1.8"


def _conn():
    """Return a connection with all tables guaranteed to exist."""
    c = get_conn(DB_PATH)
    _agent_init(c)
    _habit_init(c)
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL UNIQUE,
        address TEXT NOT NULL,
        chain TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coin TEXT NOT NULL,
        direction TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1)""")
    c.commit()
    return c


# ── Export ────────────────────────────────────────────────────────────────────

@router.get("/export")
def export_backup():
    c = _conn()

    notes = [
        {"id": r[0], "timestamp": r[1], "content": r[2]}
        for r in c.execute("SELECT id, timestamp, content FROM notes ORDER BY id").fetchall()
    ]
    habits = [
        {"id": r[0], "name": r[1], "freq_num": r[2], "freq_den": r[3],
         "position": r[4], "created_at": r[5]}
        for r in c.execute(
            "SELECT id, name, freq_num, freq_den, position, created_at "
            "FROM habits WHERE archived=0 ORDER BY position, id"
        ).fetchall()
    ]
    habit_entries = [
        {"habit_id": r[0], "date": r[1], "value": r[2]}
        for r in c.execute(
            "SELECT habit_id, date, value FROM habit_entries ORDER BY habit_id, date"
        ).fetchall()
    ]
    agents = [
        {"id": r[0], "name": r[1], "type": r[2],
         "config": json.loads(r[3]), "enabled": bool(r[4]), "interval_minutes": r[5]}
        for r in c.execute(
            "SELECT id, name, type, config, enabled, interval_minutes FROM agents ORDER BY id"
        ).fetchall()
    ]
    crypto_wallets = [
        {"id": r[0], "label": r[1], "address": r[2], "chain": r[3]}
        for r in c.execute("SELECT id, label, address, chain FROM crypto_wallets ORDER BY id").fetchall()
    ]
    crypto_alerts = [
        {"id": r[0], "coin": r[1], "direction": r[2], "price": r[3], "active": bool(r[4])}
        for r in c.execute(
            "SELECT id, coin, direction, price, active FROM crypto_alerts ORDER BY id"
        ).fetchall()
    ]
    c.close()

    ctx = Context.load()
    date_str = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "version": _VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "habits": habits,
        "habit_entries": habit_entries,
        "agents": agents,
        "crypto_wallets": crypto_wallets,
        "crypto_alerts": crypto_alerts,
        "skills": [{"name": k, "instructions": v} for k, v in ctx.skills.items()],
        "context": {
            "name": ctx.name,
            "memory": ctx.memory,
            "todo_list": ctx.todo_list,
            "vault_path": ctx.vault_path,
            "tools_enabled": ctx.tools_enabled,
            "chat_history": ctx.chat_history,
        },
        "settings": {
            "anthropic_model": ctx.anthropic_model,
            "groq_model": ctx.groq_model,
            "glm_model": ctx.glm_model,
        },
    }

    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="spark_backup_{date_str}.json"',
        },
    )


# ── Import ────────────────────────────────────────────────────────────────────

@router.post("/import")
def import_backup(backup: dict):
    if not backup.get("version"):
        raise HTTPException(400, "Fichier invalide — champ 'version' manquant.")

    c = _conn()
    try:
        if "notes" in backup:
            c.execute("DELETE FROM notes")
            for n in backup["notes"]:
                c.execute(
                    "INSERT INTO notes (id, timestamp, content) VALUES (?,?,?)",
                    (n["id"], n["timestamp"], n["content"]),
                )

        if "habits" in backup:
            c.execute("DELETE FROM habit_entries")
            c.execute("DELETE FROM habits")
            for h in backup["habits"]:
                c.execute(
                    "INSERT INTO habits (id, name, freq_num, freq_den, position, created_at) "
                    "VALUES (?,?,?,?,?,?)",
                    (h["id"], h["name"], h["freq_num"], h["freq_den"],
                     h.get("position", 0), h.get("created_at", "")),
                )
            for e in backup.get("habit_entries", []):
                c.execute(
                    "INSERT OR IGNORE INTO habit_entries (habit_id, date, value) VALUES (?,?,?)",
                    (e["habit_id"], e["date"], e.get("value", 1)),
                )

        if "agents" in backup:
            c.execute("DELETE FROM agents")
            for a in backup["agents"]:
                c.execute(
                    "INSERT INTO agents (id, name, type, config, enabled, interval_minutes) "
                    "VALUES (?,?,?,?,?,?)",
                    (a["id"], a["name"], a["type"], json.dumps(a.get("config", {})),
                     int(a.get("enabled", True)), a.get("interval_minutes", 60)),
                )

        if "crypto_wallets" in backup:
            c.execute("DELETE FROM crypto_wallets")
            for w in backup["crypto_wallets"]:
                c.execute(
                    "INSERT INTO crypto_wallets (id, label, address, chain) VALUES (?,?,?,?)",
                    (w["id"], w["label"], w["address"], w["chain"]),
                )

        if "crypto_alerts" in backup:
            c.execute("DELETE FROM crypto_alerts")
            for al in backup["crypto_alerts"]:
                c.execute(
                    "INSERT INTO crypto_alerts (id, coin, direction, price, active) VALUES (?,?,?,?,?)",
                    (al["id"], al["coin"], al["direction"], al["price"], int(al.get("active", True))),
                )

        c.commit()
    except Exception as exc:
        c.rollback()
        c.close()
        raise HTTPException(500, f"Erreur import BDD : {exc}")
    c.close()

    # Context (patch — never overwrite API keys)
    ctx = Context.load()
    if "context" in backup:
        cx = backup["context"]
        ctx.name         = cx.get("name", ctx.name)
        ctx.memory       = cx.get("memory", ctx.memory)
        ctx.todo_list    = cx.get("todo_list", ctx.todo_list)
        ctx.vault_path   = cx.get("vault_path", ctx.vault_path)
        ctx.tools_enabled = cx.get("tools_enabled", ctx.tools_enabled)
        ctx.chat_history = cx.get("chat_history", ctx.chat_history)
    if "skills" in backup:
        ctx.skills = {s["name"]: s["instructions"] for s in backup["skills"]}
    if "settings" in backup:
        s = backup["settings"]
        if s.get("anthropic_model"):
            ctx.anthropic_model = s["anthropic_model"]
        if s.get("groq_model"):
            ctx.groq_model = s["groq_model"]
        if s.get("glm_model"):
            ctx.glm_model = s["glm_model"]
    ctx.save()

    return {
        "ok": True,
        "imported": {
            "notes":         len(backup.get("notes", [])),
            "habits":        len(backup.get("habits", [])),
            "agents":        len(backup.get("agents", [])),
            "crypto_wallets": len(backup.get("crypto_wallets", [])),
            "crypto_alerts": len(backup.get("crypto_alerts", [])),
            "skills":        len(backup.get("skills", [])),
        },
    }
