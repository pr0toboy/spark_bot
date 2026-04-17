from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.deps import load_ctx
from commands.claude_cmd import run_prompt

router = APIRouter(prefix="/api/claude", tags=["claude"])


class ClaudeRequest(BaseModel):
    prompt: str = Field(min_length=1)
    use_continue: bool = False


class ClaudeResponse(BaseModel):
    reply: str
    ok: bool


@router.post("", response_model=ClaudeResponse)
def run_claude(req: ClaudeRequest):
    ctx = load_ctx()
    api_key = ctx.api_key if hasattr(ctx, "api_key") else None
    ok, reply = run_prompt(req.prompt, req.use_continue, api_key=api_key)
    return ClaudeResponse(reply=reply, ok=ok)
