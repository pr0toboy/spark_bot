from unittest.mock import patch
from context import Context
from commands import remember, recall


def test_remember_stores_input():
    ctx = Context()
    with patch("builtins.input", return_value="acheter du pain"):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                remember.handle(ctx, "/remember")
    assert ctx.memory == "acheter du pain"


def test_remember_saves_context():
    ctx = Context()
    with patch("builtins.input", return_value="test"):
        with patch("builtins.print"):
            with patch.object(ctx, "save") as mock_save:
                remember.handle(ctx, "/remember")
    mock_save.assert_called_once()


def test_recall_with_memory(capsys):
    ctx = Context(memory="acheter du pain")
    recall.handle(ctx, "/recall")
    assert "acheter du pain" in capsys.readouterr().out


def test_recall_empty(capsys):
    ctx = Context()
    recall.handle(ctx, "/recall")
    out = capsys.readouterr().out
    assert "rien" in out.lower() or "vide" in out.lower()
