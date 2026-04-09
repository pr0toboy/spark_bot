from unittest.mock import patch
from context import Context
from commands import login


def test_login_anthropic_valid():
    ctx = Context()
    with patch("getpass.getpass", return_value="sk-ant-valid123"):
        with patch.object(ctx, "save") as mock_save:
            result = login.handle(ctx, "/login anthropic")
    assert result.ok
    assert ctx.api_key == "sk-ant-valid123"
    mock_save.assert_called_once()


def test_login_groq_valid():
    ctx = Context()
    with patch("getpass.getpass", return_value="gsk_valid123"):
        with patch.object(ctx, "save") as mock_save:
            result = login.handle(ctx, "/login groq")
    assert result.ok
    assert ctx.groq_api_key == "gsk_valid123"
    mock_save.assert_called_once()


def test_login_anthropic_invalid_key():
    ctx = Context()
    with patch("getpass.getpass", return_value="bad-key"):
        result = login.handle(ctx, "/login anthropic")
    assert not result.ok
    assert ctx.api_key == ""


def test_login_groq_invalid_key():
    ctx = Context()
    with patch("getpass.getpass", return_value="bad-key"):
        result = login.handle(ctx, "/login groq")
    assert not result.ok
    assert ctx.groq_api_key == ""


def test_login_unknown_provider():
    ctx = Context()
    result = login.handle(ctx, "/login openai")
    assert not result.ok


def test_login_empty_key():
    ctx = Context()
    with patch("getpass.getpass", return_value=""):
        result = login.handle(ctx, "/login anthropic")
    assert not result.ok


def test_login_no_provider_prompts(monkeypatch):
    ctx = Context()
    inputs = iter(["anthropic"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))
    with patch("getpass.getpass", return_value="sk-ant-abc"):
        with patch.object(ctx, "save"):
            result = login.handle(ctx, "/login")
    assert result.ok
    assert ctx.api_key == "sk-ant-abc"
