from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional


def read_lines(path: str | Path, *, strip: bool = True, ignore_empty: bool = True) -> list[str]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(str(p))

    lines = p.read_text(encoding="utf-8").splitlines()
    if strip:
        lines = [ln.strip() for ln in lines]
    if ignore_empty:
        lines = [ln for ln in lines if ln]
    return lines


def read_preferences(path: str | Path = "preferences.txt") -> list[str]:
    return read_lines(path, strip=True, ignore_empty=True)


def ensure_parent_dir(path: str | Path) -> Path:
    p = Path(path)
    parent = p.parent
    parent.mkdir(parents=True, exist_ok=True)
    return p


def write_text(path: str | Path, content: str, *, encoding: str = "utf-8") -> Path:
    p = ensure_parent_dir(path)
    p.write_text(content, encoding=encoding)
    return p


def write_json(
    path: str | Path,
    data: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> Path:
    p = ensure_parent_dir(path)
    p.write_text(json.dumps(data, indent=indent, ensure_ascii=ensure_ascii), encoding="utf-8")
    return p


def join_nonempty(parts: Iterable[Optional[str]], *, sep: str = "\n") -> str:
    cleaned = [p for p in parts if p is not None and str(p).strip()]
    return sep.join([str(p) for p in cleaned])
