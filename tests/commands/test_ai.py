from unittest.mock import patch, MagicMock
from context import Context
from commands import ai


def test_ask_sends_message_and_stores_history():
    ctx = Context()
    with patch("commands.ai._chat", return_value="Voici ma réponse."):
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

    def capture(ctx, system, messages, **kwargs):
        captured["system"] = system
        return "OK"

    with patch("commands.ai._chat", side_effect=capture):
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
    with patch("commands.ai._chat", return_value="OK"):
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
    with patch("commands.ai._chat", return_value="Conversation sur Python."):
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
