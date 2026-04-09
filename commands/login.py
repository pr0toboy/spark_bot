import getpass
from result import Result

_PROVIDERS = ("anthropic", "groq")


def handle(ctx, user_input: str) -> Result:
    arg = user_input.removeprefix("/login").strip().lower()

    if not arg:
        print(f"Provider ({'/'.join(_PROVIDERS)}) : ", end="", flush=True)
        try:
            arg = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return Result.error("Annulé.")

    if arg not in _PROVIDERS:
        return Result.error(f"Provider inconnu. Choix : {', '.join(_PROVIDERS)}")

    try:
        api_key = getpass.getpass(f"Clé API {arg.capitalize()} : ").strip()
    except (EOFError, KeyboardInterrupt):
        return Result.error("Annulé.")

    if not api_key:
        return Result.error("Clé vide, annulé.")

    if arg == "anthropic":
        if not api_key.startswith("sk-ant-"):
            return Result.error("Clé Anthropic invalide (doit commencer par 'sk-ant-').")
        ctx.api_key = api_key
    elif arg == "groq":
        if not api_key.startswith("gsk_"):
            return Result.error("Clé Groq invalide (doit commencer par 'gsk_').")
        ctx.groq_api_key = api_key

    ctx.save()
    return Result.success(f"Clé {arg.capitalize()} sauvegardée.")
