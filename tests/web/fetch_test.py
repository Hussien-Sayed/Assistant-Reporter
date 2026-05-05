import sys
from pathlib import Path
from unittest.mock import patch


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_fetch_extracts_title_text_and_images():
    _add_repo_root_to_syspath()

    from src.web.fetch import WebFetcher

    html = """
    <html>
      <head><title>Hello</title></head>
      <body>
        <script>var x = 1;</script>
        <h1>Headline</h1>
        <p>First para.</p>
        <img src="/img/a.png" />
        <img src="https://cdn.example.com/b.jpg" />
      </body>
    </html>
    """

    with patch("src.web.fetch.get_text", return_value=html):
        page = WebFetcher().fetch("https://example.com/news")

    assert page.title == "Hello"
    assert "Headline" in page.text
    assert "First para." in page.text
    assert "var x" not in page.text
    assert page.image_urls[0] == "https://example.com/img/a.png"
    assert page.image_urls[1] == "https://cdn.example.com/b.jpg"


def test_fetch_many_skips_empty_urls():
    _add_repo_root_to_syspath()

    from src.web.fetch import WebFetcher

    with patch("src.web.fetch.get_text", return_value="<html></html>") as gt:
        pages = WebFetcher().fetch_many(["", "  ", "https://example.com"])

    assert len(pages) == 1
    assert gt.call_count == 1


def test_fetch_wsj_ai_url():
    _add_repo_root_to_syspath()

    from src.web.fetch import WebFetcher

    fetcher = WebFetcher()
    page = fetcher.fetch("https://techcrunch.com/category/artificial-intelligence/")

    assert page.url == "https://techcrunch.com/category/artificial-intelligence/"
    assert page.title
    assert page.text
    assert isinstance(page.image_urls, list)
