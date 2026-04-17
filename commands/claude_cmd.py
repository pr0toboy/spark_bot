import subprocess
import os
from result import Result


def handle(ctx, user_input: str) -> Result:
    prompt = user_input.removeprefix("/claude").strip()

    env = os.environ.copy()
    if ctx.api_key:
        env["ANTHROPIC_API_KEY"] = ctx.api_key

    try:
        if prompt:
            subprocess.run(["claude", "-p", prompt], env=env)
        else:
            print("Lancement de Claude Code… (Ctrl+C pour revenir à Spark)")
            subprocess.run(["claude"], env=env)
    except FileNotFoundError:
        return Result.error("Claude Code introuvable. Rebuild l'image Docker.")

    return Result.success("")
