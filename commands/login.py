import getpass
from result import Result


def handle(ctx, user_input: str) -> Result:
    """Store the Anthropic API key in the database."""
    parts = user_input.removeprefix("/login").strip()
    if parts:
        api_key = parts
    else:
        try:
            api_key = getpass.getpass("Anthropic API key: ").strip()
        except (EOFError, KeyboardInterrupt):
            return Result.error("Annulé.")

    if not api_key.startswith("sk-"):
        return Result.error("Clé invalide (doit commencer par 'sk-').")

    ctx.api_key = api_key
    ctx.save()
    return Result.success("Clé API sauvegardée. Tu peux maintenant utiliser /ask.")
