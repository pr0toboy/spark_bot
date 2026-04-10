import os
import json
import anthropic
import groq as groq_sdk
from pathlib import Path
from result import Result
from commands.model import DEFAULT_ANTHROPIC, DEFAULT_GROQ

_SPARK_MD = Path(__file__).parent.parent / "SPARK.md"

_VAULT_TOOLS_ANTHROPIC = [
    {
        "name": "list_vault_notes",
        "description": "Liste tous les fichiers .md présents dans le vault Obsidian.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_vault_note",
        "description": "Lit le contenu d'une note du vault Obsidian.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Nom du fichier .md à lire."},
            },
            "required": ["filename"],
        },
    },
    {
        "name": "write_vault_note",
        "description": (
            "Modifie ou crée une note dans le vault Obsidian. "
            "Conserver le frontmatter YAML existant si possible."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Nom du fichier .md."},
                "content": {"type": "string", "description": "Contenu complet du fichier."},
            },
            "required": ["filename", "content"],
        },
    },
]

_VAULT_TOOLS_GROQ = [
    {
        "type": "function",
        "function": {
            "name": "list_vault_notes",
            "description": "Liste tous les fichiers .md présents dans le vault Obsidian.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_vault_note",
            "description": "Lit le contenu d'une note du vault Obsidian.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Nom du fichier .md à lire."},
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_vault_note",
            "description": "Modifie ou crée une note dans le vault Obsidian.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["filename", "content"],
            },
        },
    },
]


def _run_tool(name: str, args: dict, vault_path: str) -> tuple[str, str]:
    """Execute a vault tool. Returns (result, action_label)."""
    vault = Path(vault_path).expanduser().resolve()

    if name == "list_vault_notes":
        files = sorted(vault.glob("*.md"))
        result = "\n".join(f.name for f in files) or "(vault vide)"
        return result, "📋 Listage du vault"

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

    return f"Outil '{name}' inconnu.", ""


def _resolve_provider(ctx):
    if ctx.api_key or os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", ctx.api_key or os.environ["ANTHROPIC_API_KEY"]
    if ctx.groq_api_key or os.environ.get("GROQ_API_KEY"):
        return "groq", ctx.groq_api_key or os.environ["GROQ_API_KEY"]
    raise ValueError("Aucune clé API. Lance /login anthropic ou /login groq.")


def _chat(ctx, system: str, messages: list, max_tokens: int = 1024) -> str:
    provider, api_key = _resolve_provider(ctx)

    if provider == "anthropic":
        model = ctx.anthropic_model or DEFAULT_ANTHROPIC
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model, max_tokens=max_tokens, system=system, messages=messages,
        )
        return response.content[0].text

    model = ctx.groq_model or DEFAULT_GROQ
    client = groq_sdk.Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}] + messages,
    )
    return response.choices[0].message.content


def _chat_with_vault(ctx, system: str, messages: list, vault_path: str) -> tuple[str, list[str]]:
    """Agentic loop with vault tools. Returns (reply, actions)."""
    provider, api_key = _resolve_provider(ctx)

    if provider == "anthropic":
        return _anthropic_vault_loop(ctx, api_key, system, messages, vault_path)
    return _groq_vault_loop(ctx, api_key, system, messages, vault_path)


def _anthropic_vault_loop(ctx, api_key, system, messages, vault_path) -> tuple[str, list[str]]:
    model = ctx.anthropic_model or DEFAULT_ANTHROPIC
    client = anthropic.Anthropic(api_key=api_key)
    history = list(messages)
    actions = []
    reply = ""

    while True:
        response = client.messages.create(
            model=model, max_tokens=2048, system=system,
            messages=history, tools=_VAULT_TOOLS_ANTHROPIC,
        )

        text_parts = [b.text for b in response.content if b.type == "text"]
        if text_parts:
            reply = "\n".join(text_parts)

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result, label = _run_tool(block.name, block.input, vault_path)
                if label:
                    actions.append(label)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        history.append({"role": "assistant", "content": response.content})
        history.append({"role": "user", "content": tool_results})

    return reply, actions


