import sys
from pathlib import Path
from unittest.mock import Mock, patch


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_agentic_system_run_writes_report(tmp_path, monkeypatch):
    _add_repo_root_to_syspath()

    from src.config.settings import Settings
    from src.agents.news_reporter_graph import NewsReporterAgenticSystem

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

    prefs = tmp_path / "preferences.txt"
    prefs.write_text("ai\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    fake_results = [Mock(link="https://a.com", title="A", snippet="s")]

    fake_page = Mock(
        url="https://a.com",
        title="A",
        text="Some content",
        image_urls=["https://a.com/i.png"],
    )

    with patch("src.agents.news_reporter_graph.TavilySearchClient") as SearchCls, patch(
        "src.agents.news_reporter_graph.WebFetcher"
    ) as FetchCls, patch("src.agents.news_reporter_graph.LLMAPI") as LlmCls, patch(
        "src.agents.news_reporter_graph.VisionLlmClient"
    ) as VisionCls:
        SearchCls.return_value.search.return_value = fake_results
        FetchCls.return_value.fetch_many.return_value = [fake_page]
        LlmCls.return_value.generate_response.return_value = "summary"
        VisionCls.return_value.describe_image_url.return_value.description = "desc"

        system = NewsReporterAgenticSystem(settings=settings, preferences_path=prefs, progress_callback=lambda step, detail: None, log_file_path=None)
        out_path = tmp_path / "layout.json"
        report = system.run(output_json_path=out_path)

    assert out_path.exists()
    assert len(report["articles"]) == 1
    assert "<image_description>" in report["articles"][0]["summary"]
