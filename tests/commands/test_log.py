from context import Context
from commands import log


def test_log_empty(tmp_path):
    result = log._show(db_path=tmp_path / "spark.db")
    assert result.ok
    assert "Aucune" in result.message


def test_add_and_show(tmp_path):
    db = tmp_path / "spark.db"
    log.add_entry("/remember", "test", db_path=db)
    log.add_entry("/recall", "", db_path=db)

    result = log._show(db_path=db)
    assert result.ok
    assert "/remember" in result.message
    assert "/recall" in result.message


def test_show_filters_by_command(tmp_path):
    db = tmp_path / "spark.db"
    log.add_entry("/remember", "test", db_path=db)
    log.add_entry("/recall", "", db_path=db)

    result = log._show("/remember", db_path=db)
    assert "/remember" in result.message
    assert "/recall" not in result.message


def test_clear(tmp_path):
    db = tmp_path / "spark.db"
    log.add_entry("/help", "", db_path=db)

    result = log._clear(db_path=db)
    assert result.ok

    after = log._show(db_path=db)
    assert "Aucune" in after.message


def test_handle_show(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context()
    log.add_entry("/help", "", db_path=db)

    result = log.handle(ctx, "/log", db_path=db)
    assert result.ok


def test_handle_clear(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context()
    log.add_entry("/help", "", db_path=db)

    result = log.handle(ctx, "/log clear", db_path=db)
    assert result.ok
    assert "effacé" in result.message
