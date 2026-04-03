def handle(ctx, user_input: str) -> None:
    if ctx.memory:
        print(f"Je me souviens de : {ctx.memory}")
    else:
        print("Je n'ai rien en mémoire.")
