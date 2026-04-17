from fastapi import APIRouter
from app.models import SettingsUpdate, SettingsResponse
from app.deps import load_ctx
from commands.model import (
    DEFAULT_ANTHROPIC, DEFAULT_GROQ, DEFAULT_GLM,
    ANTHROPIC_MODELS, GROQ_MODELS, GLM_MODELS,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings():
    ctx = load_ctx()
    return SettingsResponse(
        anthropic_model=ctx.anthropic_model or DEFAULT_ANTHROPIC,
        groq_model=ctx.groq_model or DEFAULT_GROQ,
        glm_model=ctx.glm_model or DEFAULT_GLM,
        has_anthropic_key=bool(ctx.api_key),
        has_groq_key=bool(ctx.groq_api_key),
        has_glm_key=bool(ctx.glm_api_key),
    )


@router.post("")
def update_settings(req: SettingsUpdate):
    ctx = load_ctx()
    if req.anthropic_api_key is not None:
        ctx.api_key = req.anthropic_api_key
    if req.groq_api_key is not None:
        ctx.groq_api_key = req.groq_api_key
    if req.glm_api_key is not None:
        ctx.glm_api_key = req.glm_api_key
    if req.anthropic_model and req.anthropic_model in ANTHROPIC_MODELS:
        ctx.anthropic_model = req.anthropic_model
    if req.groq_model and req.groq_model in GROQ_MODELS:
        ctx.groq_model = req.groq_model
    if req.glm_model and req.glm_model in GLM_MODELS:
        ctx.glm_model = req.glm_model
    ctx.save()
    return {"ok": True}


@router.get("/models")
def get_models():
    return {"anthropic": ANTHROPIC_MODELS, "groq": GROQ_MODELS, "glm": GLM_MODELS}
