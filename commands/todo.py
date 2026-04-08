from result import Result


def handle(ctx, user_input: str) -> Result:
    print("📒 Gestionnaire de listes")
    _show_lists(ctx.todo_list)
    while True:
        cmd = input("› ").strip()
        if cmd == "/new":
            _create_list(ctx)
        elif cmd == "/show":
            _show_list(ctx.todo_list)
        elif cmd == "/edit":
            _edit_list(ctx)
        elif cmd == "/remove":
            _remove_list(ctx)
        elif cmd == "/exit":
            break
        else:
            print("Commandes : /new, /show, /edit, /remove, /exit")
    return Result.success()


def _show_lists(todo_list: dict) -> None:
    if not todo_list:
        print("Il n'y a pas de liste.")
    else:
        print("Listes existantes :")
        for name in todo_list:
            print(f"  - {name}")


def _create_list(ctx) -> None:
    name = input("Nom de la nouvelle liste : ").strip()
    if name in ctx.todo_list:
        print("❗ Une liste avec ce nom existe déjà.")
    else:
        ctx.todo_list[name] = []
        ctx.save()
        print(f"✅ Liste '{name}' créée.")


def _show_list(todo_list: dict) -> None:
    name = input("Quelle liste afficher ? ").strip()
    if name not in todo_list:
        print("❌ Liste introuvable.")
    elif not todo_list[name]:
        print("📭 La liste est vide.")
    else:
        print(f"📋 Contenu de '{name}' :")
        for item in todo_list[name]:
            print(f"  - {item}")


def _remove_list(ctx) -> None:
    name = input("Quelle liste supprimer ? ").strip()
    if name in ctx.todo_list:
        del ctx.todo_list[name]
        ctx.save()
        print(f"✅ Liste '{name}' supprimée.")
    else:
        print("❗ Cette liste n'existe pas.")


def _edit_list(ctx) -> None:
    name = input("Quelle liste éditer ? ").strip()
    if name not in ctx.todo_list:
        print("❌ Liste introuvable.")
        return
    items = ctx.todo_list[name]
    while True:
        print(f"(édition de '{name}') Tape /add, /remove, /show ou /exit :")
        cmd = input("› ").strip()
        if cmd == "/add":
            item = input("Nom du nouvel élément : ").strip()
            items.append(item)
            ctx.save()
            print("✅ Ajouté.")
        elif cmd == "/remove":
            item = input("Nom de l'élément à supprimer : ").strip()
            if item in items:
                items.remove(item)
                ctx.save()
                print("✅ Supprimé.")
            else:
                print("❌ Élément non trouvé.")
        elif cmd == "/show":
            if not items:
                print("📭 La liste est vide.")
            else:
                for i in items:
                    print(f"  - {i}")
        elif cmd == "/exit":
            break
        else:
            print("Commandes : /add, /remove, /show, /exit")
