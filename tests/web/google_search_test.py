import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_google_search_client_requires_keys(monkeypatch):
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.config.settings import SettingsError
    from src.web.google_search import GoogleSearchClient

    settings = Settings(
        tavily_api_key=None,
        groq_api_key=None,
        huggingface_api_key=None,
        openai_api_key=None,
        llm_model="llama-3.1-8b-instant",
        vision_model="llama-3.2-11b-vision-preview",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=5,
        web_search_provider="tavily",
        search_overshoot_factor=2,
    )

    with pytest.raises(SettingsError):
        GoogleSearchClient(settings=settings)


def test_search_returns_results():
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.web.google_search import GoogleSearchClient

    settings = Settings(
        tavily_api_key="k",
        groq_api_key=None,
        huggingface_api_key=None,
        openai_api_key=None,
        llm_model="llama-3.1-8b-instant",
        vision_model="llama-3.2-11b-vision-preview",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=5,
        web_search_provider="tavily",
        search_overshoot_factor=2,
    )

    fake_payload = {
        "results": [
            {"title": "T1", "url": "https://a.com", "content": "S1"},
            {"title": "T2", "url": "https://b.com", "content": "S2"},
        ]
    }

    with patch("src.web.tavily_search.post_json", return_value=fake_payload) as gj:
        client = GoogleSearchClient(settings=settings)
        out = client.search("q", num_results=2)

    assert len(out) == 2
    assert out[0].link == "https://a.com"
    assert out[1].title == "T2"
    gj.assert_called_once()


def test_search_empty_query_returns_empty():
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.web.google_search import GoogleSearchClient

    settings = Settings(
        tavily_api_key="k",
        groq_api_key=None,
        huggingface_api_key=None,
        openai_api_key=None,
        llm_model="llama-3.1-8b-instant",
        vision_model="llama-3.2-11b-vision-preview",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=5,
        web_search_provider="tavily",
        search_overshoot_factor=2,
    )

    client = GoogleSearchClient(settings=settings)
    with patch("src.web.tavily_search.post_json") as gj:
        assert client.search("   ") == []
        gj.assert_not_called()
