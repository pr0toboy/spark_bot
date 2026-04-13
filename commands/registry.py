"""
Registre unifié de tous les outils Spark.

Chaque outil est défini une seule fois (nom, description, paramètres, handler).
Les fonctions get_anthropic_tools() / get_openai_tools() génèrent les schemas
dans le format attendu par chaque provider API.
"""

from pathlib import Path


# ──────────────────────────────────────────────────────────────────────────────
#  Définitions des outils
# ──────────────────────────────────────────────────────────────────────────────

_CORE_REGISTRY = [
    {
        "name": "set_reminder",
        "description": "Crée un rappel qui se déclenche après une durée donnée.",
        "parameters": {
            "message":  {"type": "string", "description": "Texte du rappel."},
            "duration": {"type": "string", "description": "Durée avant déclenchement (ex: '10min', '2h', '30s', '1j')."},
        },
        "required": ["message", "duration"],
    },
    {
        "name": "save_note",
        "description": "Enregistre une note rapide (écrite aussi dans le vault Obsidian si configuré).",
        "parameters": {
            "content": {"type": "string", "description": "Contenu de la note."},
        },
        "required": ["content"],
    },
    {
        "name": "create_todo_list",
        "description": "Crée une nouvelle liste de tâches.",
        "parameters": {
            "list_name": {"type": "string", "description": "Nom de la liste à créer."},
        },
        "required": ["list_name"],
    },
    {
        "name": "add_todo_item",
        "description": "Ajoute un élément à une liste de tâches existante.",
        "parameters": {
            "list_name": {"type": "string", "description": "Nom de la liste cible."},
            "item":      {"type": "string", "description": "Élément à ajouter."},
        },
        "required": ["list_name", "item"],
    },
    {
        "name": "show_todo_list",
        "description": "Affiche le contenu d'une liste de tâches.",
        "parameters": {
            "list_name": {"type": "string", "description": "Nom de la liste à afficher."},
        },
        "required": ["list_name"],
    },
    {
        "name": "remove_todo_item",
        "description": "Supprime un élément d'une liste de tâches.",
        "parameters": {
            "list_name": {"type": "string", "description": "Nom de la liste."},
            "item":      {"type": "string", "description": "Élément à supprimer."},
        },
        "required": ["list_name", "item"],
    },
    {
        "name": "delete_todo_list",
        "description": "Supprime entièrement une liste de tâches.",
        "parameters": {
            "list_name": {"type": "string", "description": "Nom de la liste à supprimer."},
        },
        "required": ["list_name"],
    },
    {
        "name": "get_weather",
        "description": "Affiche la météo actuelle basée sur la localisation IP.",
        "parameters": {},
        "required": [],
    },
    {
        "name": "get_quote",
        "description": "Retourne une citation inspirante aléatoire.",
        "parameters": {},
        "required": [],
    },
]

_VAULT_REGISTRY = [
    {
        "name": "list_vault_notes",
        "description": "Liste tous les fichiers .md présents dans le vault Obsidian.",
        "parameters": {},
        "required": [],
    },
    {
        "name": "read_vault_note",
        "description": "Lit le contenu d'une note du vault Obsidian.",
        "parameters": {
            "filename": {"type": "string", "description": "Nom du fichier .md à lire."},
        },
        "required": ["filename"],
    },
    {
        "name": "write_vault_note",
        "description": (
            "Modifie ou crée une note dans le vault Obsidian. "
            "Conserver le frontmatter YAML existant si possible."
        ),
        "parameters": {
            "filename": {"type": "string", "description": "Nom du fichier .md."},
            "content":  {"type": "string", "description": "Contenu complet du fichier."},
        },
        "required": ["filename", "content"],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
#  Génération des schemas par provider
# ──────────────────────────────────────────────────────────────────────────────

def _to_anthropic(tool: dict) -> dict:
    return {
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": {
            "type": "object",
            "properties": tool["parameters"],
            "required": tool["required"],
        },
    }


def _to_openai(tool: dict) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": {
                "type": "object",
                "properties": tool["parameters"],
                "required": tool["required"],
            },
        },
    }


