"""Tests for docstring heuristic scorer."""
import pytest

from code_metadata.docstring_scorer import enrich_docstrings, score_docstring

# ── none / missing ────────────────────────────────────────────────────────────

def test_none_docstring():
    r = score_docstring(None)
    assert r["presence"] is False
    assert r["style"] == "none"
    assert r["quality_score"] == 0.0
    assert r["length"] == 0


def test_empty_string():
    r = score_docstring("")
    assert r["presence"] is False
    assert r["quality_score"] == 0.0


# ── presence ──────────────────────────────────────────────────────────────────

def test_minimal_docstring_present():
    r = score_docstring("Do a thing.")
    assert r["presence"] is True
    assert r["length"] > 0
    assert r["quality_score"] >= 0.2


# ── style detection ───────────────────────────────────────────────────────────

def test_sphinx_style():
    doc = "Do something.\n\n:param x: the input\n:returns: the output\n:rtype: int"
    r = score_docstring(doc)
    assert r["style"] == "sphinx"


def test_numpy_style():
    doc = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n\n"
        "Returns\n"
        "-------\n"
        "int\n"
        "    The result.\n"
    )
    r = score_docstring(doc)
    assert r["style"] == "numpy"


def test_google_style():
    doc = (
        "Do something.\n\n"
        "Args:\n"
        "    x (int): The value.\n\n"
        "Returns:\n"
        "    int: The result.\n"
    )
    r = score_docstring(doc)
    assert r["style"] == "google"


def test_unstructured_style():
    doc = "Just a plain description with no sections."
    r = score_docstring(doc)
    assert r["style"] == "unstructured"


# ── section detection ─────────────────────────────────────────────────────────

def test_has_args_google():
    doc = "Summary.\n\nArgs:\n    x: value.\n"
    r = score_docstring(doc)
    assert r["has_args_section"] is True


def test_has_args_sphinx():
    doc = "Summary.\n\n:param x: the input\n"
    r = score_docstring(doc)
    assert r["has_args_section"] is True


def test_has_args_numpy():
    doc = "Summary.\n\nParameters\n----------\nx : int\n"
    r = score_docstring(doc)
    assert r["has_args_section"] is True


def test_no_args_section():
    doc = "Just a summary, nothing more."
    r = score_docstring(doc)
    assert r["has_args_section"] is False


def test_has_return_google():
    doc = "Summary.\n\nReturns:\n    int: something.\n"
    r = score_docstring(doc)
    assert r["has_return_section"] is True


def test_has_return_sphinx():
    doc = "Summary.\n\n:returns: the value\n"
    r = score_docstring(doc)
    assert r["has_return_section"] is True


def test_no_return_section():
    doc = "Summary with no return info."
    r = score_docstring(doc)
    assert r["has_return_section"] is False


def test_has_example_doctest():
    doc = "Summary.\n\n>>> fn(1)\n2\n"
    r = score_docstring(doc)
    assert r["has_example"] is True


def test_has_example_section():
    doc = "Summary.\n\nExample:\n    fn(1)\n"
    r = score_docstring(doc)
    assert r["has_example"] is True


def test_no_example():
    doc = "Summary with no examples."
    r = score_docstring(doc)
    assert r["has_example"] is False


# ── quality score ─────────────────────────────────────────────────────────────

def test_score_increases_with_sections():
    minimal = score_docstring("Short.")
    full = score_docstring(
        "Summary.\n\nArgs:\n    x: val.\n\nReturns:\n    int: result.\n\nExample:\n    >>> fn(1)\n"
    )
    assert full["quality_score"] > minimal["quality_score"]


def test_score_bounded_0_to_1():
    perfect = (
        "A very long docstring that exceeds 200 characters to test length bonuses. " * 4
        + "Args:\n    x: value.\n\nReturns:\n    int: result.\n\nExample:\n    >>> fn(1)\n"
    )
    r = score_docstring(perfect)
    assert 0.0 <= r["quality_score"] <= 1.0


def test_score_full_marks():
    doc = (
        "A " * 110  # > 200 chars
        + "\n\nArgs:\n    x: val.\n\nReturns:\n    int: res.\n\nExample:\n    >>> fn(1)\n"
    )
    r = score_docstring(doc)
    assert r["quality_score"] == 1.0


# ── enrich_docstrings integration ─────────────────────────────────────────────

def test_enrich_attaches_to_functions():
    parsed = {
        "functions": [
            {"name": "f", "docstring": "Do thing.\n\nArgs:\n    x: val.\n"},
            {"name": "g", "docstring": None},
        ],
        "classes": [],
    }
    result = enrich_docstrings(parsed)
    assert result["functions"][0]["docstring_quality"]["presence"] is True
    assert result["functions"][1]["docstring_quality"]["presence"] is False


def test_enrich_attaches_to_class_and_methods():
    parsed = {
        "functions": [],
        "classes": [{
            "name": "C",
            "docstring": "A class.",
            "methods": [
                {"name": "m", "docstring": None},
            ],
        }],
    }
    result = enrich_docstrings(parsed)
    cls = result["classes"][0]
    assert cls["docstring_quality"]["presence"] is True
    assert cls["methods"][0]["docstring_quality"]["presence"] is False
