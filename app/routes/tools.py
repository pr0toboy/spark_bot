from fastapi import APIRouter, HTTPException
from app.models import ToolAction, ToolItem
from app.deps import load_ctx
from commands.tools import REGISTRY

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("", response_model=list[ToolItem])
def list_tools():
    ctx = load_ctx()
    return [
        ToolItem(
            name=name,
            description=info["description"],
            enabled=ctx.tools_enabled.get(name, False),
            requires=info.get("requires"),
        )
        for name, info in REGISTRY.items()
    ]


@router.post("")
def set_tool(req: ToolAction):
    ctx = load_ctx()
    if req.name not in REGISTRY:
        raise HTTPException(status_code=404, detail=f"Outil '{req.name}' inconnu.")

    if req.enabled:
        info = REGISTRY[req.name]
        if info.get("requires") and not getattr(ctx, info["requires"], None):
            raise HTTPException(status_code=400, detail=info["requires_msg"])

    ctx.tools_enabled[req.name] = req.enabled
    ctx.save()
    return {"name": req.name, "enabled": req.enabled}
