from dataclasses import dataclass


@dataclass
class Result:
    ok: bool
    message: str = ""

    @staticmethod
    def success(message: str = "") -> "Result":
        return Result(ok=True, message=message)

    @staticmethod
    def error(message: str) -> "Result":
        return Result(ok=False, message=message)
