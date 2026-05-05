from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from src.utils.io import ensure_parent_dir, write_text


@dataclass(frozen=True)
class ArticleLayout:
    id: str
    title: str
    summary: str
    url: str
    image_url: Optional[str]
    x: int
    y: int
    width: int
    height: int


class DashboardLayoutGenerator:
    def generate_html(self, articles: list[ArticleLayout], *, output_path: str | Path) -> Path:
        p = ensure_parent_dir(output_path)

        cards = []
        for a in articles:
            img_html = f"<img src=\"{a.image_url}\" alt=\"\" style=\"max-width:100%;height:auto;border-radius:8px\"/>" if a.image_url else ""
            cards.append(
                "\n".join(
                    [
                        f"<div class=\"card\" style=\"left:{a.x}px;top:{a.y}px;width:{a.width}px;height:{a.height}px\">",
                        f"  <h3>{_escape(a.title)}</h3>",
                        f"  {img_html}",
                        f"  <p>{_escape(a.summary)}</p>",
                        f"  <a href=\"{_escape(a.url)}\" target=\"_blank\">Open</a>",
                        "</div>",
                    ]
                )
            )

        html = "\n".join(
            [
                "<!doctype html>",
                "<html>",
                "<head>",
                "  <meta charset=\"utf-8\" />",
                "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
                "  <title>News Dashboard</title>",
                "  <style>",
                "    body { font-family: Arial, sans-serif; margin: 0; padding: 16px; background: #0b1220; color: #e5e7eb; }",
                "    .board { position: relative; width: 100%; min-height: 800px; }",
                "    .card { position: absolute; padding: 12px; border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; background: rgba(255,255,255,0.06); overflow: hidden; }",
                "    .card h3 { margin: 0 0 8px 0; font-size: 16px; }",
                "    .card p { margin: 8px 0; font-size: 14px; line-height: 1.4; color: #cbd5e1; }",
                "    .card a { color: #93c5fd; text-decoration: none; }",
                "  </style>",
                "</head>",
                "<body>",
                "  <h1 style=\"margin:0 0 12px 0;font-size:20px\">News Dashboard</h1>",
                "  <div class=\"board\">",
                *cards,
                "  </div>",
                "</body>",
                "</html>",
            ]
        )

        write_text(p, html)
        return p

    def generate_simple_grid_layout(
        self,
        articles: list[dict[str, Any]],
        *,
        card_width: int = 360,
        card_height: int = 260,
        columns: int = 3,
        gap: int = 12,
    ) -> list[ArticleLayout]:
        out: list[ArticleLayout] = []
        cols = max(1, int(columns))

        for idx, a in enumerate(articles):
            col = idx % cols
            row = idx // cols
            x = col * (card_width + gap)
            y = row * (card_height + gap)

            out.append(
                ArticleLayout(
                    id=str(a.get("id") or idx),
                    title=str(a.get("title") or ""),
                    summary=str(a.get("summary") or ""),
                    url=str(a.get("url") or ""),
                    image_url=(str(a.get("image_url")) if a.get("image_url") else None),
                    x=int(x),
                    y=int(y),
                    width=int(card_width),
                    height=int(card_height),
                )
            )

        return out


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
