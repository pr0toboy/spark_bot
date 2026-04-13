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

GLM_MODELS = [
    "glm-4-plus",
    "glm-4",
    "glm-4-air",
    "glm-4-flash",
    "glm-z1-flash",
]

DEFAULT_ANTHROPIC = ANTHROPIC_MODELS[0]
DEFAULT_GROQ = GROQ_MODELS[0]
DEFAULT_GLM = GLM_MODELS[0]


def handle(ctx, user_input: str) -> Result:
    arg = user_input.removeprefix("/model").strip()

    if not arg:
        return _show(ctx)

    if arg == "list":
        return _list_all()

    parts = arg.split(None, 1)
    if len(parts) != 2:
        return Result.error(
            "Usage : /model anthropic <model> | /model groq <model> | /model glm <model> | /model list"
        )

    provider, model = parts[0].lower(), parts[1].strip()

    if provider == "anthropic":
        if model not in ANTHROPIC_MODELS:
            return Result.error(f"Modèle inconnu. Disponibles : {', '.join(ANTHROPIC_MODELS)}")
        ctx.anthropic_model = model
        ctx.save()
        return Result.success(f"Modèle Anthropic → {model}")

    if provider == "groq":
        if model not in GROQ_MODELS:
            return Result.error(f"Modèle inconnu. Disponibles : {', '.join(GROQ_MODELS)}")
        ctx.groq_model = model
        ctx.save()
        return Result.success(f"Modèle Groq → {model}")

    if provider == "glm":
        if model not in GLM_MODELS:
            return Result.error(f"Modèle inconnu. Disponibles : {', '.join(GLM_MODELS)}")
        ctx.glm_model = model
        ctx.save()
        return Result.success(f"Modèle GLM → {model}")

    return Result.error("Provider inconnu. Utilise 'anthropic', 'groq' ou 'glm'.")


def _show(ctx) -> Result:
    a = ctx.anthropic_model or DEFAULT_ANTHROPIC
    g = ctx.groq_model or DEFAULT_GROQ
    z = ctx.glm_model or DEFAULT_GLM
    return Result.success(
        f"Modèles actifs :\n"
        f"  Anthropic : {a}\n"
        f"  Groq      : {g}\n"
        f"  GLM       : {z}\n\n"
        f"Change avec /model <provider> <model>\n"
        f"Liste complète : /model list"
    )


def _list_all() -> Result:
    a_list = "\n".join(f"  • {m}" for m in ANTHROPIC_MODELS)
    g_list = "\n".join(f"  • {m}" for m in GROQ_MODELS)
    z_list = "\n".join(f"  • {m}" for m in GLM_MODELS)
    return Result.success(
        f"Anthropic :\n{a_list}\n\nGroq :\n{g_list}\n\nGLM (ZhipuAI) :\n{z_list}"
    )
