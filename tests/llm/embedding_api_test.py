import sys
from pathlib import Path
from unittest.mock import Mock

import pytest


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_embedding_api_requires_api_key(monkeypatch):
    _add_repo_root_to_syspath()

    from src.llm.embedding_api import EmbeddingAPI

    monkeypatch.delenv("HUGGINGFACE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        EmbeddingAPI(model_name="m", api_key=None)


def test_generate_embedding_parses_list(monkeypatch):
    _add_repo_root_to_syspath()

    from src.llm.embedding_api import EmbeddingAPI

    api = EmbeddingAPI(model_name="m", api_key="k")
    api.client = Mock()
    api.client.feature_extraction.return_value = [0.1, 0.2]

    out = api.generate_embedding("hello")
    assert out == [0.1, 0.2]


def test_generate_embedding_parses_nested_list(monkeypatch):
    _add_repo_root_to_syspath()

    from src.llm.embedding_api import EmbeddingAPI

    api = EmbeddingAPI(model_name="m", api_key="k")
    api.client = Mock()
    api.client.feature_extraction.return_value = [[0.1, 0.2]]

    out = api.generate_embedding("hello")
    assert out == [0.1, 0.2]
