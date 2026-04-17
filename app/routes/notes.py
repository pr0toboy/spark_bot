import re as _re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models import NoteCreate, NoteItem
from app.deps import load_ctx
from commands.note import handle as note_handle
from context import DB_PATH, get_conn

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("", response_model=list[NoteItem])
def list_notes():
    conn = get_conn(DB_PATH)
    rows = conn.execute(
        "SELECT id, timestamp, content FROM notes ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [NoteItem(id=r[0], timestamp=r[1], content=r[2]) for r in rows]


@router.post("", response_model=NoteItem)
def create_note(req: NoteCreate):
    ctx = load_ctx()
    result = note_handle(ctx, f"/note {req.content}")
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.message)
    conn = get_conn(DB_PATH)
    row = conn.execute(
        "SELECT id, timestamp, content FROM notes ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return NoteItem(id=row[0], timestamp=row[1], content=row[2])


@router.delete("/{note_id}")
def delete_note(note_id: int):
    ctx = load_ctx()
    result = note_handle(ctx, f"/note delete {note_id}")
    if not result.ok:
        raise HTTPException(status_code=404, detail=result.message)
    return {"ok": True}


@router.post("/export")
def export_to_vault():
    ctx = load_ctx()
    result = note_handle(ctx, "/note export")
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.message)
    return {"message": result.message}


_WIKILINK_RE = _re.compile(r'\[\[(.+?)\]\]')


@router.get("/graph")
def get_graph():
    ctx = load_ctx()
    if ctx.vault_path:
        vault = Path(ctx.vault_path).expanduser()
        if vault.is_dir():
            return _vault_graph(vault)
    return _db_graph()


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
                    (tid for tid, tc in content_lower.items()
                     if tid != note_id and ref_lower in tc),
                    None,
                )
            if target_id and target_id in content_map and target_id != note_id:
                key = tuple(sorted([note_id, target_id]))
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": str(note_id), "target": str(target_id)})

    return {"nodes": nodes, "edges": edges}
