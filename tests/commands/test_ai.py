from unittest.mock import patch, MagicMock
from context import Context
from commands import ai
from commands.registry import _run_vault_tool


# ──────────────────────────────────────────────────────────────────────────────
#  Commandes de base (/ai history, clear, compact, edit)
# ──────────────────────────────────────────────────────────────────────────────

def test_ask_sends_message_and_stores_history():
    ctx = Context()
    with patch("commands.ai.agent_loop", return_value=("Voici ma réponse.", [])):
        with patch.object(ctx, "save"):
            result = ai.handle(ctx, "/ai Quelle est la météo ?")
    assert len(ctx.chat_history) == 2
    assert ctx.chat_history[0] == {"role": "user", "content": "Quelle est la météo ?"}
    assert ctx.chat_history[1] == {"role": "assistant", "content": "Voici ma réponse."}
    assert result.ok
    assert "Voici ma réponse." in result.message


def test_ask_includes_spark_context_in_system():
    ctx = Context(memory="je m'appelle Alexis", todo_list={"travail": ["PR review"]})
    captured = {}

    def capture(ctx, system, messages):
        captured["system"] = system
        return "OK", []

    with patch("commands.ai.agent_loop", side_effect=capture):
        with patch.object(ctx, "save"):
            ai.handle(ctx, "/ai test")

    assert "je m'appelle Alexis" in captured["system"]
    assert "PR review" in captured["system"]


def test_ask_empty_message():
    ctx = Context()
    result = ai.handle(ctx, "/ai")
    assert not result.ok
    assert "Usage" in result.message
    assert len(ctx.chat_history) == 0


def test_ask_saves_context():
    ctx = Context()
    with patch("commands.ai.agent_loop", return_value=("OK", [])):
        with patch.object(ctx, "save") as mock_save:
            ai.handle(ctx, "/ai test")
    mock_save.assert_called_once()


def test_ask_history_empty():
    ctx = Context()
    result = ai.handle(ctx, "/ai history")
    assert result.ok
    assert "vide" in result.message


def test_ask_history_shows_entries():
    ctx = Context()
    ctx.chat_history = [
        {"role": "user", "content": "Bonjour"},
        {"role": "assistant", "content": "Salut !"},
    ]
    result = ai.handle(ctx, "/ai history")
    assert result.ok
    assert "Bonjour" in result.message
    assert "Salut !" in result.message
    assert "Toi" in result.message
    assert "Spark" in result.message


def test_ask_clear():
    ctx = Context()
    ctx.chat_history = [{"role": "user", "content": "test"}]
    with patch.object(ctx, "save"):
        result = ai.handle(ctx, "/ai clear")
    assert result.ok
    assert ctx.chat_history == []


def test_ask_compact():
    ctx = Context()
    ctx.chat_history = [
        {"role": "user", "content": "Parle-moi de Python"},
        {"role": "assistant", "content": "Python est un langage interprété."},
    ]
    with patch("commands.ai._chat", return_value=("Conversation sur Python.", [])):
        with patch.object(ctx, "save"):
            result = ai.handle(ctx, "/ai compact")
    assert result.ok
    assert len(ctx.chat_history) == 1
    assert "[Résumé]" in ctx.chat_history[0]["content"]
    assert "Conversation sur Python." in result.message


def test_ask_compact_empty():
    ctx = Context()
    result = ai.handle(ctx, "/ai compact")
    assert result.ok
    assert "vide" in result.message


def test_ask_edit_spark_md(tmp_path):
    spark_md = tmp_path / "SPARK.md"
    with patch("commands.ai._SPARK_MD", spark_md):
        with patch("builtins.input", side_effect=["Tu es un assistant.", "EOF"]):
            result = ai.handle(Context(), "/ai edit")
    assert result.ok
    assert spark_md.read_text() == "Tu es un assistant."


# ──────────────────────────────────────────────────────────────────────────────
#  Agent loop — toujours actif, avec ou sans vault
# ──────────────────────────────────────────────────────────────────────────────

def test_agent_loop_always_called_for_ai():
    ctx = Context()
    with patch("commands.ai.agent_loop", return_value=("Réponse.", [])) as mock_loop:
        with patch.object(ctx, "save"):
            result = ai.handle(ctx, "/ai bonjour")
    mock_loop.assert_called_once()
    assert "Réponse." in result.message


