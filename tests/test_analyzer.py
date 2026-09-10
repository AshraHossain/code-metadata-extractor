"""Tests for the analyzer module."""
from pathlib import Path

import pytest

from code_metadata.analyzer import (
    build_test_index,
    enrich_file,
    extract_dependencies,
    file_raw_metrics,
)
from code_metadata.parser import parse_file

FIXTURE = Path(__file__).parent / "fixtures" / "sample_module.py"
FIXTURE_SOURCE = FIXTURE.read_text()
FIXTURE_DIR = FIXTURE.parent


@pytest.fixture(scope="module")
def enriched():
    parsed = parse_file(FIXTURE)
    test_index = build_test_index(FIXTURE_DIR)
    return enrich_file(parsed, FIXTURE_SOURCE, test_index)


# ── raw metrics ───────────────────────────────────────────────────────────────

def test_raw_metrics_returns_sloc():
    m = file_raw_metrics(FIXTURE_SOURCE)
    assert m["sloc"] > 0
    assert m["loc"] >= m["sloc"]


def test_raw_metrics_bad_source():
    m = file_raw_metrics("def oops(:\n    pass\n")
    # radon may raise or return zeros — must not crash
    assert isinstance(m["sloc"], int)


# ── complexity enrichment ─────────────────────────────────────────────────────

def test_complexity_field_present(enriched):
    fn = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    assert "complexity" in fn


def test_cyclomatic_complexity_minimum(enriched):
    fn = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    assert fn["complexity"]["cyclomatic_complexity"] >= 1


def test_complex_function_higher_cc(enriched):
    simple = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    complex_fn = next(f for f in enriched["functions"] if f["name"] == "complex_function")
    assert complex_fn["complexity"]["cyclomatic_complexity"] > simple["complexity"]["cyclomatic_complexity"]


def test_loc_positive(enriched):
    fn = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    assert fn["complexity"]["lines_of_code"] > 0


def test_private_fields_removed(enriched):
    fn = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    assert "_loc" not in fn
    assert "_docstring_lines" not in fn


# ── dependencies ──────────────────────────────────────────────────────────────

def test_dependencies_list(enriched):
    fn = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    assert isinstance(fn["complexity"]["dependencies"], list)


def test_extract_dependencies_direct():
    import ast as _ast
    src = "import os\ndef fn():\n    os.path.join('a', 'b')\n"
    tree = _ast.parse(src)
    fn_node = next(n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef))
    deps = extract_dependencies(fn_node, ["os"])
    assert any("os" in d for d in deps)


def test_extract_dependencies_no_match():
    import ast as _ast
    src = "def fn():\n    x = len([1, 2, 3])\n"
    tree = _ast.parse(src)
    fn_node = next(n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef))
    deps = extract_dependencies(fn_node, [])
    assert deps == []


# ── test-coverage inference ───────────────────────────────────────────────────

def test_build_test_index_returns_dict():
    index = build_test_index(FIXTURE_DIR)
    assert isinstance(index, dict)


def test_test_index_finds_simple_function():
    # test_sample_module.py has test_simple_function → maps to "simple_function"
    index = build_test_index(FIXTURE_DIR)
    assert "simple_function" in index


def test_has_test_flag_true(enriched):
    fn = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    assert fn["complexity"]["has_test"] is True


def test_has_test_flag_false(enriched):
    # complex_function has no matching test_ entry
    fn = next(f for f in enriched["functions"] if f["name"] == "complex_function")
    assert fn["complexity"]["has_test"] is False


def test_test_files_list_populated(enriched):
    fn = next(f for f in enriched["functions"] if f["name"] == "simple_function")
    assert len(fn["complexity"]["test_files"]) > 0


# ── class methods enriched ────────────────────────────────────────────────────

def test_class_methods_get_complexity(enriched):
    cls = next(c for c in enriched["classes"] if c["name"] == "SampleClass")
    init = next(m for m in cls["methods"] if m["name"] == "__init__")
    assert "complexity" in init
    assert init["complexity"]["cyclomatic_complexity"] >= 1


# ── error resilience ──────────────────────────────────────────────────────────

def test_enrich_bad_source_no_crash(tmp_path):
    bad_py = tmp_path / "bad.py"
    bad_py.write_text("def oops(:\n    pass\n")
    parsed = parse_file(bad_py)
    result = enrich_file(parsed, bad_py.read_text(), {})
    assert result["functions"] == []
