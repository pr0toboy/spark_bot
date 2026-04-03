from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

DATA_PATH = Path(__file__).parent / "data" / "spark_data.json"


@dataclass
class Context:
    memory: str = ""
    todo_list: dict = field(default_factory=dict)
    chat_history: list = field(default_factory=list)

    def save(self) -> None:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls) -> "Context":
        if DATA_PATH.exists():
            try:
                return cls(**json.loads(DATA_PATH.read_text()))
            except (json.JSONDecodeError, TypeError):
                return cls()
        return cls()
