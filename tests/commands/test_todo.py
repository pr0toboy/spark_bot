from unittest.mock import patch
from context import Context
from commands import todo


def test_create_list():
    ctx = Context()
    with patch("builtins.input", return_value="liste1"):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                todo._create_list(ctx)
    assert "liste1" in ctx.todo_list


def test_create_list_duplicate(capsys):
    ctx = Context(todo_list={"courses": []})
    with patch("builtins.input", return_value="courses"):
        todo._create_list(ctx)
    assert "existe" in capsys.readouterr().out


def test_remove_list():
    ctx = Context(todo_list={"courses": ["pain"]})
    with patch("builtins.input", return_value="courses"):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                todo._remove_list(ctx)
    assert "courses" not in ctx.todo_list


def test_remove_list_missing(capsys):
    ctx = Context()
    with patch("builtins.input", return_value="inexistant"):
        todo._remove_list(ctx)
    out = capsys.readouterr().out
    assert "existe" in out.lower() or "n'existe" in out.lower()
