import sys
from pathlib import Path
from unittest.mock import Mock

import pytest


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_llmapi_requires_api_key(monkeypatch):
    _add_repo_root_to_syspath()

    from src.llm.llm_api import LLMAPI

    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(ValueError):
        LLMAPI(model_name="m", api_key=None)


def test_llmapi_generate_response_parses_content(monkeypatch):
    _add_repo_root_to_syspath()

    from src.llm.llm_api import LLMAPI

    # Avoid importing real groq client; override the instance client with a stub.
    api = LLMAPI(model_name="m", api_key="k")

    fake_response = Mock()
    fake_choice = Mock()
    fake_choice.message.content = " hi "
    fake_response.choices = [fake_choice]

    api.client = Mock()
    api.client.chat.completions.create.return_value = fake_response

    out = api.generate_response("hello")
    assert out == "hi"
