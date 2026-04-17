from pydantic import BaseModel, Field
from typing import Any


class AiRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class AiResponse(BaseModel):
    reply: str
    actions: list[str] = []


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


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
    name: str = Field(min_length=1, max_length=64)
    instructions: str = Field(min_length=1, max_length=2000)


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


# ── Crypto ────────────────────────────────────────────────────────────────────

class CryptoWalletItem(BaseModel):
    label: str
    address: str
    chain: str
    balance: float | None = None
    balance_usd: float | None = None


class CryptoWalletCreate(BaseModel):
    address: str = Field(min_length=1)
    label: str = Field(min_length=1)


class CryptoWalletRename(BaseModel):
    label: str = Field(min_length=1)


class CryptoMarketItem(BaseModel):
    symbol: str
    price_usd: float
    change_24h: float


class CryptoPortfolio(BaseModel):
    wallets: list[CryptoWalletItem]
    market: list[CryptoMarketItem]
    total_usd: float | None = None


class CryptoPriceItem(BaseModel):
    symbol: str
    price_usd: float
    change_24h: float
    market_cap: float | None = None


class CryptoTrendItem(BaseModel):
    rank: int | None = None
    symbol: str
    name: str


class CryptoAlertItem(BaseModel):
    id: int
    coin: str
    direction: str
    price: float
    active: bool


class CryptoAlertCreate(BaseModel):
    coin: str = Field(min_length=1)
    direction: str
    price: float


# ── Habits ────────────────────────────────────────────────────────────────────

class HabitItem(BaseModel):
    id: int
    name: str
    freq_num: int
    freq_den: int
    done_today: bool
    streak: int
    best_streak: int
    week: list[bool]


class HabitCreate(BaseModel):
    name: str = Field(min_length=1)
    freq_num: int = 1
    freq_den: int = 1


class HabitStats(BaseModel):
    id: int
    name: str
    streak: int
    best_streak: int
    week_done: int
    month_done: int
    total: int
    week: list[bool]


class HabitCheckResult(BaseModel):
    id: int
    name: str
    done_today: bool
    streak: int
    best_streak: int
