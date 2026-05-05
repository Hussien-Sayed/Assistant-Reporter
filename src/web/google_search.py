from __future__ import annotations

from typing import Optional

from src.config.settings import Settings
from src.utils.http import RetryConfig
from src.web.tavily_search import SearchResult, TavilySearchClient


class GoogleSearchClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        cse_id: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        _unused = (cse_id,)
        self._client = TavilySearchClient(api_key=api_key, settings=settings)

    def search(self, query: str, *, num_results: int = 5, retry: RetryConfig | None = None) -> list[SearchResult]:
        return self._client.search(query, num_results=num_results, retry=retry)
