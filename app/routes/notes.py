from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models import NoteCreate, NoteItem
from app.deps import load_ctx
from commands.note import _write_vault_note, handle as note_handle
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
    timestamp = datetime.now().isoformat(timespec="seconds")
    conn = get_conn(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO notes (timestamp, content) VALUES (?, ?)",
        (timestamp, req.content),
    )
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    if ctx.vault_path:
        _write_vault_note(ctx.vault_path, note_id, timestamp, req.content)
    return NoteItem(id=note_id, timestamp=timestamp, content=req.content)


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
