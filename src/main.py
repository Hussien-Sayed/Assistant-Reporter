from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from src.agents.news_reporter_graph import NewsReporterAgenticSystem
from src.config.settings import Settings, SettingsError, get_settings
from src.layout.dashboard_layout_generator import DashboardLayoutGenerator, ArticleLayout
from src.utils.io import ensure_parent_dir, write_json


@dataclass(frozen=True)
class RunOutputs:
    report_json_path: Path
    dashboard_html_path: Path


def run_app(
    *,
    output_dir: str | Path = "output",
    preferences_path: str | Path = "preferences.txt",
    settings: Optional[Settings] = None,
    agentic_system_factory: Optional[Callable[[Settings, str | Path], NewsReporterAgenticSystem]] = None,
    progress_callback: Optional[Callable[[str, str], None]] = None,
    log_file_path: str | Path = "output/agent_log.txt",
) -> RunOutputs:
    settings = settings or get_settings()
    output_dir_p = Path(output_dir)

    def _default_factory(s: Settings, prefs: str | Path) -> NewsReporterAgenticSystem:
        return NewsReporterAgenticSystem(
            settings=s,
            preferences_path=prefs,
            progress_callback=progress_callback,
            log_file_path=log_file_path,
        )

    factory = agentic_system_factory or _default_factory
    system = factory(settings, preferences_path)

    report_path = ensure_parent_dir(output_dir_p / "layout.json")
    report = system.run(output_json_path=report_path)

    # Render HTML from report (articles + computed grid layout)
    articles = report.get("articles") or []
    layout_gen = DashboardLayoutGenerator()
    layouts = layout_gen.generate_simple_grid_layout(articles, columns=3)

    html_path = ensure_parent_dir(output_dir_p / "dashboard.html")
    layout_gen.generate_html(layouts, output_path=html_path)

    # Ensure report json exists even if the injected system didn't write it.
    if not report_path.exists():
        write_json(report_path, report)

    return RunOutputs(report_json_path=Path(report_path), dashboard_html_path=Path(html_path))


def main() -> int:
    try:
        run_app()
        return 0
    except SettingsError as exc:
        print(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
