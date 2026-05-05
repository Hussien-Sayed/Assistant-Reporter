from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.utils.http import RetryConfig


@dataclass(frozen=True)
class SearchResult:
    title: str
    link: str
    snippet: str


class FakeSearchClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        settings: Optional[object] = None,
    ) -> None:
        _unused = (api_key, settings)
        self._results: list[SearchResult] = []

    def set_results(self, results: list[SearchResult]) -> None:
        self._results = results

    def search(self, query: str, *, num_results: int = 5, retry: RetryConfig | None = None) -> list[SearchResult]:
        _unused = (retry,)
        if not query or not query.strip():
            return []

        if not self._results:
            return [
                SearchResult(
                    title=f"Fake result for: {query}",
                    link=f"https://fake.example.com/{query.replace(' ', '-')}",
                    snippet=f"This is a fake search result snippet for the query: {query}",
                )
            ]

        return self._results[:num_results]