def get_anthropic_tools(ctx) -> list:
    tools = [_to_anthropic(t) for t in _CORE_REGISTRY]
    if ctx.vault_path and ctx.tools_enabled.get("obsidian", False):
        tools.extend(_to_anthropic(t) for t in _VAULT_REGISTRY)
    return tools


def get_openai_tools(ctx) -> list:
    tools = [_to_openai(t) for t in _CORE_REGISTRY]
    if ctx.vault_path and ctx.tools_enabled.get("obsidian", False):
        tools.extend(_to_openai(t) for t in _VAULT_REGISTRY)
    return tools


# ──────────────────────────────────────────────────────────────────────────────
#  Exécution des outils
# ──────────────────────────────────────────────────────────────────────────────

def run_tool(name: str, args: dict, ctx) -> tuple[str, str]:
    """Exécute un outil par nom. Retourne (texte_résultat, label_action)."""

    if name == "set_reminder":
        from commands.remind import handle
        result = handle(ctx, f"/remind {args['message']}, {args['duration']}")
        return result.message, f"⏰ Rappel : {args['message']} dans {args['duration']}"

    if name == "save_note":
        from commands.note import _add
        result = _add(args["content"], ctx)
        return result.message, f"📝 Note : {args['content'][:50]}"

    if name == "create_todo_list":
        from commands.todo import handle
        result = handle(ctx, f"/todo new {args['list_name']}")
        return result.message, f"📋 Nouvelle liste : {args['list_name']}"

    if name == "add_todo_item":
        from commands.todo import handle
        result = handle(ctx, f"/todo add {args['list_name']} {args['item']}")
        return result.message, f"✅ Todo [{args['list_name']}] : {args['item']}"

    if name == "show_todo_list":
        from commands.todo import handle
        result = handle(ctx, f"/todo show {args['list_name']}")
        return result.message, ""

    if name == "remove_todo_item":
        from commands.todo import handle
        result = handle(ctx, f"/todo remove {args['list_name']} {args['item']}")
        return result.message, f"🗑️  Todo supprimé : {args['item']}"

    if name == "delete_todo_list":
        from commands.todo import handle
        result = handle(ctx, f"/todo delete {args['list_name']}")
        return result.message, f"🗑️  Liste supprimée : {args['list_name']}"

    if name == "get_weather":
        from commands.weather import handle
        result = handle(ctx, "/weather")
        return result.message, "⛅ Météo"

    if name == "get_quote":
        from commands.quote import handle
        result = handle(ctx, "/quote")
        return result.message, "💬 Citation"

    if name in ("list_vault_notes", "read_vault_note", "write_vault_note"):
        return _run_vault_tool(name, args, ctx.vault_path)

    return f"Outil '{name}' inconnu.", ""


def _run_vault_tool(name: str, args: dict, vault_path: str) -> tuple[str, str]:
    vault = Path(vault_path).expanduser().resolve()

    if name == "list_vault_notes":
        files = sorted(vault.glob("*.md"))
        return "\n".join(f.name for f in files) or "(vault vide)", "📋 Listage du vault"

    if name == "read_vault_note":
        note_file = (vault / args["filename"]).resolve()
        if not str(note_file).startswith(str(vault)):
            return "Accès refusé.", "🚫 Accès refusé"
        if not note_file.exists():
            return f"Fichier '{args['filename']}' introuvable.", f"❌ Introuvable : {args['filename']}"
        return note_file.read_text(), f"📖 Lecture : {args['filename']}"

    if name == "write_vault_note":
        note_file = (vault / args["filename"]).resolve()
        if not str(note_file).startswith(str(vault)):
            return "Accès refusé.", "🚫 Accès refusé"
        vault.mkdir(parents=True, exist_ok=True)
        note_file.write_text(args["content"])
        return "Note sauvegardée.", f"✏️  Modification : {args['filename']}"

    return f"Outil vault '{name}' inconnu.", ""
