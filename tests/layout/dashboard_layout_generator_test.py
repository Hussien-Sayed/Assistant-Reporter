import sys
from pathlib import Path


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_generate_simple_grid_layout_positions():
    _add_repo_root_to_syspath()

    from src.layout.dashboard_layout_generator import DashboardLayoutGenerator

    articles = [
        {"id": "a", "title": "t", "summary": "s", "url": "u"},
        {"id": "b", "title": "t", "summary": "s", "url": "u"},
        {"id": "c", "title": "t", "summary": "s", "url": "u"},
        {"id": "d", "title": "t", "summary": "s", "url": "u"},
    ]

    layouts = DashboardLayoutGenerator().generate_simple_grid_layout(
        articles, card_width=100, card_height=50, columns=2, gap=10
    )

    assert layouts[0].x == 0 and layouts[0].y == 0
    assert layouts[1].x == 110 and layouts[1].y == 0
    assert layouts[2].x == 0 and layouts[2].y == 60
    assert layouts[3].x == 110 and layouts[3].y == 60


def test_generate_html_writes_file(tmp_path):
    _add_repo_root_to_syspath()

    from src.layout.dashboard_layout_generator import ArticleLayout, DashboardLayoutGenerator

    layouts = [
        ArticleLayout(
            id="1",
            title="A",
            summary="B",
            url="https://example.com",
            image_url=None,
            x=0,
            y=0,
            width=200,
            height=100,
        )
    ]

    out = tmp_path / "dashboard.html"
    DashboardLayoutGenerator().generate_html(layouts, output_path=out)

    assert out.exists()
    data = out.read_text(encoding="utf-8")
    assert "News Dashboard" in data
    assert "https://example.com" in data
