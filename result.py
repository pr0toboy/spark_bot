from dataclasses import dataclass


@dataclass
class Result:
    ok: bool
    message: str = ""
    redirect: str = ""   # si non vide, bot.py ré-dispatche cette commande

    @staticmethod
    def success(message: str = "") -> "Result":
        return Result(ok=True, message=message)

    @staticmethod
    def error(message: str) -> "Result":
        return Result(ok=False, message=message)

    @staticmethod
    def dispatch(command: str) -> "Result":
        return Result(ok=True, redirect=command)
