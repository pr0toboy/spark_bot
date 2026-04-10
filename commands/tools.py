from result import Result

REGISTRY = {
    "obsidian": {
        "description": "Accès au vault Obsidian pour /ai (lecture/écriture de notes)",
        "requires": "vault_path",
        "requires_msg": "Configure d'abord un vault avec /note vault <chemin>",
    },
}


def handle(ctx, user_input: str) -> Result:
    sub = user_input.removeprefix("/tools").strip()

    if not sub or sub == "list":
        return _list(ctx)
    if sub.startswith("enable "):
        return _enable(ctx, sub.removeprefix("enable ").strip())
    if sub.startswith("disable "):
        return _disable(ctx, sub.removeprefix("disable ").strip())

    return Result.error(
        "Usage : /tools              — lister les outils\n"
        "        /tools enable <outil>\n"
        "        /tools disable <outil>"
    )


def _list(ctx) -> Result:
    lines = ["🛠️  Outils disponibles :"]
    for name, info in REGISTRY.items():
        status = "✅ activé" if ctx.tools_enabled.get(name, False) else "⭕ désactivé"
        lines.append(f"  {name:<12} {status}  — {info['description']}")
    return Result.success("\n".join(lines))


def _enable(ctx, name: str) -> Result:
    if name not in REGISTRY:
        return Result.error(f"Outil inconnu : {name}. Disponibles : {', '.join(REGISTRY)}")

    info = REGISTRY[name]
    if info.get("requires") and not getattr(ctx, info["requires"], None):
        return Result.error(f"❌ {info['requires_msg']}")

    ctx.tools_enabled[name] = True
    ctx.save()
    return Result.success(f"✅ Outil '{name}' activé.")


def _disable(ctx, name: str) -> Result:
    if name not in REGISTRY:
        return Result.error(f"Outil inconnu : {name}. Disponibles : {', '.join(REGISTRY)}")

    ctx.tools_enabled[name] = False
    ctx.save()
    return Result.success(f"⭕ Outil '{name}' désactivé.")
