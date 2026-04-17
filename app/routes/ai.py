from fastapi import APIRouter, HTTPException
from app.models import AiRequest, AiResponse
from app.deps import load_ctx
from commands.ai import chat_api, handle as ai_handle
from commands import (
    remember, recall, todo, remind, localize, weather,
    log, note, quote, model, tools, skills, crypto,
    help as help_cmd,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])

_DISPATCH = {
    "/remember": remember.handle,
    "/recall":   recall.handle,
    "/todo":     todo.handle,
    "/remind":   remind.handle,
    "/localize": localize.handle,
    "/weather":  weather.handle,
    "/log":      log.handle,
    "/note":     note.handle,
    "/quote":    quote.handle,
    "/model":    model.handle,
    "/tools":    tools.handle,
    "/skills":   skills.handle,
    "/crypto":   crypto.handle,
    "/help":     help_cmd.handle,
}


@router.post("", response_model=AiResponse)
def chat(req: AiRequest):
    ctx = load_ctx()
    msg = req.message.strip()

    if msg.startswith("/"):
        cmd = msg.split()[0]
        handler = _DISPATCH.get(cmd)
        if handler:
            result = handler(ctx, msg)
            log.add_entry(cmd, msg.removeprefix(cmd).strip())
            return AiResponse(reply=result.message, actions=[])
        return AiResponse(
            reply=f"Commande inconnue : {cmd}\n" + help_cmd.handle(ctx, "/help").message,
            actions=[],
        )

    try:
        reply, actions = chat_api(ctx, msg)
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
