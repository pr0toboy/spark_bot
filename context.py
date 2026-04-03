from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

DATA_PATH = Path("data/spark_data.json")


@dataclass
class Context:
    memory: str = ""
    todo_list: dict = field(default_factory=dict)
    chat_history: list = field(default_factory=list)

    def save(self) -> None:
        DATA_PATH.parent.mkdir(exist_ok=True)
        DATA_PATH.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls) -> "Context":
        if DATA_PATH.exists():
            return cls(**json.loads(DATA_PATH.read_text()))
        return cls()
