import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models import AgentCreate, AgentItem, AgentRunItem, AgentUpdate
from commands.agent import _init_tables, run_agent
from context import get_conn

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _conn():
    c = get_conn()
    _init_tables(c)
    return c


def _to_item(row) -> AgentItem:
    config = json.loads(row[3])
    return AgentItem(
        id=row[0], name=row[1], type=row[2],
        url=config.get("url", ""),
        keywords=config.get("keywords", []),
        enabled=bool(row[4]),
        interval_minutes=row[5],
        last_run=row[6],
        ai_context=config.get("ai_context", ""),
        imap_host=config.get("imap_host", ""),
        imap_port=config.get("imap_port", 993),
        imap_username=config.get("username", ""),
        imap_folder=config.get("folder", "INBOX"),
    )


@router.post("/push/token")
def register_token(body: dict):
    token = (body.get("token") or "").strip()
    if not token:
        raise HTTPException(400, "Token manquant.")
    c = _conn()
    c.execute(
        "INSERT OR REPLACE INTO fcm_tokens (token, registered_at) VALUES (?,?)",
        (token, datetime.now(timezone.utc).isoformat()),
    )
    c.commit()
    c.close()
    return {"ok": True}


@router.get("", response_model=list[AgentItem])
def list_agents():
    c = _conn()
    rows = c.execute(
        "SELECT id, name, type, config, enabled, interval_minutes, last_run FROM agents ORDER BY id"
    ).fetchall()
    c.close()
    return [_to_item(r) for r in rows]


@router.post("", response_model=AgentItem, status_code=201)
def create_agent(req: AgentCreate):
    c = _conn()
    config: dict = {
        "url": req.url,
        "keywords": req.keywords,
        "ai_context": req.ai_context,
    }
    if req.type == "email":
        config.update({
            "imap_host": req.imap_host,
            "imap_port": req.imap_port,
            "username": req.imap_username,
            "password": req.imap_password,
            "folder": req.imap_folder,
        })
    c.execute(
        "INSERT INTO agents (name, type, config, enabled, interval_minutes, created_at) VALUES (?,?,?,1,?,?)",
        (req.name, req.type, json.dumps(config, ensure_ascii=False),
         req.interval_minutes, datetime.now(timezone.utc).isoformat()),
    )
    c.commit()
    aid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    row = c.execute(
        "SELECT id, name, type, config, enabled, interval_minutes, last_run FROM agents WHERE id=?",
        (aid,),
    ).fetchone()
    result = _to_item(row)
    c.close()
    return result


@router.patch("/{agent_id}", response_model=AgentItem)
def update_agent(agent_id: int, req: AgentUpdate):
    c = _conn()
    row = c.execute(
        "SELECT id, name, type, config, enabled, interval_minutes, last_run FROM agents WHERE id=?",
        (agent_id,),
    ).fetchone()
    if not row:
        c.close()
        raise HTTPException(404, f"Agent #{agent_id} introuvable.")
    config = json.loads(row[3])
    if req.url is not None:
        config["url"] = req.url
    if req.keywords is not None:
        config["keywords"] = req.keywords
    if req.ai_context is not None:
        config["ai_context"] = req.ai_context
    if req.imap_host is not None:
        config["imap_host"] = req.imap_host
    if req.imap_port is not None:
        config["imap_port"] = req.imap_port
    if req.imap_username is not None:
        config["username"] = req.imap_username
    if req.imap_password is not None:
        config["password"] = req.imap_password
    if req.imap_folder is not None:
        config["folder"] = req.imap_folder
    enabled = req.enabled if req.enabled is not None else bool(row[4])
    interval = req.interval_minutes if req.interval_minutes is not None else row[5]
    c.execute(
        "UPDATE agents SET config=?, enabled=?, interval_minutes=? WHERE id=?",
        (json.dumps(config, ensure_ascii=False), int(enabled), interval, agent_id),
    )
    c.commit()
    row = c.execute(
        "SELECT id, name, type, config, enabled, interval_minutes, last_run FROM agents WHERE id=?",
        (agent_id,),
    ).fetchone()
    result = _to_item(row)
    c.close()
    return result


@router.delete("/{agent_id}")
def delete_agent(agent_id: int):
    c = _conn()
    cur = c.execute("DELETE FROM agents WHERE id=?", (agent_id,))
    c.commit()
    c.close()
    if cur.rowcount == 0:
        raise HTTPException(404, f"Agent #{agent_id} introuvable.")
    return {"ok": True}


@router.post("/{agent_id}/run")
def trigger_run(agent_id: int):
    return run_agent(agent_id)


@router.get("/{agent_id}/runs", response_model=list[AgentRunItem])
def list_runs(agent_id: int):
    c = _conn()
    rows = c.execute(
        "SELECT id, agent_id, timestamp, status, summary, items FROM agent_runs "
        "WHERE agent_id=? ORDER BY id DESC LIMIT 50",
        (agent_id,),
    ).fetchall()
    c.close()
    return [
        AgentRunItem(
            id=r[0], agent_id=r[1], timestamp=r[2],
            status=r[3], summary=r[4], items=json.loads(r[5]),
        )
        for r in rows
    ]
