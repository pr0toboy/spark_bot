from result import Result


def handle(ctx, user_input: str) -> Result:
    value = user_input.removeprefix("/remember").strip()
    if not value:
        print("Que dois-je me souvenir ?")
        value = input("› ").strip()
    if not value:
        return Result.error("❌ Rien à mémoriser.")
    ctx.memory = value
    ctx.save()
    return Result.success(f"Ok, je me souviens : « {value} »")
