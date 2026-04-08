from unittest.mock import patch
from context import Context
from commands import note


def test_note_inline(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note acheter du pain", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "acheter du pain" in result.message


def test_note_interactive(tmp_path):
    ctx = Context()
    with patch("builtins.input", return_value="appeler maman"):
        with patch("builtins.print"):
            result = note.handle(ctx, "/note", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "appeler maman" in result.message


def test_note_empty_interactive(tmp_path):
    ctx = Context()
    with patch("builtins.input", return_value=""):
        with patch("builtins.print"):
            result = note.handle(ctx, "/note", db_path=tmp_path / "spark.db")
    assert not result.ok
    assert "❌" in result.message


def test_note_list_empty(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note list", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "Aucune" in result.message


def test_note_list(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context()
    note.handle(ctx, "/note première note", db_path=db)
    note.handle(ctx, "/note deuxième note", db_path=db)

    result = note.handle(ctx, "/note list", db_path=db)
    assert result.ok
    assert "première note" in result.message
    assert "deuxième note" in result.message


def test_note_delete(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context()
    note.handle(ctx, "/note à supprimer", db_path=db)

    listed = note._list(db_path=db)
    note_id = listed.message.split("[")[1].split("]")[0]

    result = note.handle(ctx, f"/note delete {note_id}", db_path=db)
    assert result.ok
    assert "supprimée" in result.message

    after = note._list(db_path=db)
    assert "Aucune" in after.message


def test_note_delete_invalid_id(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note delete 999", db_path=tmp_path / "spark.db")
    assert not result.ok


def test_note_delete_bad_arg(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note delete abc", db_path=tmp_path / "spark.db")
    assert not result.ok
    assert "Usage" in result.message
