from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.utils.http import RetryConfig
from src.web.fetch import FetchedPage


class FakeWebFetcher:
    def __init__(self, *, settings: object | None = None) -> None:
        _unused = settings
        self._pages: dict[str, FetchedPage] = {}

    def set_page(self, page: FetchedPage) -> None:
        self._pages[page.url] = page

    def fetch(self, url: str, *, retry: RetryConfig | None = None, timeout_seconds: float = 20.0) -> FetchedPage:
        _unused = (retry, timeout_seconds)
        if url in self._pages:
            return self._pages[url]

        return FetchedPage(
            url=url,
            title=f"Fake title for: {url}",
            text=f"This is fake content for the URL: {url}. In a real scenario, this would contain the actual article content.",
            image_urls=[],
        )

    def fetch_many(self, urls: Iterable[str], *, retry: RetryConfig | None = None) -> list[FetchedPage]:
        _unused = retry
        pages: list[FetchedPage] = []
        for u in urls:
            u = (u or "").strip()
            if not u:
                continue
            pages.append(self.fetch(u))
        return pages
