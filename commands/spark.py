import re
from result import Result
from commands.registry import run_tool
from commands.ai import agent_loop, _resolve_provider, handle as _ai_handle

_REMIND_RE = re.compile(
    r"^(.+?),\s*(\d+\s*(?:min|h|s|j|heures?|minutes?|secondes?|jours?))\s*$",
    re.IGNORECASE,
)
_NOTE_RE = re.compile(
    r"^(?:note(?:r)?(?:\s+que)?|enregistre(?:r)?(?:\s+que)?)\s*[:\-]?\s+(.+)$",
    re.IGNORECASE,
)
_TODO_ADD_RE = re.compile(
    r"^(?:ajoute(?:r)?)\s+(.+?)\s+à\s+(?:(?:ma|la)\s+(?:liste(?:\s+de)?\s+)?)(.+)$",
    re.IGNORECASE,
)

_ROUTER_SYSTEM = """\
Tu es Spark, un assistant personnel. L'utilisateur s'exprime en langage naturel.
Analyse son intention et exécute-la directement avec les outils disponibles.

Règles :
- Utilise toujours un outil si la demande s'y prête.
- Tu peux enchaîner plusieurs outils pour une demande complexe.
- Si la demande est une question ouverte sans action claire, réponds en texte court.
- Ne commente pas tes actions — les labels d'outils informent déjà l'utilisateur.\
"""


def _fmt(label: str, result: str) -> str:
    return f"{label}\n{result}" if label else result


def _try_regex(text: str, ctx) -> Result | None:
    m = _REMIND_RE.match(text)
    if m:
        r, l = run_tool("set_reminder", {"message": m.group(1).strip(), "duration": m.group(2).strip()}, ctx)
        return Result.success(_fmt(l, r))

    m = _NOTE_RE.match(text)
    if m:
        r, l = run_tool("save_note", {"content": m.group(1).strip()}, ctx)
        return Result.success(_fmt(l, r))

    m = _TODO_ADD_RE.match(text)
    if m:
        r, l = run_tool("add_todo_item", {"list_name": m.group(2).strip(), "item": m.group(1).strip()}, ctx)
        return Result.success(_fmt(l, r))

    return None


def handle(ctx, user_input: str) -> Result:
    text = user_input.removeprefix("/spark").strip()
    if not text:
        return Result.error(
            "Tape simplement ce que tu veux faire en langage naturel.\n"
            "Exemples :\n"
            "  boire de l'eau, 20min\n"
            "  note que j'ai appelé Alice\n"
            "  ajoute du lait à ma liste courses\n"
            "  rappelle-moi de faire les courses et ajoute pain à la liste"
        )

    direct = _try_regex(text, ctx)
    if direct:
        return direct

    try:
        reply, actions = agent_loop(ctx, _ROUTER_SYSTEM, [{"role": "user", "content": text}])
    except ValueError as e:
        return Result.error(str(e))

    if actions:
        if reply:
            actions.append(f"Spark : {reply}")
        return Result.success("\n".join(actions))

    if reply:
        return Result.success(f"Spark : {reply}")

    return _ai_handle(ctx, f"/ai {text}")
