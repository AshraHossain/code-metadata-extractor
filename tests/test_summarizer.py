"""Tests for the summarizer module (mocked Anthropic client)."""
from unittest.mock import MagicMock, patch

import pytest


def _make_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


@patch("code_metadata.summarizer._client")
def test_summarize_function_returns_string(mock_client):
    client = MagicMock()
    client.messages.create.return_value = _make_response("Adds two numbers.")
    mock_client.return_value = client

    from code_metadata.summarizer import summarize_function
    result = summarize_function("add", "Add two numbers.", "def add(a, b):\n    return a + b")
    assert isinstance(result, str)
    assert result == "Adds two numbers."


@patch("code_metadata.summarizer._client")
def test_summarize_function_strips_whitespace(mock_client):
    client = MagicMock()
    client.messages.create.return_value = _make_response("  Parses a file.  ")
    mock_client.return_value = client

    from code_metadata.summarizer import summarize_function
    result = summarize_function("parse", None, "def parse(): pass")
    assert result == "Parses a file."


@patch("code_metadata.summarizer._client")
def test_enrich_summaries_attaches_to_functions(mock_client):
    client = MagicMock()
    client.messages.create.return_value = _make_response("Does something.")
    mock_client.return_value = client

    from code_metadata.summarizer import enrich_summaries
    parsed = {
        "functions": [{"name": "fn", "line_number": 1, "end_line_number": 2}],
        "classes": [],
    }
    result = enrich_summaries(parsed, "def fn():\n    pass")
    assert result["functions"][0]["summary"] == "Does something."


@patch("code_metadata.summarizer._client")
def test_enrich_summaries_attaches_to_methods(mock_client):
    client = MagicMock()
    client.messages.create.return_value = _make_response("Method summary.")
    mock_client.return_value = client

    from code_metadata.summarizer import enrich_summaries
    parsed = {
        "functions": [],
        "classes": [{"name": "C", "methods": [{"name": "m", "line_number": 1, "end_line_number": 2}]}],
    }
    result = enrich_summaries(parsed, "def m():\n    pass")
    assert result["classes"][0]["methods"][0]["summary"] == "Method summary."


def test_client_raises_import_error_without_anthropic():
    import sys
    from unittest.mock import patch
    # Block the import by injecting None into sys.modules
    with patch.dict(sys.modules, {"anthropic": None}):
        import importlib
        import code_metadata.summarizer as s
        importlib.reload(s)
        with pytest.raises(ImportError, match="anthropic"):
            s._client()
    # Restore the real module object after context exits
    importlib.reload(s)
