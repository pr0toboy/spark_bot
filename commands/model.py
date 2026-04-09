from result import Result

ANTHROPIC_MODELS = [
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

DEFAULT_ANTHROPIC = ANTHROPIC_MODELS[0]
DEFAULT_GROQ = GROQ_MODELS[0]


def handle(ctx, user_input: str) -> Result:
    arg = user_input.removeprefix("/model").strip()

    if not arg:
        return _show(ctx)

    if arg == "list":
        return _list_all()

    parts = arg.split(None, 1)
    if len(parts) != 2:
        return Result.error(
            "Usage : /model anthropic <model> | /model groq <model> | /model list"
        )

    provider, model = parts[0].lower(), parts[1].strip()

    if provider == "anthropic":
        if model not in ANTHROPIC_MODELS:
            return Result.error(
                f"Modèle inconnu. Disponibles : {', '.join(ANTHROPIC_MODELS)}"
            )
        ctx.anthropic_model = model
        ctx.save()
        return Result.success(f"Modèle Anthropic → {model}")

    if provider == "groq":
        if model not in GROQ_MODELS:
            return Result.error(
                f"Modèle inconnu. Disponibles : {', '.join(GROQ_MODELS)}"
            )
        ctx.groq_model = model
        ctx.save()
        return Result.success(f"Modèle Groq → {model}")

    return Result.error("Provider inconnu. Utilise 'anthropic' ou 'groq'.")


def _show(ctx) -> Result:
    a = ctx.anthropic_model or DEFAULT_ANTHROPIC
    g = ctx.groq_model or DEFAULT_GROQ
    return Result.success(
        f"Modèles actifs :\n"
        f"  Anthropic : {a}\n"
        f"  Groq      : {g}\n\n"
        f"Change avec /model anthropic <model> ou /model groq <model>\n"
        f"Liste complète : /model list"
    )


def _list_all() -> Result:
    a_list = "\n".join(f"  • {m}" for m in ANTHROPIC_MODELS)
    g_list = "\n".join(f"  • {m}" for m in GROQ_MODELS)
    return Result.success(
        f"Anthropic :\n{a_list}\n\nGroq :\n{g_list}"
    )
