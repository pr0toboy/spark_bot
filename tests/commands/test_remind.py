from unittest.mock import patch, MagicMock
from context import Context
from commands import remind


def test_parse_duration_minutes():
    assert remind._parse_duration("10min") == 600
    assert remind._parse_duration("10 minutes") == 600
    assert remind._parse_duration("1 minute") == 60


def test_parse_duration_seconds():
    assert remind._parse_duration("30s") == 30
    assert remind._parse_duration("30 secondes") == 30


def test_parse_duration_hours():
    assert remind._parse_duration("1h") == 3600
    assert remind._parse_duration("2 heures") == 7200


def test_parse_duration_invalid():
    assert remind._parse_duration("blabla") is None
    assert remind._parse_duration("") is None


def test_remind_creates_timer():
    ctx = Context()
    with patch("threading.Timer") as mock_timer:
        mock_timer.return_value = MagicMock()
        result = remind.handle(ctx, "/remind boire de l'eau, 10min")
    mock_timer.assert_called_once_with(600, mock_timer.call_args[0][1])
    assert result.ok
    assert "✅" in result.message


def test_remind_invalid_format():
    ctx = Context()
    result = remind.handle(ctx, "/remind sans virgule")
    assert not result.ok
    assert "❌" in result.message


def test_remind_invalid_duration():
    ctx = Context()
    result = remind.handle(ctx, "/remind boire, demain")
    assert not result.ok
    assert "❌" in result.message
