import re as _re
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models import NoteCreate, NoteItem
from app.deps import load_ctx
from app.context import DB_PATH, get_conn

router = APIRouter(prefix="/api/notes", tags=["notes"])

_WIKILINK_RE = _re.compile(r'\[\[(.+?)\]\]')


@router.get("", response_model=list[NoteItem])
def list_notes():
    conn = get_conn(DB_PATH)
    rows = conn.execute("SELECT id, timestamp, content FROM notes ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return [NoteItem(id=r[0], timestamp=r[1], content=r[2]) for r in rows]


@router.post("", response_model=NoteItem)
def create_note(req: NoteCreate):
    conn = get_conn(DB_PATH)
    timestamp = datetime.now().isoformat(timespec="seconds")
    cursor = conn.execute("INSERT INTO notes (timestamp, content) VALUES (?, ?)", (timestamp, req.content))
    note_id = cursor.lastrowid
    conn.commit()

    ctx = load_ctx()
    if ctx.vault_path:
        _write_vault_note(ctx.vault_path, note_id, timestamp, req.content)

    conn.close()
    return NoteItem(id=note_id, timestamp=timestamp, content=req.content)


@router.delete("/{note_id}")
def delete_note(note_id: int):
    conn = get_conn(DB_PATH)
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Note #{note_id} introuvable.")
    return {"ok": True}


@router.post("/export")
def export_to_vault():
    ctx = load_ctx()
    if not ctx.vault_path:
        raise HTTPException(status_code=400, detail="Aucun vault configuré.")
    conn = get_conn(DB_PATH)
    rows = conn.execute("SELECT id, timestamp, content FROM notes ORDER BY id").fetchall()
    conn.close()
    if not rows:
        return {"message": "Aucune note à exporter."}
    Path(ctx.vault_path).expanduser().mkdir(parents=True, exist_ok=True)
    for note_id, timestamp, content in rows:
        _write_vault_note(ctx.vault_path, note_id, timestamp, content)
    return {"message": f"{len(rows)} note(s) exportée(s) vers : {ctx.vault_path}"}


@router.get("/graph")
def get_graph():
    ctx = load_ctx()
    if ctx.vault_path:
        vault = Path(ctx.vault_path).expanduser()
        if vault.is_dir():
            return _vault_graph(vault)
    return _db_graph()


def _slug(content: str) -> str:
    slug = content[:50].strip()
    slug = _re.sub(r'[\\/:*?"<>|]', "-", slug)
    slug = _re.sub(r"\s+", " ", slug).strip()
    return slug


def _write_vault_note(vault_path: str, note_id: int, timestamp: str, content: str) -> None:
    vault = Path(vault_path).expanduser()
    vault.mkdir(parents=True, exist_ok=True)
    ts_safe = timestamp.replace(":", "-")
    filename = f"{ts_safe} {_slug(content)}.md"
    frontmatter = f"---\nid: {note_id}\ncreated: {timestamp}\ntags:\n  - spark\n  - note\n---\n\n"
    (vault / filename).write_text(frontmatter + content)


def _vault_graph(vault: Path) -> dict:
    md_files = list(vault.glob("**/*.md"))
    name_to_path = {f.stem.lower(): f for f in md_files}
    nodes = [{"id": f.stem, "label": f.stem} for f in md_files]
    edges = []
    seen = set()
    for f in md_files:
        try:
            content = f.read_text(errors="ignore")
        except OSError:
            continue
        for m in _WIKILINK_RE.finditer(content):
            ref = m.group(1).split("|")[0].strip().lower()
            target = name_to_path.get(ref)
            if target and target.stem != f.stem:
                key = tuple(sorted([f.stem, target.stem]))
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": f.stem, "target": target.stem})
    return {"nodes": nodes, "edges": edges}


def _db_graph() -> dict:
    conn = get_conn(DB_PATH)
    rows = conn.execute("SELECT id, content FROM notes ORDER BY id").fetchall()
    conn.close()
    content_map = {r[0]: r[1] for r in rows}
    content_lower = {r[0]: r[1].lower() for r in rows}
    nodes = [{"id": str(r[0]), "label": r[1][:40].split("\n")[0]} for r in rows]
    edges = []
    seen = set()
    for note_id, content in content_map.items():
        for m in _WIKILINK_RE.finditer(content):
            ref = m.group(1).strip()
            try:
                target_id = int(ref)
            except ValueError:
                ref_lower = ref.lower()
                target_id = next(
                    (tid for tid, tc in content_lower.items() if tid != note_id and ref_lower in tc), None
                )
            if target_id and target_id in content_map and target_id != note_id:
                key = tuple(sorted([note_id, target_id]))
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": str(note_id), "target": str(target_id)})
    return {"nodes": nodes, "edges": edges}
