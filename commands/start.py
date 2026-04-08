from result import Result


def handle(ctx, user_input: str) -> Result:
    if not ctx.name:
        print("Bienvenue sur Spark ! Comment tu t'appelles ?")
        name = input("› ").strip()
        if name:
            ctx.name = name
            ctx.save()
        else:
            name = "toi"
        return Result.success(
            f"Salut {name} ! 🚀 Spark est prêt.\n"
            "Tape /help pour voir les commandes disponibles."
        )
    return Result.success(
        f"Content de te revoir, {ctx.name} ! 🚀\n"
        "Tape /help pour voir les commandes disponibles."
    )
