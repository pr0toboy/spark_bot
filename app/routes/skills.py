from fastapi import APIRouter, HTTPException
from app.models import SkillCreate, SkillItem
from app.deps import load_ctx
from commands.skills import PRESETS

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
