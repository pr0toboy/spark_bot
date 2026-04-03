def handle(ctx, user_input: str) -> None:
    print("Que dois-je me souvenir ?")
    ctx.memory = input("› ").strip()
    ctx.save()
    print("Ok, je m'en souviendrai !")
