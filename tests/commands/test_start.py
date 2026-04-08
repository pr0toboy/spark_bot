from unittest.mock import patch
from context import Context
from commands import start


def test_start_first_launch_sets_name():
    ctx = Context()
    with patch("builtins.input", return_value="Alexis"):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                result = start.handle(ctx, "/start")
    assert ctx.name == "Alexis"
    assert result.ok
    assert "Alexis" in result.message


def test_start_first_launch_empty_name():
    ctx = Context()
    with patch("builtins.input", return_value=""):
        with patch("builtins.print"):
            result = start.handle(ctx, "/start")
    assert ctx.name == ""
    assert result.ok


def test_start_returning_user():
    ctx = Context(name="Alexis")
    result = start.handle(ctx, "/start")
    assert result.ok
    assert "Alexis" in result.message
    assert "revoir" in result.message


def test_start_saves_name():
    ctx = Context()
    with patch("builtins.input", return_value="Alexis"):
        with patch("builtins.print"):
            with patch.object(ctx, "save") as mock_save:
                start.handle(ctx, "/start")
    mock_save.assert_called_once()
