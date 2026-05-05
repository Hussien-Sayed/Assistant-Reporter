from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional


class SettingsError(RuntimeError):
    pass


def _parse_env_line(line: str) -> Optional[tuple[str, str]]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    if not key:
        return None

    return key, value


def load_dotenv(dotenv_path: str | os.PathLike[str] = ".env", *, override: bool = False) -> bool:
    path = Path(dotenv_path)
    if not path.exists() or not path.is_file():
        return False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(raw_line)
        if not parsed:
            continue

        key, value = parsed
        if not override and key in os.environ:
            continue

        os.environ[key] = value

    return True


def _get_env(name: str, *, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value == "":
        if required and default is None:
            raise SettingsError(f"Missing required environment variable: {name}")
        return default
    return value


@dataclass(frozen=True)
class Settings:
    tavily_api_key: Optional[str]
    groq_api_key: Optional[str]
    huggingface_api_key: Optional[str]
    openai_api_key: Optional[str]
    llm_model: str
    vision_model: str
    embedding_model: str
    preferred_results_k: int
    web_search_provider: str
    search_overshoot_factor: int


@lru_cache(maxsize=1)
def get_settings(*, dotenv_path: str | os.PathLike[str] = ".env") -> Settings:
    load_dotenv(dotenv_path)

    preferred_results_k_raw = _get_env("TOP_K_RESULTS", default="5")
    try:
        preferred_results_k = int(preferred_results_k_raw) if preferred_results_k_raw is not None else 5
    except ValueError as exc:
        raise SettingsError("TOP_K_RESULTS must be an integer") from exc

    overshoot_factor_raw = _get_env("SEARCH_OVERSHOOT_FACTOR", default="2")
    try:
        search_overshoot_factor = int(overshoot_factor_raw) if overshoot_factor_raw is not None else 2
    except ValueError as exc:
        raise SettingsError("SEARCH_OVERSHOOT_FACTOR must be an integer") from exc
    if search_overshoot_factor < 1:
        raise SettingsError("SEARCH_OVERSHOOT_FACTOR must be at least 1")

    return Settings(
        tavily_api_key=_get_env("TAVILY_API_KEY"),
        groq_api_key=_get_env("GROQ_API_KEY"),
        huggingface_api_key=_get_env("HUGGINGFACE_API_KEY"),
        openai_api_key=_get_env("OPENAI_API_KEY"),
        llm_model=_get_env("LLM_MODEL", default="llama-3.1-8b-instant") or "llama-3.1-8b-instant",
        vision_model=_get_env("VISION_MODEL", default="llama-3.2-11b-vision-preview")
        or "llama-3.2-11b-vision-preview",
        embedding_model=_get_env("EMBEDDING_MODEL", default="sentence-transformers/all-MiniLM-L6-v2")
        or "sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=preferred_results_k,
        web_search_provider=_get_env("WEB_SEARCH_PROVIDER", default="tavily") or "tavily",
        search_overshoot_factor=search_overshoot_factor,
    )
