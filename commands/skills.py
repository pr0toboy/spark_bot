from result import Result

PRESETS = {
    "superpower": (
        "Tu es en mode Superpower. Applique systématiquement ces règles :\n"
        "\n"
        "RAISONNEMENT\n"
        "- Pour toute question complexe, décompose le problème étape par étape avant de répondre.\n"
        "- Identifie les hypothèses implicites et signale-les.\n"
        "- Si plusieurs approches existent, présente les compromis.\n"
        "- En cas d'incertitude, dis-le clairement plutôt que d'inventer.\n"
        "\n"
        "FORMAT\n"
        "- Utilise le markdown : titres, listes, blocs de code, gras pour les points clés.\n"
        "- Structure longue réponse : contexte → analyse → conclusion → prochaines étapes.\n"
        "- Pour le code : explique ce qu'il fait, signale les cas limites, préfère la lisibilité.\n"
        "\n"
        "QUALITÉ\n"
        "- Sois exhaustif mais concis : pas de remplissage, chaque phrase doit apporter de la valeur.\n"
        "- Anticipe les questions de suivi et adresse-les proactivement.\n"
        "- Propose des alternatives quand la demande initiale n'est pas optimale.\n"
        "- Termine par une action concrète ou une question de clarification si pertinent."
    ),
}


def handle(ctx, user_input: str) -> Result:
    sub = user_input.removeprefix("/skills").strip()

    if not sub or sub == "list":
        return _list(ctx)
    if sub == "presets":
        return _list_presets()
    if sub.startswith("add "):
        return _add(ctx, sub.removeprefix("add ").strip())
    if sub.startswith("remove "):
        return _remove(ctx, sub.removeprefix("remove ").strip())
    if sub.startswith("show "):
        return _show(ctx, sub.removeprefix("show ").strip())

    return Result.error(
        "Usage : /skills                    — lister les skills actifs\n"
        "        /skills presets            — lister les presets disponibles\n"
        "        /skills add <nom> [texte]  — ajouter (preset si connu, interactif sinon)\n"
        "        /skills remove <nom>       — supprimer\n"
        "        /skills show <nom>         — afficher les instructions"
    )


def _list(ctx) -> Result:
    if not ctx.skills:
        return Result.success("Aucun skill défini. Ajoute-en avec /skills add <nom>.")
    lines = ["🧠 Skills actifs :"]
    for name, instructions in ctx.skills.items():
        preview = instructions.splitlines()[0][:60]
        tag = " [preset]" if name in PRESETS else ""
        lines.append(f"  {name:<16} — {preview}{tag}")
    return Result.success("\n".join(lines))


def _list_presets() -> Result:
    lines = ["✨ Presets disponibles :"]
    for name, instructions in PRESETS.items():
        preview = instructions.splitlines()[0][:60]
        lines.append(f"  {name:<16} — {preview}")
    lines.append("\nAjoute un preset avec : /skills add <nom>")
    return Result.success("\n".join(lines))


def _add(ctx, arg: str) -> Result:
    if not arg:
        return Result.error("Usage : /skills add <nom> [instructions]")

    parts = arg.split(None, 1)
    name = parts[0].lower()

    if len(parts) == 2:
        instructions = parts[1].strip()
    elif name in PRESETS:
        instructions = PRESETS[name]
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

    is_update = name in ctx.skills
    ctx.skills[name] = instructions
    ctx.save()
    action = "mis à jour" if is_update else "ajouté"
    preset_tag = " (preset)" if name in PRESETS and len(parts) == 1 else ""
    return Result.success(f"🧠 Skill '{name}' {action}{preset_tag}.")


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
