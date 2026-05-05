from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
from datetime import datetime

from src.config.settings import Settings, get_settings
from src.layout.dashboard_layout_generator import DashboardLayoutGenerator
from src.utils.io import read_preferences, write_json
from src.web.fake_fetch import FakeWebFetcher
from src.web.fake_search import FakeSearchClient, SearchResult
from src.web.fetch import WebFetcher
from src.web.google_search import GoogleSearchClient
from src.web.tavily_search import TavilySearchClient
from src.llm.llm_api import LLMAPI
from src.llm.vision_llm_api import VisionLlmClient


@dataclass(frozen=True)
class ArticleSummary:
    title: str
    url: str
    summary: str
    image_url: Optional[str]


class NewsReporterAgenticSystem:
    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        preferences_path: str | Path = "preferences.txt",
        top_k: Optional[int] = None,
        progress_callback: Optional[Callable[[str, str], None]] = None,
        log_file_path: str | Path = "output/agent_log.txt",
    ) -> None:
        self._settings = settings or get_settings()
        self._preferences_path = preferences_path
        self._top_k = int(top_k) if top_k is not None else int(self._settings.preferred_results_k)
        self._log_file_path = Path(log_file_path) if log_file_path else None
        if self._log_file_path:
            self._log_file_path.parent.mkdir(parents=True, exist_ok=True)

        def _combined_callback(step: str, detail: str) -> None:
            if progress_callback:
                progress_callback(step, detail)
            if self._log_file_path:
                timestamp = datetime.now().isoformat()
                self._log_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._log_file_path, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] [{step.upper()}] {detail}\n")

        self._progress_callback = _combined_callback

        provider = self._settings.web_search_provider.lower()
        if provider == "fake":
            self._search = FakeSearchClient(settings=self._settings)
            self._fetcher = FakeWebFetcher(settings=self._settings)
        elif provider == "google":
            self._search = GoogleSearchClient(settings=self._settings)
            self._fetcher = WebFetcher()
        else:
            self._search = TavilySearchClient(settings=self._settings)
            self._fetcher = WebFetcher()

        self._llm = LLMAPI(model_name=self._settings.llm_model, api_key=self._settings.groq_api_key)
        self._vision = None
        if self._settings.groq_api_key:
            self._vision = VisionLlmClient(settings=self._settings)
        self._layout = DashboardLayoutGenerator()

    def _make_queries(self, keywords: list[str]) -> list[str]:
        if not keywords:
            return []
        base = " ".join(keywords[:8])
        return [f"{base} latest news", f"{base} breaking news"]

    def _summarize_page(self, title: str, url: str, text: str) -> str:
        prompt = "\n".join(
            [
                "Summarize the following news article in 3-5 bullet points.",
                f"Title: {title}",
                f"URL: {url}",
                "Content:",
                text[:8000],
            ]
        )
        return self._llm.generate_response(prompt)

    def _describe_image(self, image_url: Optional[str]) -> Optional[str]:
        if not image_url:
            return None
        if self._vision is None:
            return None

        # Skip unsupported formats (e.g., SVG) that vision models can't process
        url_lower = image_url.lower()
        if url_lower.endswith(".svg") or ".svg?" in url_lower:
            self._progress_callback("vision", f"Skipping SVG image (unsupported format): {image_url}")
            return None

        try:
            self._progress_callback("vision", f"Describing image: {image_url}")
            desc = self._vision.describe_image_url(image_url).description
            if not desc:
                return None
            return f"<image_description>{desc}</image_description>"
        except Exception as exc:
            self._progress_callback("vision", f"Failed to describe image, continuing without it: {exc}")
            return None

    def _content_check(self, summary: str) -> bool:
        return bool(summary and summary.strip())

    def run(
        self,
        *,
        output_json_path: str | Path = "output/layout.json",
    ) -> dict[str, Any]:
        self._progress_callback("start", "Reading preferences and generating search queries")
        keywords = read_preferences(self._preferences_path)
        queries = self._make_queries(keywords)
        self._progress_callback("search", f"Searching for {len(queries)} queries: {', '.join(queries)}")

        num_results_per_query = self._top_k * self._settings.search_overshoot_factor
        self._progress_callback("search", f"Requesting {num_results_per_query} results per query (overshoot factor: {self._settings.search_overshoot_factor})")

        all_results: list[SearchResult] = []
        for idx, q in enumerate(queries):
            self._progress_callback("search", f"Running query {idx + 1}/{len(queries)}: {q}")
            all_results.extend(self._search.search(q, num_results=num_results_per_query))

        self._progress_callback("deduplicate", f"Deduplicating {len(all_results)} search results")
        unique_urls: list[str] = []
        seen: set[str] = set()
        for r in all_results:
            if r.link in seen:
                continue
            seen.add(r.link)
            unique_urls.append(r.link)

        self._progress_callback("fetch", f"Fetching {len(unique_urls)} unique URLs")
        pages = self._fetcher.fetch_many(unique_urls)
        self._progress_callback("fetch", f"Successfully fetched {len(pages)} pages (skipped {len(unique_urls) - len(pages)} failures)")

        # Take only the first N successful pages (the rest are overshoot for fallback)
        pages = pages[: self._top_k]
        self._progress_callback("summarize", f"Summarizing {len(pages)} fetched pages (target: {self._top_k})")
        summaries: list[ArticleSummary] = []
        for idx, p in enumerate(pages):
            self._progress_callback("summarize", f"Summarizing page {idx + 1}/{len(pages)}: {p.title or p.url}")
            s = self._summarize_page(p.title, p.url, p.text)
            if not self._content_check(s):
                self._progress_callback("summarize", f"Skipped page {idx + 1}/{len(pages)} (empty summary)")
                continue

            image_url = p.image_urls[0] if p.image_urls else None
            img_desc = self._describe_image(image_url)
            final_summary = s if not img_desc else f"{s}\n{img_desc}"

            summaries.append(
                ArticleSummary(
                    title=p.title or p.url,
                    url=p.url,
                    summary=final_summary,
                    image_url=image_url,
                )
            )

        self._progress_callback("layout", f"Generating layout for {len(summaries)} articles")
        layout_items = self._layout.generate_simple_grid_layout(
            [
                {
                    "id": str(i),
                    "title": a.title,
                    "summary": a.summary,
                    "url": a.url,
                    "image_url": a.image_url,
                }
                for i, a in enumerate(summaries)
            ],
            columns=3,
        )

        self._progress_callback("finalizing", "Building final report and writing to disk")
        report = {
            "articles": [
                {
                    "title": a.title,
                    "url": a.url,
                    "summary": a.summary,
                    "image_url": a.image_url,
                }
                for a in summaries
            ],
            "layout": [
                {
                    "id": li.id,
                    "x": li.x,
                    "y": li.y,
                    "width": li.width,
                    "height": li.height,
                }
                for li in layout_items
            ],
        }

        write_json(output_json_path, report)
        self._progress_callback("complete", f"Done! Generated report with {len(summaries)} articles")
        return report
