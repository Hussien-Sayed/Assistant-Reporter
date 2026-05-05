from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.utils.http import HttpError, RetryConfig, get_text


@dataclass(frozen=True)
class FetchedPage:
    url: str
    title: str
    text: str
    image_urls: list[str]


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return str(soup.title.string).strip()

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(" ", strip=True)

    return ""


def _extract_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    body = soup.body or soup
    text = body.get_text(" ", strip=True)
    return text


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src:
            continue
        abs_url = urljoin(base_url, src)
        if abs_url in seen:
            continue
        seen.add(abs_url)
        out.append(abs_url)

    return out


class WebFetcher:
    def fetch(self, url: str, *, retry: RetryConfig | None = None, timeout_seconds: float = 20.0) -> FetchedPage:
        html = get_text(url, retry=retry, timeout_seconds=timeout_seconds)
        soup = BeautifulSoup(html, "html.parser")
        title = _extract_title(soup)
        text = _extract_text(soup)
        image_urls = _extract_images(soup, url)
        return FetchedPage(url=url, title=title, text=text, image_urls=image_urls)

    def fetch_many(self, urls: Iterable[str], *, retry: RetryConfig | None = None) -> list[FetchedPage]:
        pages: list[FetchedPage] = []
        for u in urls:
            u = (u or "").strip()
            if not u:
                continue
            try:
                pages.append(self.fetch(u, retry=retry))
            except HttpError as exc:
                # Skip failed URLs (e.g., paywalls, 401, 404)
                # The agent will use the overshoot factor to get enough successful pages
                continue
        return pages
