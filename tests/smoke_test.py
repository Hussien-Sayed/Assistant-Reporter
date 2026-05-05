import json
import sys
from pathlib import Path


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_run_app_writes_outputs(tmp_path):
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.main import run_app

    settings = Settings(
        tavily_api_key="g",
        groq_api_key="groq",
        huggingface_api_key="hf",
        openai_api_key="oai",
        llm_model="llama-3.1-8b-instant",
        vision_model="llama-3.2-11b-vision-preview",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        preferred_results_k=2,
        web_search_provider="tavily",
        search_overshoot_factor=2,
    )

    def factory(_settings, _prefs):
        class FakeSystem:
            def run(self, *, output_json_path):
                report = {
                    "articles": [
                        {
                            "title": "A",
                            "url": "https://example.com",
                            "summary": "S",
                            "image_url": None,
                        }
                    ],
                    "layout": [],
                }
                Path(output_json_path).write_text(json.dumps(report), encoding="utf-8")
                return report

        return FakeSystem()

    outputs = run_app(
        output_dir=tmp_path,
        preferences_path=tmp_path / "preferences.txt",
        settings=settings,
        agentic_system_factory=factory,
        progress_callback=lambda step, detail: None,
        log_file_path=None,
    )

    assert outputs.report_json_path.exists()
    assert outputs.dashboard_html_path.exists()

    html = outputs.dashboard_html_path.read_text(encoding="utf-8")
    assert "News Dashboard" in html
    assert "https://example.com" in html