def _groq_vault_loop(ctx, api_key, system, messages, vault_path) -> tuple[str, list[str]]:
    model = ctx.groq_model or DEFAULT_GROQ
    client = groq_sdk.Groq(api_key=api_key)
    history = [{"role": "system", "content": system}] + list(messages)
    actions = []
    reply = ""

    while True:
        response = client.chat.completions.create(
            model=model, max_tokens=2048, messages=history,
            tools=_VAULT_TOOLS_GROQ, tool_choice="auto",
        )
        msg = response.choices[0].message
        reply = msg.content or ""

        if not msg.tool_calls:
            break

        history.append(msg)
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result, label = _run_tool(tool_call.function.name, args, vault_path)
            if label:
                actions.append(label)
            history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return reply, actions


def handle(ctx, user_input: str) -> Result:
    msg = user_input.removeprefix("/ai").strip()

    if msg == "history":
        return _history(ctx)
    if msg == "clear":
        return _clear(ctx)
    if msg == "compact":
        return _compact(ctx)
    if msg == "edit":
        return _edit_spark_md()
    if not msg:
        return Result.error(
            "Usage : /ai <question>\n"
            "        /ai history   — afficher l'historique\n"
            "        /ai clear     — vider l'historique\n"
            "        /ai compact   — résumer et compacter l'historique\n"
            "        /ai edit      — modifier SPARK.md"
        )

    base_system = _SPARK_MD.read_text() if _SPARK_MD.exists() else "Tu es Spark, un assistant CLI."
    spark_context = (
        f"\n\nContexte utilisateur :\n"
        f"Mémoire : {ctx.memory or 'vide'}\n"
        f"Todos : {ctx.todo_list or 'aucun'}"
    )
    if ctx.vault_path:
        spark_context += (
            f"\nVault Obsidian : {ctx.vault_path}\n"
            "Tu peux lister, lire et modifier les notes du vault avec les outils disponibles."
        )
    system = base_system + spark_context

    ctx.chat_history.append({"role": "user", "content": msg})

    try:
        if ctx.vault_path:
            reply, actions = _chat_with_vault(ctx, system, ctx.chat_history, ctx.vault_path)
        else:
            reply = _chat(ctx, system, ctx.chat_history)
            actions = []
    except ValueError as e:
        ctx.chat_history.pop()
        return Result.error(str(e))

    ctx.chat_history.append({"role": "assistant", "content": reply})
    ctx.save()

    output = "\n".join(actions + [f"Spark : {reply}"])
    return Result.success(output)


def _history(ctx) -> Result:
    if not ctx.chat_history:
        return Result.success("Historique vide.")
    lines = []
    for entry in ctx.chat_history:
        role = "Toi" if entry["role"] == "user" else "Spark"
        lines.append(f"[{role}] {entry['content']}")
    return Result.success("\n".join(lines))


def _clear(ctx) -> Result:
    ctx.chat_history = []
    ctx.save()
    return Result.success("Historique effacé.")


def _compact(ctx) -> Result:
    if not ctx.chat_history:
        return Result.success("Historique déjà vide.")

    history_text = "\n".join(f"{e['role']}: {e['content']}" for e in ctx.chat_history)
    try:
        summary = _chat(
            ctx,
            "Tu es un assistant qui résume des conversations de manière concise.",
            [{"role": "user", "content": f"Résume cette conversation en quelques phrases :\n\n{history_text}"}],
            max_tokens=512,
        )
    except ValueError as e:
        return Result.error(str(e))

    ctx.chat_history = [{"role": "assistant", "content": f"[Résumé] {summary}"}]
    ctx.save()
    return Result.success(f"Historique compacté :\n{summary}")


def _edit_spark_md() -> Result:
    current = _SPARK_MD.read_text() if _SPARK_MD.exists() else ""
    print(f"Contenu actuel de SPARK.md ({'vide' if not current else f'{len(current)} caractères'}) :")
    if current:
        print(current)
    print("Nouveau contenu (terminer avec une ligne contenant uniquement 'EOF') :")
    lines = []
    while True:
        line = input()
        if line == "EOF":
            break
        lines.append(line)
    new_content = "\n".join(lines)
    _SPARK_MD.write_text(new_content)
    return Result.success(f"SPARK.md mis à jour ({len(new_content)} caractères).")
