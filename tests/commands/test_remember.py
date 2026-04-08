from unittest.mock import patch
from context import Context
from commands import remember, recall


def test_remember_inline():
    ctx = Context()
    with patch.object(ctx, "save"):
        result = remember.handle(ctx, "/remember mon code wifi est 1234")
    assert ctx.memory == "mon code wifi est 1234"
    assert result.ok
    assert "1234" in result.message


def test_remember_interactive():
    ctx = Context()
    with patch("builtins.input", return_value="acheter du pain"):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                result = remember.handle(ctx, "/remember")
    assert ctx.memory == "acheter du pain"
    assert result.ok


def test_remember_empty_input():
    ctx = Context()
    with patch("builtins.input", return_value=""):
        with patch("builtins.print"):
            result = remember.handle(ctx, "/remember")
    assert not result.ok
    assert "❌" in result.message


def test_remember_saves_context():
    ctx = Context()
    with patch.object(ctx, "save") as mock_save:
        remember.handle(ctx, "/remember test")
    mock_save.assert_called_once()


def test_recall_with_memory():
    ctx = Context(memory="acheter du pain")
    result = recall.handle(ctx, "/recall")
    assert result.ok
    assert "acheter du pain" in result.message


def test_recall_empty():
    ctx = Context()
    result = recall.handle(ctx, "/recall")
    assert result.ok
    assert "rien" in result.message.lower() or "vide" in result.message.lower()
