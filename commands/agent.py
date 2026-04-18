import hashlib
import json
import feedparser
import requests
from datetime import datetime, timezone

from context import get_conn, DATA_DIR

_SA_PATH = DATA_DIR / "firebase-service-account.json"
_firebase_initialized = False


def _init_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT    NOT NULL,
            type             TEXT    NOT NULL CHECK(type IN ('rss','web')),
            config           TEXT    NOT NULL DEFAULT '{}',
            enabled          INTEGER NOT NULL DEFAULT 1,
            interval_minutes INTEGER NOT NULL DEFAULT 60,
            last_run         TEXT,
            created_at       TEXT    NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            timestamp TEXT   NOT NULL,
            status   TEXT    NOT NULL CHECK(status IN ('ok','error','empty')),
            summary  TEXT    NOT NULL DEFAULT '',
            items    TEXT    NOT NULL DEFAULT '[]'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fcm_tokens (
            token         TEXT PRIMARY KEY,
            registered_at TEXT NOT NULL
        )
    """)
    conn.commit()


def _get_firebase():
    global _firebase_initialized
    if not _SA_PATH.exists():
        return None
    import firebase_admin
    from firebase_admin import credentials
    if not _firebase_initialized:
        cred = credentials.Certificate(str(_SA_PATH))
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
    return firebase_admin


def send_push(title: str, body: str) -> int:
    fb = _get_firebase()
    if fb is None:
        return 0
    from firebase_admin import messaging
    conn = get_conn()
    _init_tables(conn)
    tokens = [r[0] for r in conn.execute("SELECT token FROM fcm_tokens").fetchall()]
    conn.close()
    if not tokens:
        return 0
    resp = messaging.send_each_for_multicast(
        messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=tokens,
        )
    )
    return resp.success_count


def _fetch_rss(url: str, keywords: list[str]) -> list[dict]:
    feed = feedparser.parse(url)
    kw = [k.lower() for k in keywords]
    results = []
    for entry in feed.entries[:30]:
        text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
        if not kw or any(k in text for k in kw):
            results.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:400],
            })
    return results


def _fetch_web(url: str, prev_hash: str | None) -> tuple[list[dict], str]:
    r = requests.get(url, timeout=15, allow_redirects=True)
    r.raise_for_status()
    h = hashlib.sha256(r.text.encode()).hexdigest()
    if prev_hash == h:
        return [], h
    return [{"title": "Changement détecté", "link": url, "published": "", "summary": r.text[:500]}], h


def run_agent(agent_id: int) -> dict:
    conn = get_conn()
    _init_tables(conn)
    row = conn.execute(
        "SELECT id, name, type, config FROM agents WHERE id=? AND enabled=1",
        (agent_id,),
    ).fetchone()
    if not row:
        conn.close()
        return {"status": "error", "summary": "Agent introuvable ou désactivé.", "items": []}

    aid, name, atype, config_str = row
    config = json.loads(config_str)

    try:
        if atype == "rss":
            items = _fetch_rss(config.get("url", ""), config.get("keywords", []))
        elif atype == "web":
            items, new_hash = _fetch_web(config.get("url", ""), config.get("last_hash"))
            config["last_hash"] = new_hash
            conn.execute(
                "UPDATE agents SET config=? WHERE id=?",
                (json.dumps(config, ensure_ascii=False), aid),
            )
        else:
            items = []
        status = "ok" if items else "empty"
        summary = f"{len(items)} résultat(s)" if items else "Rien de nouveau"
    except Exception as e:
        status, summary, items = "error", str(e)[:200], []

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO agent_runs (agent_id, timestamp, status, summary, items) VALUES (?,?,?,?,?)",
        (aid, now, status, summary, json.dumps(items, ensure_ascii=False)),
    )
    conn.execute("UPDATE agents SET last_run=? WHERE id=?", (now, aid))
    conn.commit()
    conn.close()

    if items:
        send_push(f"Agent · {name}", summary)

    return {"status": status, "summary": summary, "items": items}
