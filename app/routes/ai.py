from fastapi import APIRouter, HTTPException
from app.models import AiRequest, AiResponse
from app.deps import load_ctx
from commands import ai as ai_cmd

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("", response_model=AiResponse)
def chat(req: AiRequest):
    ctx = load_ctx()
    result = ai_cmd.handle(ctx, f"/ai {req.message}")
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.message)

    lines = result.message.splitlines()
    actions = [l for l in lines if not l.startswith("Spark :")]
    reply_lines = [l.removeprefix("Spark : ") for l in lines if l.startswith("Spark :")]
    return AiResponse(reply="\n".join(reply_lines), actions=actions)


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
    result = ai_cmd.handle(ctx, "/ai compact")
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.message)
    return {"message": result.message}
