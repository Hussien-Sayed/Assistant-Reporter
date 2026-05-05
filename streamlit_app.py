from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import streamlit as st
import streamlit.components.v1 as components

from src.config.settings import Settings, SettingsError
from src.main import run_app


@dataclass(frozen=True)
class DemoArticle:
    title: str
    url: str
    summary: str
    image_url: str | None


def _read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _demo_factory(_settings: Settings, _prefs_path: str | Path):
    class FakeSystem:
        def run(self, *, output_json_path):
            report = {
                "articles": [
                    {
                        "title": "Demo: Example Article",
                        "url": "https://example.com",
                        "summary": "This is a demo run (no external API calls).",
                        "image_url": None,
                    }
                ],
                "layout": [],
            }
            Path(output_json_path).write_text(json.dumps(report), encoding="utf-8")
            return report

    return FakeSystem()


def main() -> None:
    st.set_page_config(page_title="News Reporter", layout="wide")

    st.title("News Reporter")

    repo_root = Path(__file__).resolve().parent
    prefs_path = repo_root / "preferences.txt"

    with st.sidebar:
        st.header("Controls")

        demo_mode = st.toggle("Demo mode (no external APIs)", value=False)
        show_log = st.toggle("Show log in UI", value=False)

        st.subheader("Preferences")
        prefs_text = st.text_area(
            "One keyword per line",
            value=_read_text_file(prefs_path),
            height=160,
        )

        if st.button("Save preferences", use_container_width=True):
            _write_text_file(prefs_path, prefs_text.strip() + "\n" if prefs_text.strip() else "")
            st.success("Saved preferences.txt")

        run_clicked = st.button("Run", type="primary", use_container_width=True)

    output_dir = repo_root / "output"

    if run_clicked:
        output_dir.mkdir(parents=True, exist_ok=True)

        # In demo mode, we bypass real API keys by injecting a fake system + dummy settings.
        if demo_mode:
            settings = Settings(
                tavily_api_key="demo",
                groq_api_key="demo",
                huggingface_api_key="demo",
                openai_api_key="demo",
                llm_model="llama-3.1-8b-instant",
                vision_model="llama-3.2-11b-vision-preview",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                preferred_results_k=2,
                web_search_provider="fake",
                search_overshoot_factor=2,
            )
            factory: Callable[[Settings, str | Path], object] = _demo_factory
        else:
            settings = None
            factory = None

        try:
            progress_placeholder = st.empty()
            progress_messages: list[str] = []

            def progress_callback(step: str, detail: str) -> None:
                progress_messages.append(f"[{step.upper()}] {detail}")
                progress_placeholder.markdown("\n".join(progress_messages[-5:]))

            log_file = output_dir / "agent_log.txt"

            with st.spinner("Running..."):
                outputs = run_app(
                    output_dir=output_dir,
                    preferences_path=prefs_path,
                    settings=settings,
                    agentic_system_factory=factory,
                    progress_callback=progress_callback,
                    log_file_path=log_file,
                )

            st.success("Done")
            st.session_state["last_outputs"] = {
                "report_json_path": str(outputs.report_json_path),
                "dashboard_html_path": str(outputs.dashboard_html_path),
            }
            if show_log and log_file and log_file.exists():
                st.session_state["last_log_path"] = str(log_file)
        except SettingsError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.exception(exc)

    last = st.session_state.get("last_outputs")
    if not last:
        st.info("Click Run to generate the dashboard.")
        return

    report_path = Path(last["report_json_path"])
    html_path = Path(last["dashboard_html_path"])

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Report JSON")
        if report_path.exists():
            try:
                st.json(json.loads(report_path.read_text(encoding="utf-8")))
            except Exception:
                st.code(report_path.read_text(encoding="utf-8"), language="json")
        else:
            st.warning(f"Missing file: {report_path}")

    with col2:
        st.subheader("Dashboard Preview")
        if html_path.exists():
            components.html(html_path.read_text(encoding="utf-8"), height=900, scrolling=True)
        else:
            st.warning(f"Missing file: {html_path}")

    log_path = st.session_state.get("last_log_path")
    if log_path:
        st.subheader("Agent Log")
        log_file = Path(log_path)
        if log_file.exists():
            st.code(log_file.read_text(encoding="utf-8"), language="text")
        else:
            st.warning(f"Missing log file: {log_path}")


if __name__ == "__main__":
    main()
