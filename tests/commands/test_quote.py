from unittest.mock import patch, MagicMock
import requests
from context import Context
from commands import quote


def test_quote_from_api():
    ctx = Context()
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"q": "Teste ta volonté.", "a": "Marc Aurèle"}]
    with patch("requests.get", return_value=mock_resp):
        result = quote.handle(ctx, "/quote")
    assert result.ok
    assert "Teste ta volonté." in result.message
    assert "Marc Aurèle" in result.message


def test_quote_fallback_on_error():
    ctx = Context()
    with patch("requests.get", side_effect=requests.RequestException("timeout")):
        result = quote.handle(ctx, "/quote")
    assert result.ok
    assert "💬" in result.message
    assert "—" in result.message
