from context import Context
from commands import model
from commands.model import DEFAULT_ANTHROPIC, DEFAULT_GROQ, ANTHROPIC_MODELS, GROQ_MODELS


def test_model_show_defaults():
    ctx = Context()
    result = model.handle(ctx, "/model")
    assert result.ok
    assert DEFAULT_ANTHROPIC in result.message
    assert DEFAULT_GROQ in result.message


def test_model_show_custom():
    ctx = Context(anthropic_model="claude-haiku-4-5", groq_model="gemma2-9b-it")
    result = model.handle(ctx, "/model")
    assert result.ok
    assert "claude-haiku-4-5" in result.message
    assert "gemma2-9b-it" in result.message


def test_model_list():
    result = model.handle(Context(), "/model list")
    assert result.ok
    for m in ANTHROPIC_MODELS + GROQ_MODELS:
        assert m in result.message


def test_model_set_anthropic_valid():
    ctx = Context()
    with __import__("unittest.mock", fromlist=["patch"]).patch.object(ctx, "save") as mock_save:
        result = model.handle(ctx, "/model anthropic claude-haiku-4-5")
    assert result.ok
    assert ctx.anthropic_model == "claude-haiku-4-5"
    mock_save.assert_called_once()


def test_model_set_groq_valid():
    ctx = Context()
    with __import__("unittest.mock", fromlist=["patch"]).patch.object(ctx, "save") as mock_save:
        result = model.handle(ctx, "/model groq gemma2-9b-it")
    assert result.ok
    assert ctx.groq_model == "gemma2-9b-it"
    mock_save.assert_called_once()


def test_model_set_anthropic_invalid():
    ctx = Context()
    result = model.handle(ctx, "/model anthropic gpt-4o")
    assert not result.ok
    assert ctx.anthropic_model == ""


def test_model_set_groq_invalid():
    ctx = Context()
    result = model.handle(ctx, "/model groq gpt-4o")
    assert not result.ok
    assert ctx.groq_model == ""


def test_model_unknown_provider():
    ctx = Context()
    result = model.handle(ctx, "/model openai gpt-4o")
    assert not result.ok


def test_model_missing_model_arg():
    ctx = Context()
    result = model.handle(ctx, "/model anthropic")
    assert not result.ok
