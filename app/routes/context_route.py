from fastapi import APIRouter
from app.models import ContextResponse
from app.deps import load_ctx

router = APIRouter(prefix="/api/context", tags=["context"])


@router.get("", response_model=ContextResponse)
def get_context():
    ctx = load_ctx()
    return ContextResponse(
        memory=ctx.memory,
        todo_list=ctx.todo_list,
        vault_path=ctx.vault_path,
        chat_history=ctx.chat_history,
    )
