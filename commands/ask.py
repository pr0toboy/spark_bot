import os
import anthropic
import groq as groq_sdk
from pathlib import Path
from result import Result
from commands.model import DEFAULT_ANTHROPIC, DEFAULT_GROQ

_SPARK_MD = Path(__file__).parent.parent / "SPARK.md"


def _resolve_provider(ctx):
    """Return (provider, api_key) or raise ValueError."""
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
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    else:  # groq
        model = ctx.groq_model or DEFAULT_GROQ
        client = groq_sdk.Groq(api_key=api_key)
        groq_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=groq_messages,
        )
        return response.choices[0].message.content


def handle(ctx, user_input: str) -> Result:
    msg = user_input.removeprefix("/ask").strip()

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
            "Usage : /ask <question>\n"
            "        /ask history   — afficher l'historique\n"
            "        /ask clear     — vider l'historique\n"
            "        /ask compact   — résumer et compacter l'historique\n"
            "        /ask edit      — modifier SPARK.md"
        )

    base_system = _SPARK_MD.read_text() if _SPARK_MD.exists() else "Tu es Spark, un assistant CLI."
    spark_context = (
        f"\n\nContexte utilisateur :\n"
        f"Mémoire : {ctx.memory or 'vide'}\n"
        f"Todos : {ctx.todo_list or 'aucun'}"
    )
    system = base_system + spark_context

    ctx.chat_history.append({"role": "user", "content": msg})

    try:
        reply = _chat(ctx, system, ctx.chat_history)
    except ValueError as e:
        ctx.chat_history.pop()
        return Result.error(str(e))

    ctx.chat_history.append({"role": "assistant", "content": reply})
    ctx.save()
    return Result.success(f"Spark : {reply}")


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

    history_text = "\n".join(
        f"{e['role']}: {e['content']}" for e in ctx.chat_history
    )
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
