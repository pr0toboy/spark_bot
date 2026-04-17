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
