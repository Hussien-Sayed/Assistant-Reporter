from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.config.settings import Settings, SettingsError, get_settings
from src.utils.http import RetryConfig, post_json


@dataclass(frozen=True)
class SearchResult:
    title: str
    link: str
    snippet: str


class TavilySearchClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        settings: Optional[Settings] = None,
        base_url: str = "https://api.tavily.com",
    ) -> None:
        if settings is None:
            settings = get_settings()

        self._api_key = api_key or settings.tavily_api_key
        self._base_url = base_url.rstrip("/")

        if not self._api_key:
            raise SettingsError("TAVILY_API_KEY is required for TavilySearchClient")

    def search(self, query: str, *, num_results: int = 5, retry: RetryConfig | None = None) -> list[SearchResult]:
        if not query or not query.strip():
            return []

        url = f"{self._base_url}/search"
        payload: dict[str, Any] = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max(1, min(int(num_results), 10)),
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
        }

        data = post_json(url, json_body=payload, retry=retry)
        results = data.get("results") if isinstance(data, dict) else None
        if not results:
            return []

        out: list[SearchResult] = []
        for it in results:
            if not isinstance(it, dict):
                continue
            title = str(it.get("title") or "").strip()
            link = str(it.get("url") or it.get("link") or "").strip()
            snippet = str(it.get("content") or it.get("snippet") or "").strip()
            if not link:
                continue
            out.append(SearchResult(title=title, link=link, snippet=snippet))

        return out
