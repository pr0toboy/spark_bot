import re
import threading
from result import Result

_active_reminders: list[dict] = []


def _parse_duration(s: str) -> int | None:
    """Retourne la durée en secondes, ou None si invalide."""
    s = s.strip().lower()
    patterns = [
        (r"^(\d+)\s*(?:s|seconde|secondes)$", 1),
        (r"^(\d+)\s*(?:m|min|minute|minutes)$", 60),
        (r"^(\d+)\s*(?:h|heure|heures)$", 3600),
        (r"^(\d+)\s*(?:j|jour|jours)$", 86400),
    ]
    for pattern, multiplier in patterns:
        m = re.match(pattern, s)
        if m:
            return int(m.group(1)) * multiplier
    return None


def handle(ctx, user_input: str) -> Result:
    rest = user_input.removeprefix("/remind").strip()

    if rest == "list":
        return _list_reminders()

    if "," not in rest:
        return Result.error("❌ Format : /remind <message>, <durée>  (ex: /remind boire de l'eau, 10min)")

    message, duration_str = rest.rsplit(",", 1)
    message = message.strip()
    seconds = _parse_duration(duration_str)

    if seconds is None:
        return Result.error("❌ Durée invalide. Ex: 10min, 1h, 30s, 1 jour")

    reminder = {"message": message}
    _active_reminders.append(reminder)

    def _fire():
        print(f"\n🔔 Rappel : {message}")
        if reminder in _active_reminders:
            _active_reminders.remove(reminder)

    threading.Timer(seconds, _fire).start()
    return Result.success(f"✅ Rappel créé : '{message}' dans {seconds}s")


def _list_reminders() -> Result:
    if not _active_reminders:
        return Result.success("📭 Aucun rappel actif.")
    lines = ["📋 Rappels actifs :"] + [f"  - {r['message']}" for r in _active_reminders]
    return Result.success("\n".join(lines))
