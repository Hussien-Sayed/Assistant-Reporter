# News Reporter

A small Python project that gathers news pages, summarizes them, and generates a simple HTML dashboard.

## Requirements

- Python 3.10+ (tested on Python 3.12)

## Setup

1) Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Run (Streamlit UI)

```bash
streamlit run streamlit_app.py
```

- Use the sidebar to edit/save `preferences.txt`
- Click **Run** to generate:
  - `output/layout.json`
  - `output/dashboard.html`

### Demo mode

The Streamlit app includes a **Demo mode** toggle that runs without external API calls.

## Run (CLI)

```bash
python -m src.main
```

This will also generate `output/layout.json` and `output/dashboard.html`.

## Notes

- Modules under `src/rag/` are currently **placeholders** because they are meant to be copied from your `chatbot-school` project. The current pipeline does not depend on them yet.
- External calls:
  - Tavily Search API (requires `TAVILY_API_KEY`)
  - Groq API for summarization (requires `GROQ_API_KEY`)
  - HuggingFace Inference API for embeddings (requires `HUGGINGFACE_API_KEY`)
  - Optional: Groq vision model for image description (uses `GROQ_API_KEY` + `VISION_MODEL`)
