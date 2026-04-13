"""
Routeur langage naturel de Spark — 3 niveaux :

  1. Regex fast path  (0 tokens)   — patterns fréquents reconnus immédiatement
  2. Agent loop       (N tokens)   — IA avec accès à tous les outils du registre
  3. Fallback /ai     (N tokens)   — si aucun outil appelé, traité comme question
"""

import re
from result import Result
from commands.registry import run_tool


# ──────────────────────────────────────────────────────────────────────────────
#  Niveau 1 — Regex fast path
# ──────────────────────────────────────────────────────────────────────────────

# "boire de l'eau, 15min"  /  "appeler Alice, 2h"
_REMIND_RE = re.compile(
    r"^(.+?),\s*(\d+\s*(?:min|h|s|j|heures?|minutes?|secondes?|jours?))\s*$",
    re.IGNORECASE,
)

# "note que j'ai appelé Alice"  /  "note : réunion annulée"
_NOTE_RE = re.compile(
    r"^(?:note(?:r)?(?:\s+que)?|enregistre(?:r)?(?:\s+que)?)\s*[:\-]?\s+(.+)$",
    re.IGNORECASE,
)

# "ajoute du lait à ma liste courses"  /  "ajoute pain à la liste courses"
_TODO_ADD_RE = re.compile(
    r"^(?:ajoute(?:r)?)\s+(.+?)\s+à\s+(?:(?:ma|la)\s+(?:liste(?:\s+de)?\s+)?)(.+)$",
    re.IGNORECASE,
)


def _try_regex(text: str, ctx) -> Result | None:
    """Tente de matcher les patterns fréquents. Retourne un Result ou None."""

    m = _REMIND_RE.match(text)
    if m:
        message, duration = m.group(1).strip(), m.group(2).strip()
        result_text, label = run_tool("set_reminder", {"message": message, "duration": duration}, ctx)
        return Result.success(f"{label}\n{result_text}" if label else result_text)

    m = _NOTE_RE.match(text)
    if m:
        content = m.group(1).strip()
        result_text, label = run_tool("save_note", {"content": content}, ctx)
        return Result.success(f"{label}\n{result_text}" if label else result_text)

    m = _TODO_ADD_RE.match(text)
    if m:
        item, list_name = m.group(1).strip(), m.group(2).strip()
        result_text, label = run_tool("add_todo_item", {"list_name": list_name, "item": item}, ctx)
        return Result.success(f"{label}\n{result_text}" if label else result_text)

    return None


# ──────────────────────────────────────────────────────────────────────────────
#  System prompt du routeur
# ──────────────────────────────────────────────────────────────────────────────

_ROUTER_SYSTEM = """\
Tu es Spark, un assistant personnel. L'utilisateur s'exprime en langage naturel.
Analyse son intention et exécute-la directement avec les outils disponibles.

Règles :
- Utilise toujours un outil si la demande s'y prête.
- Tu peux enchaîner plusieurs outils pour une demande complexe.
- Si la demande est une question ouverte sans action claire, réponds en texte court.
- Ne commente pas tes actions — les labels d'outils informent déjà l'utilisateur.\
"""


# ──────────────────────────────────────────────────────────────────────────────
#  Handler principal
# ──────────────────────────────────────────────────────────────────────────────

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

    # Niveau 1 — regex
    direct = _try_regex(text, ctx)
    if direct:
        return direct

    # Niveau 2 — agent loop
    from commands.ai import agent_loop, _resolve_provider
    try:
        _resolve_provider(ctx)
    except ValueError as e:
        return Result.error(str(e))

    reply, actions = agent_loop(ctx, _ROUTER_SYSTEM, [{"role": "user", "content": text}])

    if actions:
        parts = actions[:]
        if reply:
            parts.append(f"Spark : {reply}")
        return Result.success("\n".join(parts))

    # Niveau 3 — fallback question ouverte
    if reply:
        return Result.success(f"Spark : {reply}")

    # Aucun résultat — traiter comme /ai
    from commands.ai import handle as ai_handle
    return ai_handle(ctx, f"/ai {text}")
