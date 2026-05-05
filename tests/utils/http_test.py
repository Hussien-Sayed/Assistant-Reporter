import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_get_json_success():
    _add_repo_root_to_syspath()

    from src.utils.http import get_json

    response = Mock()
    response.status_code = 200
    response.json.return_value = {"ok": True}

    with patch("requests.request", return_value=response) as req:
        data = get_json("https://example.com")

    assert data == {"ok": True}
    req.assert_called_once()


def test_request_retries_on_5xx_then_succeeds(monkeypatch):
    _add_repo_root_to_syspath()

    from src.utils import http

    response1 = Mock()
    response1.status_code = 500
    response1.text = "server error"

    response2 = Mock()
    response2.status_code = 200
    response2.text = "ok"

    monkeypatch.setattr(http, "_sleep_backoff", lambda *_args, **_kwargs: None)

    with patch("requests.request", side_effect=[response1, response2]) as req:
        resp = http.request("GET", "https://example.com")

    assert resp.status_code == 200
    assert req.call_count == 2


def test_request_raises_on_4xx_no_retry(monkeypatch):
    _add_repo_root_to_syspath()

    from src.utils import http
    from src.utils.http import HttpError

    response = Mock()
    response.status_code = 404
    response.text = "not found"

    monkeypatch.setattr(http, "_sleep_backoff", lambda *_args, **_kwargs: None)

    with patch("requests.request", return_value=response) as req:
        with pytest.raises(HttpError) as exc:
            http.request("GET", "https://example.com")

    assert "HTTP 404" in str(exc.value)
    assert req.call_count == 1
