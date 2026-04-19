from fastapi import APIRouter, HTTPException
from app.models import AiRequest, AiResponse
from app.deps import load_ctx
from app.services.ai import run_turn, compact_history

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("", response_model=AiResponse)
def chat(req: AiRequest):
    ctx = load_ctx()
    try:
        reply, actions = run_turn(ctx, req.message.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AiResponse(reply=reply, actions=actions)


@router.get("/history")
def get_history():
    ctx = load_ctx()
    return {"history": ctx.chat_history}


@router.delete("/history")
def clear_history():
    ctx = load_ctx()
    ctx.chat_history = []
    ctx.save()
    return {"ok": True}


@router.post("/compact")
def compact():
    ctx = load_ctx()
    try:
        summary = compact_history(ctx)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": summary}
