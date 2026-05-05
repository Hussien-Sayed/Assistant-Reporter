import sys
from pathlib import Path
from unittest.mock import patch
import os
from dotenv import load_dotenv

import pytest

# Load .env file to get environment variables
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_vision_client_requires_api_key():
    _add_repo_root_to_syspath()

    from src.config.settings import Settings, SettingsError
    from src.llm.vision_llm_api import VisionLlmClient

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

    client = VisionLlmClient(settings=settings)
    with pytest.raises(SettingsError):
        client.describe_image_url("https://example.com/cat.png")


def test_describe_image_url_returns_description():
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.llm.vision_llm_api import VisionLlmClient

    settings = Settings(
        tavily_api_key="k",
        groq_api_key="k",
        huggingface_api_key=None,
        openai_api_key="k",
        llm_model="llama-3.1-8b-instant",
        vision_model="llama-3.2-11b-vision-preview",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=5,
        web_search_provider="tavily",
        search_overshoot_factor=2,
    )

    class _Msg:
        content = "a cat"

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    with patch("src.llm.vision_llm_api.groq.Groq") as GroqCls:
        GroqCls.return_value.chat.completions.create.return_value = _Resp()
        client = VisionLlmClient(settings=settings)
        out = client.describe_image_url("https://example.com/cat.png")

    assert out.description == "a cat"
    assert out.model == "llama-3.2-11b-vision-preview"


def test_describe_image_url_empty_returns_empty_description():
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.llm.vision_llm_api import VisionLlmClient

    settings = Settings(
        tavily_api_key=None,
        groq_api_key=None,
        huggingface_api_key=None,
        openai_api_key="k",
        llm_model="llama-3.1-8b-instant",
        vision_model="llama-3.2-11b-vision-preview",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=5,
        web_search_provider="tavily",
        search_overshoot_factor=2,
    )

    client = VisionLlmClient(settings=settings)
    out = client.describe_image_url("   ")
    assert out.description == ""


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
def test_describe_image_url_real_image():
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.llm.vision_llm_api import VisionLlmClient

    settings = Settings(
        tavily_api_key=None,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        huggingface_api_key=None,
        openai_api_key=None,
        llm_model="llama-3.1-8b-instant",
        vision_model="meta-llama/llama-4-scout-17b-16e-instruct",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=5,
        web_search_provider="tavily",
        search_overshoot_factor=2,
    )

    client = VisionLlmClient(settings=settings)
    out = client.describe_image_url("https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=800")
    assert out.description
    assert len(out.description) > 0
    assert out.model == "meta-llama/llama-4-scout-17b-16e-instruct"

