import os
import shutil
import subprocess
from result import Result

_TIMEOUT = 180  # seconds
_FALLBACK = os.path.expanduser("~/.local/bin/claude")


def _bin() -> str | None:
    return shutil.which("claude") or (_FALLBACK if os.path.isfile(_FALLBACK) else None)


def run_prompt(prompt: str, use_continue: bool = False, api_key: str | None = None) -> tuple[bool, str]:
    path = _bin()
    if not path:
        return False, "Claude Code introuvable (cherché dans PATH et ~/.local/bin/claude)."

    cmd = [path, "-p", "--dangerously-skip-permissions", "--output-format", "text"]
    if use_continue:
        cmd.append("--continue")
    cmd.append(prompt)

    env = os.environ.copy()
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT, env=env)
        out = r.stdout.strip()
        if not out:
            err = r.stderr.strip()
            return (False, err or f"Pas de réponse (code {r.returncode}).") if r.returncode != 0 \
                else (True, "(pas de réponse)")
        return True, out
    except subprocess.TimeoutExpired:
        return False, f"Délai dépassé ({_TIMEOUT}s)."
    except Exception as e:
        return False, str(e)


def handle(ctx, user_input: str) -> Result:
    prompt = user_input.removeprefix("/claude").strip()
    if not prompt:
        return Result.error("Usage : /claude <tâche ou question>  (ex: /claude liste les fichiers du projet)")
    ok, msg = run_prompt(prompt, api_key=ctx.api_key if hasattr(ctx, "api_key") else None)
    return Result.success(msg) if ok else Result.error(msg)
