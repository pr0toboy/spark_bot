from unittest.mock import patch
from context import Context
from commands import skills


def test_list_empty():
    ctx = Context()
    result = skills.handle(ctx, "/skills")
    assert result.ok
    assert "Aucun skill" in result.message


def test_list_explicit():
    ctx = Context(skills={"traduction": "Traduis toujours en anglais."})
    result = skills.handle(ctx, "/skills list")
    assert result.ok
    assert "traduction" in result.message
    assert "Traduis" in result.message


def test_add_inline():
    ctx = Context()
    with patch.object(ctx, "save"):
        result = skills.handle(ctx, "/skills add résumé Résume toujours en 3 points.")
    assert result.ok
    assert ctx.skills["résumé"] == "Résume toujours en 3 points."


def test_add_normalises_name_to_lowercase():
    ctx = Context()
    with patch.object(ctx, "save"):
        skills.handle(ctx, "/skills add MonSkill instruction")
    assert "monskill" in ctx.skills


def test_add_interactive():
    ctx = Context()
    with patch("builtins.input", side_effect=["Tu réponds toujours en markdown.", "EOF"]):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                result = skills.handle(ctx, "/skills add markdown")
    assert result.ok
    assert "Tu réponds toujours en markdown." in ctx.skills["markdown"]


def test_add_interactive_empty():
    ctx = Context()
    with patch("builtins.input", side_effect=["EOF"]):
        with patch("builtins.print"):
            result = skills.handle(ctx, "/skills add vide")
    assert not result.ok
    assert "vide" in result.message.lower()


def test_add_no_name():
    ctx = Context()
    result = skills.handle(ctx, "/skills add")
    assert not result.ok


def test_add_updates_existing():
    ctx = Context(skills={"traduction": "ancienne instruction"})
    with patch.object(ctx, "save"):
        skills.handle(ctx, "/skills add traduction nouvelle instruction")
    assert ctx.skills["traduction"] == "nouvelle instruction"


def test_remove():
    ctx = Context(skills={"code": "Écris du code propre."})
    with patch.object(ctx, "save"):
        result = skills.handle(ctx, "/skills remove code")
    assert result.ok
    assert "code" not in ctx.skills


def test_remove_unknown():
    ctx = Context()
    result = skills.handle(ctx, "/skills remove ghost")
    assert not result.ok
    assert "introuvable" in result.message


def test_show():
    ctx = Context(skills={"code": "Écris du code propre et commenté."})
    result = skills.handle(ctx, "/skills show code")
    assert result.ok
    assert "Écris du code propre et commenté." in result.message


def test_show_unknown():
    ctx = Context()
    result = skills.handle(ctx, "/skills show ghost")
    assert not result.ok


def test_bad_usage():
    ctx = Context()
    result = skills.handle(ctx, "/skills blabla")
    assert not result.ok
    assert "Usage" in result.message


def test_presets_list():
    ctx = Context()
    result = skills.handle(ctx, "/skills presets")
    assert result.ok
    assert "superpower" in result.message


def test_add_superpower_preset():
    ctx = Context()
    with patch.object(ctx, "save"):
        result = skills.handle(ctx, "/skills add superpower")
    assert result.ok
    assert "superpower" in ctx.skills
    assert ctx.skills["superpower"] == skills.PRESETS["superpower"]
    assert "(preset)" in result.message


def test_add_superpower_custom_overrides_preset():
    ctx = Context()
    with patch.object(ctx, "save"):
        skills.handle(ctx, "/skills add superpower instruction custom")
    assert ctx.skills["superpower"] == "instruction custom"


def test_list_shows_preset_tag():
    ctx = Context(skills={"superpower": skills.PRESETS["superpower"]})
    result = skills.handle(ctx, "/skills list")
    assert "[preset]" in result.message


def test_save_called_on_add():
    ctx = Context()
    with patch.object(ctx, "save") as mock_save:
        skills.handle(ctx, "/skills add test instruction")
    mock_save.assert_called_once()


def test_save_called_on_remove():
    ctx = Context(skills={"test": "instruction"})
    with patch.object(ctx, "save") as mock_save:
        skills.handle(ctx, "/skills remove test")
    mock_save.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
#  Injection dans /ai (system prompt)
# ──────────────────────────────────────────────────────────────────────────────

def test_superpower_injected_in_ai():
    from commands import ai
    ctx = Context(skills={"superpower": skills.PRESETS["superpower"]})
    captured = {}

    def capture(ctx, system, messages):
        captured["system"] = system
        return "OK", []

    with patch("commands.ai.agent_loop", side_effect=capture):
        with patch.object(ctx, "save"):
            ai.handle(ctx, "/ai bonjour")

    assert "[superpower]" in captured["system"]
    assert "Superpower" in captured["system"]


def test_skills_injected_in_system():
    from commands import ai
    ctx = Context(skills={"code": "Écris du code propre."})
    captured = {}

    def capture(ctx, system, messages):
        captured["system"] = system
        return "OK", []

    with patch("commands.ai.agent_loop", side_effect=capture):
        with patch.object(ctx, "save"):
            ai.handle(ctx, "/ai bonjour")

    assert "[code]" in captured["system"]
    assert "Écris du code propre." in captured["system"]


def test_no_skills_no_injection():
    from commands import ai
    ctx = Context()
    captured = {}

    def capture(ctx, system, messages):
        captured["system"] = system
        return "OK", []

    with patch("commands.ai.agent_loop", side_effect=capture):
        with patch.object(ctx, "save"):
            ai.handle(ctx, "/ai bonjour")

    assert "Skills actifs" not in captured["system"]


def test_multiple_skills_all_injected():
    from commands import ai
    ctx = Context(skills={"traduction": "Traduis en anglais.", "résumé": "Résume en 3 points."})
    captured = {}

    def capture(ctx, system, messages):
        captured["system"] = system
        return "OK", []

    with patch("commands.ai.agent_loop", side_effect=capture):
        with patch.object(ctx, "save"):
            ai.handle(ctx, "/ai test")

    assert "[traduction]" in captured["system"]
    assert "[résumé]" in captured["system"]
