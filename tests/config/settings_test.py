import os
import sys
from pathlib import Path

import pytest


def _add_repo_root_to_syspath() -> Path:
    # tests/... -> repo root
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_load_dotenv_sets_env_vars(tmp_path, monkeypatch):
    repo_root = _add_repo_root_to_syspath()
    assert repo_root.exists()

    from src.config.settings import load_dotenv

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("FOO=bar\n# comment\nEMPTY=\nQUOTED=\"x\"\n", encoding="utf-8")

    monkeypatch.delenv("FOO", raising=False)
    monkeypatch.delenv("QUOTED", raising=False)

    loaded = load_dotenv(dotenv_file)
    assert loaded is True
    assert os.getenv("FOO") == "bar"
    assert os.getenv("QUOTED") == "x"


def test_get_settings_reads_values_and_parses_top_k(tmp_path, monkeypatch):
    _add_repo_root_to_syspath()

    from src.config import settings as settings_module

    settings_module.get_settings.cache_clear()

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text(
        "TAVILY_API_KEY=key\nGROQ_API_KEY=groq\nHUGGINGFACE_API_KEY=hf\nOPENAI_API_KEY=oai\nLLM_MODEL=m\nVISION_MODEL=vm\nEMBEDDING_MODEL=e\nTOP_K_RESULTS=7\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("HUGGINGFACE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("VISION_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("TOP_K_RESULTS", raising=False)

    s = settings_module.get_settings(dotenv_path=dotenv_file)
    assert s.tavily_api_key == "key"
    assert s.groq_api_key == "groq"
    assert s.huggingface_api_key == "hf"
    assert s.openai_api_key == "oai"
    assert s.llm_model == "m"
    assert s.vision_model == "vm"
    assert s.embedding_model == "e"
    assert s.preferred_results_k == 7
    assert s.web_search_provider == "tavily"
    assert s.search_overshoot_factor == 2


def test_get_settings_raises_on_invalid_top_k(tmp_path, monkeypatch):
    _add_repo_root_to_syspath()

    from src.config import settings as settings_module
    from src.config.settings import SettingsError

    settings_module.get_settings.cache_clear()

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("TOP_K_RESULTS=not_an_int\n", encoding="utf-8")

    monkeypatch.delenv("TOP_K_RESULTS", raising=False)

    with pytest.raises(SettingsError):
        settings_module.get_settings(dotenv_path=dotenv_file)
