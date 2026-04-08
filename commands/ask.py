import anthropic
from pathlib import Path
from result import Result

_SPARK_MD = Path(__file__).parent.parent / "SPARK.md"
_client = anthropic.Anthropic()


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

    response = _client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=system,
        messages=ctx.chat_history,
    )

    reply = response.content[0].text
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
    response = _client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        system="Tu es un assistant qui résume des conversations de manière concise.",
        messages=[{
            "role": "user",
            "content": f"Résume cette conversation en quelques phrases :\n\n{history_text}"
        }],
    )
    summary = response.content[0].text
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
