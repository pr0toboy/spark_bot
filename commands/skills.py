from result import Result


def handle(ctx, user_input: str) -> Result:
    sub = user_input.removeprefix("/skills").strip()

    if not sub or sub == "list":
        return _list(ctx)
    if sub.startswith("add "):
        return _add(ctx, sub.removeprefix("add ").strip())
    if sub.startswith("remove "):
        return _remove(ctx, sub.removeprefix("remove ").strip())
    if sub.startswith("show "):
        return _show(ctx, sub.removeprefix("show ").strip())

    return Result.error(
        "Usage : /skills                    — lister les skills\n"
        "        /skills add <nom> [texte]  — ajouter (interactif si pas de texte)\n"
        "        /skills remove <nom>       — supprimer\n"
        "        /skills show <nom>         — afficher les instructions"
    )


def _list(ctx) -> Result:
    if not ctx.skills:
        return Result.success("Aucun skill défini. Ajoute-en avec /skills add <nom>.")
    lines = ["🧠 Skills actifs :"]
    for name, instructions in ctx.skills.items():
        preview = instructions.splitlines()[0][:60]
        lines.append(f"  {name:<16} — {preview}")
    return Result.success("\n".join(lines))


def _add(ctx, arg: str) -> Result:
    if not arg:
        return Result.error("Usage : /skills add <nom> [instructions]")

    parts = arg.split(None, 1)
    name = parts[0].lower()

    if len(parts) == 2:
        instructions = parts[1].strip()
    else:
        print(f"📝 Instructions pour le skill '{name}' (terminer avec une ligne 'EOF') :")
        lines = []
        while True:
            line = input("› ")
            if line == "EOF":
                break
            lines.append(line)
        instructions = "\n".join(lines).strip()

    if not instructions:
        return Result.error("❌ Instructions vides, skill non enregistré.")

    ctx.skills[name] = instructions
    ctx.save()
    action = "mis à jour" if name in ctx.skills else "ajouté"
    return Result.success(f"🧠 Skill '{name}' {action}.")


def _remove(ctx, name: str) -> Result:
    name = name.lower()
    if name not in ctx.skills:
        return Result.error(f"❌ Skill '{name}' introuvable.")
    del ctx.skills[name]
    ctx.save()
    return Result.success(f"🗑️  Skill '{name}' supprimé.")


def _show(ctx, name: str) -> Result:
    name = name.lower()
    if name not in ctx.skills:
        return Result.error(f"❌ Skill '{name}' introuvable.")
    return Result.success(f"🧠 [{name}]\n{ctx.skills[name]}")
