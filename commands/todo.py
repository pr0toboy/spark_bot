from result import Result


def _parse_name_item(rest: str, subcmd: str, todo_list: dict):
    """Parse '<nom> <élément>' from rest. Returns (name, item) or Result.error."""
    parts = rest.split(None, 1)
    if len(parts) < 2:
        return Result.error(f"Usage : /todo {subcmd} <nom> <élément>")
    name, item = parts[0], parts[1].strip()
    if name not in todo_list:
        return Result.error(f"Liste '{name}' introuvable.")
    return name, item


def handle(ctx, user_input: str) -> Result:
    args = user_input.removeprefix("/todo").strip()

    if not args:
        if not ctx.todo_list:
            return Result.success("Aucune liste. Crée-en une avec /todo new <nom>.")
        lines = ["📒 Listes :"]
        for name, items in ctx.todo_list.items():
            lines.append(f"  {name} ({len(items)} élément(s))")
        return Result.success("\n".join(lines))

    parts = args.split(None, 1)
    subcmd = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if subcmd == "new":
        name = rest.strip()
        if not name:
            return Result.error("Usage : /todo new <nom>")
        if name in ctx.todo_list:
            return Result.error(f"La liste '{name}' existe déjà.")
        ctx.todo_list[name] = []
        ctx.save()
        return Result.success(f"✅ Liste '{name}' créée.")

    if subcmd == "show":
        name = rest.strip()
        if not name:
            return Result.error("Usage : /todo show <nom>")
        if name not in ctx.todo_list:
            return Result.error(f"Liste '{name}' introuvable.")
        items = ctx.todo_list[name]
        if not items:
            return Result.success(f"📭 La liste '{name}' est vide.")
        lines = [f"📋 '{name}' :"]
        for item in items:
            lines.append(f"  - {item}")
        return Result.success("\n".join(lines))

    if subcmd == "add":
        parsed = _parse_name_item(rest, subcmd, ctx.todo_list)
        if isinstance(parsed, Result):
            return parsed
        name, item = parsed
        ctx.todo_list[name].append(item)
        ctx.save()
        return Result.success(f"✅ '{item}' ajouté à '{name}'.")

    if subcmd == "remove":
        parsed = _parse_name_item(rest, subcmd, ctx.todo_list)
        if isinstance(parsed, Result):
            return parsed
        name, item = parsed
        if item not in ctx.todo_list[name]:
            return Result.error(f"Élément '{item}' non trouvé dans '{name}'.")
        ctx.todo_list[name].remove(item)
        ctx.save()
        return Result.success(f"✅ '{item}' supprimé de '{name}'.")

    if subcmd == "delete":
        name = rest.strip()
        if not name:
            return Result.error("Usage : /todo delete <nom>")
        if name not in ctx.todo_list:
            return Result.error(f"Liste '{name}' introuvable.")
        del ctx.todo_list[name]
        ctx.save()
        return Result.success(f"✅ Liste '{name}' supprimée.")

    return Result.error(f"Sous-commande inconnue : '{subcmd}'. Tape /help todo.")
