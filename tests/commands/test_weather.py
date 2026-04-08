from unittest.mock import patch, MagicMock
from context import Context
from commands import weather


MOCK_IPINFO = {"ip": "1.2.3.4", "city": "Paris", "loc": "48.8534,2.3488"}
MOCK_WEATHER = {"current_weather": {"temperature": 15.2, "windspeed": 12.5, "weathercode": 3}}


def test_weather_displays_info():
    ctx = Context()
    mock_resp = MagicMock()
    mock_resp.json.side_effect = [MOCK_IPINFO, MOCK_WEATHER]
    with patch("requests.get", return_value=mock_resp):
        result = weather.handle(ctx, "/weather")
    assert result.ok
    assert "Paris" in result.message
    assert "15.2" in result.message
    assert "12.5" in result.message
    assert "☁️" in result.message  # code 3 = Couvert


def test_weather_handles_error():
    ctx = Context()
    import requests
    with patch("requests.get", side_effect=requests.RequestException("timeout")):
        result = weather.handle(ctx, "/weather")
    assert not result.ok
    assert "❌" in result.message


def test_wc_emoji_known_code():
    emoji, desc = weather._wc_emoji(0)
    assert emoji == "☀️"
    assert "dégagé" in desc.lower()


def test_wc_emoji_unknown_code():
    emoji, desc = weather._wc_emoji(999)
    assert emoji == "❓"
