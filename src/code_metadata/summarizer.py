"""Optional LLM summarization via Anthropic API (claude-haiku-4-5-20251001)."""
from __future__ import annotations

from typing import Optional


def _client():
    try:
        import anthropic
        return anthropic.Anthropic()
    except ImportError:
        raise ImportError("Install anthropic: pip install 'code-metadata[llm]'")


def summarize_function(name: str, docstring: Optional[str], source_lines: str) -> str:
    """Return a one-sentence summary of a function via Claude Haiku."""
    client = _client()
    prompt = (
        f"Summarize this Python function in one sentence (max 20 words). "
        f"Focus on what it does, not its structure.\n\n"
        f"Name: {name}\n"
        f"Docstring: {docstring or 'None'}\n"
        f"Source:\n{source_lines}\n\n"
        f"Reply with just the summary sentence, no quotes."
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=80,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def enrich_summaries(parsed: dict, source: str) -> dict:
    """Attach LLM-generated summary to each function/method in a parsed file dict."""
    lines = source.splitlines()

    def _src(fn: dict) -> str:
        start = max(0, fn.get("line_number", 1) - 1)
        end = fn.get("end_line_number", start + 1)
        return "\n".join(lines[start:end])

    for fn in parsed.get("functions", []):
        fn["summary"] = summarize_function(fn["name"], fn.get("docstring"), _src(fn))

    for cls in parsed.get("classes", []):
        for m in cls.get("methods", []):
            m["summary"] = summarize_function(m["name"], m.get("docstring"), _src(m))

    return parsed
