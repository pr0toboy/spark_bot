from result import Result


def handle(ctx, user_input: str) -> Result:
    if ctx.memory:
        return Result.success(f"Je me souviens de : {ctx.memory}")
    return Result.success("Je n'ai rien en mémoire.")
