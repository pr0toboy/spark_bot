import time
from result import Result


def handle(ctx, user_input: str) -> Result:
    work_secs = 25 * 60
    break_secs = 5 * 60
    print("🍅 Pomodoro démarre — 25min travail / 5min pause × 4 cycles")
    print("(Ctrl+C pour annuler)\n")

    try:
        for cycle in range(1, 5):
            print(f"Cycle {cycle}/4")
            _countdown(work_secs, "💼 Travail")
            print("\n⏰ Pause !")
            _countdown(break_secs, "⏸️  Pause")
            print("\n⏰ Fin de la pause !")
        return Result.success("🎉 Pomodoro terminé !")
    except KeyboardInterrupt:
        return Result.error("⛔ Pomodoro interrompu.")


def _countdown(seconds: int, label: str) -> None:
    for remaining in range(seconds, 0, -1):
        m, s = divmod(remaining, 60)
        print(f"\r{label} : {m:02d}:{s:02d}", end="", flush=True)
        time.sleep(1)
    print(f"\r{label} : 00:00", flush=True)
