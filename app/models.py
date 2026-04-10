from pydantic import BaseModel
from typing import Any


class AiRequest(BaseModel):
    message: str


class AiResponse(BaseModel):
    reply: str
    actions: list[str] = []


class NoteCreate(BaseModel):
    content: str


class NoteItem(BaseModel):
    id: int
    timestamp: str
    content: str


class ToolAction(BaseModel):
    name: str
    enabled: bool


class ToolItem(BaseModel):
    name: str
    description: str
    enabled: bool
    requires: str | None = None


class SkillCreate(BaseModel):
    name: str
    instructions: str


class SkillItem(BaseModel):
    name: str
    instructions: str
    is_preset: bool = False


class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None
    anthropic_model: str | None = None
    groq_model: str | None = None


class SettingsResponse(BaseModel):
    anthropic_model: str
    groq_model: str
    has_anthropic_key: bool
    has_groq_key: bool


class ContextResponse(BaseModel):
    memory: str
    todo_list: dict[str, Any]
    vault_path: str
    chat_history: list[dict[str, str]]
