from fastapi import APIRouter, HTTPException
from app.models import SkillCreate, SkillItem
from app.deps import load_ctx
PRESETS = {
    "cromagnon": (
        "Toi répondre TRÈS simple. Comme homme des cavernes.\n"
        "- Mots courts. Phrases courtes. Pas de mots compliqués.\n"
        "- Si mot compliqué obligatoire, toi expliquer avec mots simples après.\n"
        "- Pas de markdown. Pas de titres. Pas de listes fancy.\n"
        "- Toi utiliser analogies simples : feu, pierre, mammifère, grotte.\n"
        "- Maximum 5 phrases par réponse. Aller à l'essentiel."
    ),
    "superpower": (
        "Tu es en mode Superpower. Applique systématiquement ces règles :\n\n"
        "RAISONNEMENT\n"
        "- Décompose le problème étape par étape avant de répondre.\n"
        "- Identifie les hypothèses implicites et signale-les.\n"
        "- Si plusieurs approches existent, présente les compromis.\n\n"
        "FORMAT\n"
        "- Utilise le markdown : titres, listes, blocs de code, gras pour les points clés.\n"
        "- Structure : contexte → analyse → conclusion → prochaines étapes.\n\n"
        "QUALITÉ\n"
        "- Exhaustif mais concis : chaque phrase apporte de la valeur.\n"
        "- Anticipe les questions de suivi.\n"
        "- Propose des alternatives quand la demande initiale n'est pas optimale."
    ),
}

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[SkillItem])
def list_skills():
    ctx = load_ctx()
    return [
        SkillItem(name=name, instructions=instr, is_preset=name in PRESETS)
        for name, instr in ctx.skills.items()
    ]


@router.get("/presets", response_model=list[SkillItem])
def list_presets():
    return [
        SkillItem(name=name, instructions=instr, is_preset=True)
        for name, instr in PRESETS.items()
    ]


@router.post("", response_model=SkillItem)
def upsert_skill(req: SkillCreate):
    ctx = load_ctx()
    name = req.name.lower()
    ctx.skills[name] = req.instructions
    ctx.save()
    return SkillItem(name=name, instructions=req.instructions, is_preset=name in PRESETS)


@router.delete("/{name}")
def delete_skill(name: str):
    ctx = load_ctx()
    if name not in ctx.skills:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' introuvable.")
    del ctx.skills[name]
    ctx.save()
    return {"ok": True}
