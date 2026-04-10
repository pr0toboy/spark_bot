from fastapi import APIRouter, HTTPException
from app.models import AiRequest, AiResponse
from app.deps import load_ctx
from commands.ai import chat_api, handle as ai_handle

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("", response_model=AiResponse)
def chat(req: AiRequest):
    ctx = load_ctx()
    try:
        reply, actions = chat_api(ctx, req.message)
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
    result = ai_handle(ctx, "/ai compact")
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.message)
    return {"message": result.message}
