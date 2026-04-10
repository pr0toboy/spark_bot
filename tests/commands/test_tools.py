from unittest.mock import patch
from context import Context
from commands import tools


def test_list_empty():
    ctx = Context()
    result = tools.handle(ctx, "/tools")
    assert result.ok
    assert "obsidian" in result.message
    assert "désactivé" in result.message


def test_list_explicit():
    ctx = Context()
    result = tools.handle(ctx, "/tools list")
    assert result.ok
    assert "obsidian" in result.message


def test_enable_obsidian(tmp_path):
    ctx = Context(vault_path=str(tmp_path))
    with patch.object(ctx, "save"):
        result = tools.handle(ctx, "/tools enable obsidian")
    assert result.ok
    assert ctx.tools_enabled["obsidian"] is True


def test_enable_obsidian_no_vault():
    ctx = Context()
    result = tools.handle(ctx, "/tools enable obsidian")
    assert not result.ok
    assert "vault" in result.message.lower()


def test_disable_obsidian(tmp_path):
    ctx = Context(vault_path=str(tmp_path), tools_enabled={"obsidian": True})
    with patch.object(ctx, "save"):
        result = tools.handle(ctx, "/tools disable obsidian")
    assert result.ok
    assert ctx.tools_enabled["obsidian"] is False


def test_enable_unknown():
    ctx = Context()
    result = tools.handle(ctx, "/tools enable foobar")
    assert not result.ok
    assert "inconnu" in result.message


def test_disable_unknown():
    ctx = Context()
    result = tools.handle(ctx, "/tools disable foobar")
    assert not result.ok


def test_bad_usage():
    ctx = Context()
    result = tools.handle(ctx, "/tools blabla")
    assert not result.ok
    assert "Usage" in result.message


def test_list_shows_enabled_status(tmp_path):
    ctx = Context(vault_path=str(tmp_path), tools_enabled={"obsidian": True})
    result = tools.handle(ctx, "/tools")
    assert "activé" in result.message


def test_save_called_on_enable(tmp_path):
    ctx = Context(vault_path=str(tmp_path))
    with patch.object(ctx, "save") as mock_save:
        tools.handle(ctx, "/tools enable obsidian")
    mock_save.assert_called_once()


def test_save_called_on_disable():
    ctx = Context(tools_enabled={"obsidian": True})
    with patch.object(ctx, "save") as mock_save:
        tools.handle(ctx, "/tools disable obsidian")
    mock_save.assert_called_once()
