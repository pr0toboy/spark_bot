from pydantic import BaseModel, Field
from typing import Any


class AiRequest(BaseModel):
    message: str = Field(min_length=1)


class AiResponse(BaseModel):
    reply: str
    actions: list[str] = []


class NoteCreate(BaseModel):
    content: str = Field(min_length=1)


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
    name: str = Field(min_length=1)
    instructions: str = Field(min_length=1)


class SkillItem(BaseModel):
    name: str
    instructions: str
    is_preset: bool = False


class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None
    glm_api_key: str | None = None
    anthropic_model: str | None = None
    groq_model: str | None = None
    glm_model: str | None = None


class SettingsResponse(BaseModel):
    anthropic_model: str
    groq_model: str
    glm_model: str
    has_anthropic_key: bool
    has_groq_key: bool
    has_glm_key: bool


class ContextResponse(BaseModel):
    memory: str
    todo_list: dict[str, Any]
    vault_path: str
    chat_history: list[dict[str, str]]
