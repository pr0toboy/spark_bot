from unittest.mock import patch
from context import Context
from commands import todo


def test_list_empty():
    ctx = Context()
    result = todo.handle(ctx, "/todo")
    assert result.ok
    assert "Aucune liste" in result.message


def test_list_shows_lists():
    ctx = Context(todo_list={"courses": ["lait", "pain"], "travail": []})
    result = todo.handle(ctx, "/todo")
    assert result.ok
    assert "courses" in result.message
    assert "travail" in result.message


def test_new_list():
    ctx = Context()
    with patch.object(ctx, "save"):
        result = todo.handle(ctx, "/todo new courses")
    assert result.ok
    assert "courses" in ctx.todo_list
    assert ctx.todo_list["courses"] == []


def test_new_list_duplicate():
    ctx = Context(todo_list={"courses": []})
    result = todo.handle(ctx, "/todo new courses")
    assert not result.ok
    assert "existe" in result.message


def test_new_list_no_name():
    ctx = Context()
    result = todo.handle(ctx, "/todo new")
    assert not result.ok


def test_show_list():
    ctx = Context(todo_list={"courses": ["lait", "pain"]})
    result = todo.handle(ctx, "/todo show courses")
    assert result.ok
    assert "lait" in result.message
    assert "pain" in result.message


def test_show_list_empty():
    ctx = Context(todo_list={"vide": []})
    result = todo.handle(ctx, "/todo show vide")
    assert result.ok
    assert "vide" in result.message.lower()


def test_show_list_missing():
    ctx = Context()
    result = todo.handle(ctx, "/todo show ghost")
    assert not result.ok
    assert "introuvable" in result.message


def test_add_item():
    ctx = Context(todo_list={"courses": []})
    with patch.object(ctx, "save"):
        result = todo.handle(ctx, "/todo add courses lait")
    assert result.ok
    assert "lait" in ctx.todo_list["courses"]


def test_add_item_list_missing():
    ctx = Context()
    result = todo.handle(ctx, "/todo add ghost lait")
    assert not result.ok


def test_add_item_no_args():
    ctx = Context()
    result = todo.handle(ctx, "/todo add courses")
    assert not result.ok


def test_remove_item():
    ctx = Context(todo_list={"courses": ["lait", "pain"]})
    with patch.object(ctx, "save"):
        result = todo.handle(ctx, "/todo remove courses lait")
    assert result.ok
    assert "lait" not in ctx.todo_list["courses"]
    assert "pain" in ctx.todo_list["courses"]


def test_remove_item_missing():
    ctx = Context(todo_list={"courses": ["lait"]})
    result = todo.handle(ctx, "/todo remove courses pain")
    assert not result.ok
    assert "non trouvé" in result.message


def test_remove_item_list_missing():
    ctx = Context()
    result = todo.handle(ctx, "/todo remove ghost lait")
    assert not result.ok


def test_delete_list():
    ctx = Context(todo_list={"courses": ["lait"]})
    with patch.object(ctx, "save"):
        result = todo.handle(ctx, "/todo delete courses")
    assert result.ok
    assert "courses" not in ctx.todo_list


def test_delete_list_missing():
    ctx = Context()
    result = todo.handle(ctx, "/todo delete ghost")
    assert not result.ok


def test_unknown_subcommand():
    ctx = Context()
    result = todo.handle(ctx, "/todo blabla")
    assert not result.ok
    assert "inconnue" in result.message
