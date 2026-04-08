from unittest.mock import patch, MagicMock
from context import Context
from commands import localize


MOCK_RESPONSE = {
    "ip": "1.2.3.4",
    "city": "Paris",
    "region": "Île-de-France",
    "country": "FR",
    "loc": "48.8534,2.3488",
    "org": "AS12345 Free SAS",
}


def test_localize_displays_info():
    ctx = Context()
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_RESPONSE
    with patch("requests.get", return_value=mock_resp):
        result = localize.handle(ctx, "/localize")
    assert result.ok
    assert "Paris" in result.message
    assert "1.2.3.4" in result.message
    assert "Île-de-France" in result.message


def test_localize_handles_error():
    ctx = Context()
    import requests
    with patch("requests.get", side_effect=requests.RequestException("timeout")):
        result = localize.handle(ctx, "/localize")
    assert not result.ok
    assert "❌" in result.message