def test_agent_loop_called_with_vault_active(tmp_path):
    ctx = Context(vault_path=str(tmp_path), tools_enabled={"obsidian": True})
    with patch("commands.ai.agent_loop", return_value=("Vault OK.", ["📖 Lecture : a.md"])) as mock_loop:
        with patch.object(ctx, "save"):
            result = ai.handle(ctx, "/ai lis mes notes")
    mock_loop.assert_called_once()
    assert "Vault OK." in result.message
    assert "📖 Lecture : a.md" in result.message


def test_system_contains_vault_hint_when_active(tmp_path):
    ctx = Context(vault_path=str(tmp_path), tools_enabled={"obsidian": True})
    captured = {}

    def capture(ctx, system, messages):
        captured["system"] = system
        return "OK", []

    with patch("commands.ai.agent_loop", side_effect=capture):
        with patch.object(ctx, "save"):
            ai.handle(ctx, "/ai test vault")

    assert "vault" in captured["system"].lower()


def test_system_no_vault_hint_when_disabled(tmp_path):
    ctx = Context(vault_path=str(tmp_path), tools_enabled={"obsidian": False})
    captured = {}

    def capture(ctx, system, messages):
        captured["system"] = system
        return "OK", []

    with patch("commands.ai.agent_loop", side_effect=capture):
        with patch.object(ctx, "save"):
            ai.handle(ctx, "/ai test")

    assert "Vault Obsidian actif" not in captured["system"]


def test_actions_displayed_in_output():
    ctx = Context()
    actions = ["📖 Lecture : note.md", "✏️  Modification : note.md"]
    with patch("commands.ai.agent_loop", return_value=("Fait.", actions)):
        with patch.object(ctx, "save"):
            result = ai.handle(ctx, "/ai modifie ma note")
    assert "📖 Lecture : note.md" in result.message
    assert "✏️  Modification : note.md" in result.message
    assert "Fait." in result.message


def test_history_rollback_on_error():
    ctx = Context()
    with patch("commands.ai.agent_loop", side_effect=ValueError("API error")):
        result = ai.handle(ctx, "/ai test")
    assert not result.ok
    assert len(ctx.chat_history) == 0


# ──────────────────────────────────────────────────────────────────────────────
#  Vault tools (registry._run_vault_tool)
# ──────────────────────────────────────────────────────────────────────────────

def test_run_tool_list(tmp_path):
    (tmp_path / "note1.md").write_text("contenu")
    (tmp_path / "note2.md").write_text("contenu")
    result, label = _run_vault_tool("list_vault_notes", {}, str(tmp_path))
    assert "note1.md" in result
    assert "note2.md" in result
    assert "Listage" in label


def test_run_tool_list_empty(tmp_path):
    result, label = _run_vault_tool("list_vault_notes", {}, str(tmp_path))
    assert "vide" in result


def test_run_tool_read(tmp_path):
    note = tmp_path / "test.md"
    note.write_text("# Titre\nContenu de la note.")
    result, label = _run_vault_tool("read_vault_note", {"filename": "test.md"}, str(tmp_path))
    assert "Contenu de la note." in result
    assert "test.md" in label


def test_run_tool_read_missing(tmp_path):
    result, label = _run_vault_tool("read_vault_note", {"filename": "ghost.md"}, str(tmp_path))
    assert "introuvable" in result.lower()


def test_run_tool_write(tmp_path):
    result, label = _run_vault_tool(
        "write_vault_note",
        {"filename": "new.md", "content": "# Nouvelle note"},
        str(tmp_path),
    )
    assert (tmp_path / "new.md").read_text() == "# Nouvelle note"
    assert "new.md" in label


def test_run_tool_write_overwrite(tmp_path):
    note = tmp_path / "existing.md"
    note.write_text("ancien contenu")
    _run_vault_tool("write_vault_note", {"filename": "existing.md", "content": "nouveau"}, str(tmp_path))
    assert note.read_text() == "nouveau"


def test_run_tool_path_traversal(tmp_path):
    result, label = _run_vault_tool(
        "read_vault_note", {"filename": "../secret.txt"}, str(tmp_path)
    )
    assert "Accès refusé" in result
