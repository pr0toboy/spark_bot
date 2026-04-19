import hashlib
import json
from datetime import datetime, timezone

from app.context import get_conn, DATA_DIR

_SA_PATH = DATA_DIR / "firebase-service-account.json"
_firebase_initialized = False


def init_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT    NOT NULL,
            type             TEXT    NOT NULL,
            config           TEXT    NOT NULL DEFAULT '{}',
            enabled          INTEGER NOT NULL DEFAULT 1,
            interval_minutes INTEGER NOT NULL DEFAULT 60,
            last_run         TEXT,
            created_at       TEXT    NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id  INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            timestamp TEXT    NOT NULL,
            status    TEXT    NOT NULL CHECK(status IN ('ok','error','empty')),
            summary   TEXT    NOT NULL DEFAULT '',
            items     TEXT    NOT NULL DEFAULT '[]'
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
    init_tables(conn)
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
    import feedparser
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
    import requests
    r = requests.get(url, timeout=15, allow_redirects=True)
    r.raise_for_status()
    h = hashlib.sha256(r.text.encode()).hexdigest()
    if prev_hash == h:
        return [], h
    return [{"title": "Changement détecté", "link": url, "published": "", "summary": r.text[:500]}], h


def _fetch_email(config: dict) -> tuple[list[dict], int]:
    import imaplib
    import email as email_lib
    from email.header import decode_header as dh

    host = config.get("imap_host", "imap.gmail.com")
    port = int(config.get("imap_port", 993))
    username = config.get("username", "")
    password = config.get("password", "")
    folder = config.get("folder", "INBOX")
    last_uid = int(config.get("last_uid", 0))

    def _decode(s) -> str:
        if not s:
            return ""
        parts = dh(s)
        result = []
        for part, enc in parts:
            if isinstance(part, bytes):
                result.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                result.append(str(part))
        return "".join(result)

    def _body(msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                    try:
                        return part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )[:500]
                    except Exception:
                        pass
        else:
            try:
                return msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )[:500]
            except Exception:
                pass
        return ""

    with imaplib.IMAP4_SSL(host, port) as imap:
        imap.login(username, password)
        imap.select(folder, readonly=True)
        if last_uid:
            _, data = imap.uid("search", None, f"UID {last_uid + 1}:*")
        else:
            _, data = imap.uid("search", None, "UNSEEN")
        raw_uids = data[0].split() if data[0] else []
        uids = [u for u in raw_uids if int(u) > last_uid]
        if not uids:
            return [], last_uid
        batch = uids[-20:]
        _, msg_data = imap.uid("fetch", b",".join(batch), "(RFC822)")
        results = []
        new_last_uid = last_uid
        for i in range(0, len(msg_data), 2):
            part = msg_data[i]
            if not part or not isinstance(part, tuple):
                continue
            uid_int = int(batch[i // 2])
            msg = email_lib.message_from_bytes(part[1])
            subject = _decode(msg.get("Subject", "(Sans objet)"))
            sender = _decode(msg.get("From", ""))
            date = msg.get("Date", "")
            body = _body(msg)
            results.append({
                "title": subject,
                "link": f"email:uid:{uid_int}",
                "published": date,
                "summary": f"De : {sender}\n{body[:400]}",
            })
            new_last_uid = max(new_last_uid, uid_int)
    return results, new_last_uid


def _get_api_key(conn) -> str:
    row = conn.execute("SELECT value FROM kv WHERE key='api_key'").fetchone()
    if not row:
        return ""
    try:
        val = json.loads(row[0])
        return val if isinstance(val, str) else ""
    except Exception:
        return ""


def _ai_filter(items: list[dict], ai_context: str, api_key: str) -> tuple[list[dict], str]:
    if not items or not ai_context.strip() or not api_key:
        return items, f"{len(items)} résultat(s)"
    try:
        import anthropic
        items_text = "\n".join([
            f"[{i + 1}] {item.get('title', '(sans titre)')} — {item.get('summary', '')[:300]}"
            for i, item in enumerate(items[:20])
        ])
        prompt = (
            f"Tu analyses du contenu récent pour un utilisateur.\n"
            f"Contexte de l'utilisateur : {ai_context}\n\n"
            f"Contenu :\n{items_text}\n\n"
            f"Y a-t-il des éléments pertinents ? Si oui, résumé concis (3-5 lignes). Si non, réponds : SKIP"
        )
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        result = resp.content[0].text.strip()
        if result.upper().startswith("SKIP"):
            return [], "Rien de pertinent (filtré par IA)"
        return items, result
    except Exception as e:
        return items, f"{len(items)} résultat(s) (filtre IA indisponible: {str(e)[:80]})"


def run_agent(agent_id: int) -> dict:
    conn = get_conn()
    init_tables(conn)
    row = conn.execute(
        "SELECT id, name, type, config FROM agents WHERE id=? AND enabled=1", (agent_id,)
    ).fetchone()
    if not row:
        conn.close()
        return {"status": "error", "summary": "Agent introuvable ou désactivé.", "items": []}

    aid, name, atype, config_str = row
    config = json.loads(config_str)
    items: list[dict] = []
    summary = ""
    status = "ok"
    config_changed = False

    try:
        if atype == "rss":
            items = _fetch_rss(config.get("url", ""), config.get("keywords", []))
        elif atype == "web":
            items, new_hash = _fetch_web(config.get("url", ""), config.get("last_hash"))
            if config.get("last_hash") != new_hash:
                config["last_hash"] = new_hash
                config_changed = True
        elif atype == "email":
            items, new_uid = _fetch_email(config)
            if new_uid != int(config.get("last_uid", 0)):
                config["last_uid"] = new_uid
                config_changed = True

        if config_changed:
            conn.execute("UPDATE agents SET config=? WHERE id=?", (json.dumps(config, ensure_ascii=False), aid))

        ai_context = config.get("ai_context", "").strip()
        if items and ai_context:
            api_key = _get_api_key(conn)
            items, summary = _ai_filter(items, ai_context, api_key)
        else:
            summary = f"{len(items)} résultat(s)" if items else "Rien de nouveau"

        status = "ok" if items else "empty"
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
