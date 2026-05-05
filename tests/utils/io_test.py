import json
import sys
from pathlib import Path

import pytest


def _add_repo_root_to_syspath() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    return repo_root


def test_read_lines_strips_and_ignores_empty(tmp_path):
    _add_repo_root_to_syspath()

    from src.utils.io import read_lines

    p = tmp_path / "prefs.txt"
    p.write_text("  a \n\n b\n", encoding="utf-8")

    lines = read_lines(p)
    assert lines == ["a", "b"]


def test_read_preferences_default_path(tmp_path, monkeypatch):
    _add_repo_root_to_syspath()

    from src.utils.io import read_preferences

    prefs = tmp_path / "preferences.txt"
    prefs.write_text("x\ny\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    assert read_preferences() == ["x", "y"]


def test_write_text_creates_parent_dirs(tmp_path):
    _add_repo_root_to_syspath()

    from src.utils.io import write_text

    out = tmp_path / "a" / "b" / "c.txt"
    write_text(out, "hello")
    assert out.read_text(encoding="utf-8") == "hello"


def test_write_json_writes_json(tmp_path):
    _add_repo_root_to_syspath()

    from src.utils.io import write_json

    out = tmp_path / "out.json"
    write_json(out, {"a": 1})
    assert json.loads(out.read_text(encoding="utf-8")) == {"a": 1}


def test_join_nonempty():
    _add_repo_root_to_syspath()

    from src.utils.io import join_nonempty

    assert join_nonempty(["a", None, " ", "b"]) == "a\nb"
