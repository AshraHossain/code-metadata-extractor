"""Heuristic docstring quality scoring — no LLM, pure string matching."""
from __future__ import annotations

import re
from typing import Literal, Optional

DocstringStyle = Literal["numpy", "google", "sphinx", "unstructured", "none"]

# ── style detection ───────────────────────────────────────────────────────────

# Sphinx: :param name:  :type name:  :returns:  :rtype:
_RE_SPHINX = re.compile(r":(param|type|returns?|rtype)\b")

# NumPy: section headers underlined with dashes
#   Parameters
#   ----------
_RE_NUMPY = re.compile(r"^\s*(Parameters|Returns|Raises|Notes|Examples|Attributes)\s*\n\s*-{3,}", re.MULTILINE)

# Google: "Args:\n    ", "Returns:\n    "
_RE_GOOGLE = re.compile(r"^\s*(Args|Returns|Raises|Note|Example|Attributes)\s*:\s*\n\s+\S", re.MULTILINE)

# Section presence (style-agnostic)
_RE_ARGS = re.compile(
    r"(^\s*(Args|Parameters|Params)\s*[:\n]|:param\s+\w|Parameters\s*\n\s*-{3,})",
    re.MULTILINE | re.IGNORECASE,
)
_RE_RETURNS = re.compile(
    r"(^\s*(Returns?|Return value)\s*[:\n]|:returns?:|:rtype:|Returns\s*\n\s*-{3,})",
    re.MULTILINE | re.IGNORECASE,
)
_RE_EXAMPLE = re.compile(
    r"(^\s*(Examples?)\s*[:\n]|>>>\s|\bExample\b)",
    re.MULTILINE | re.IGNORECASE,
)


def _detect_style(doc: str) -> DocstringStyle:
    if _RE_SPHINX.search(doc):
        return "sphinx"
    if _RE_NUMPY.search(doc):
        return "numpy"
    if _RE_GOOGLE.search(doc):
        return "google"
    return "unstructured"


# ── scoring ───────────────────────────────────────────────────────────────────

def _quality_score(
    presence: bool,
    length: int,
    has_args: bool,
    has_return: bool,
    has_example: bool,
) -> float:
    if not presence:
        return 0.0
    score = 0.2                          # base: docstring exists
    score += 0.2 if has_args else 0.0
    score += 0.2 if has_return else 0.0
    score += 0.2 if has_example else 0.0
    score += 0.1 if length >= 50 else 0.0
    score += 0.1 if length >= 200 else 0.0
    return round(min(score, 1.0), 4)


# ── public API ────────────────────────────────────────────────────────────────

def score_docstring(docstring: Optional[str]) -> dict:
    """Return a DocstringQuality-shaped dict for one function/method/class.

    Args:
        docstring: raw docstring text, or None.

    Returns:
        Dict matching the DocstringQuality schema.
    """
    if not docstring:
        return {
            "presence": False,
            "length": 0,
            "has_args_section": False,
            "has_return_section": False,
            "has_example": False,
            "style": "none",
            "quality_score": 0.0,
        }

    has_args = bool(_RE_ARGS.search(docstring))
    has_return = bool(_RE_RETURNS.search(docstring))
    has_example = bool(_RE_EXAMPLE.search(docstring))
    length = len(docstring)

    return {
        "presence": True,
        "length": length,
        "has_args_section": has_args,
        "has_return_section": has_return,
        "has_example": has_example,
        "style": _detect_style(docstring),
        "quality_score": _quality_score(True, length, has_args, has_return, has_example),
    }


def enrich_docstrings(parsed: dict) -> dict:
    """Attach docstring_quality to every function and class in a parsed-file dict."""

    def _attach_fn(fn: dict) -> dict:
        fn["docstring_quality"] = score_docstring(fn.get("docstring"))
        return fn

    parsed["functions"] = [_attach_fn(f) for f in parsed.get("functions", [])]
    for cls in parsed.get("classes", []):
        cls["docstring_quality"] = score_docstring(cls.get("docstring"))
        cls["methods"] = [_attach_fn(m) for m in cls.get("methods", [])]
    return parsed
