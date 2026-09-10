"""Tests for the AST parser."""
from pathlib import Path

import pytest

from code_metadata.parser import parse_file

FIXTURE = Path(__file__).parent / "fixtures" / "sample_module.py"


@pytest.fixture(scope="module")
def parsed():
    return parse_file(FIXTURE)


def test_file_path_recorded(parsed):
    assert parsed["file_path"].endswith("sample_module.py")


def test_total_lines_positive(parsed):
    assert parsed["total_lines"] > 0


def test_top_level_functions_found(parsed):
    names = [f["name"] for f in parsed["functions"]]
    assert "simple_function" in names
    assert "no_docstring" in names
    assert "async_function" in names
    assert "complex_function" in names


def test_class_not_in_functions(parsed):
    names = [f["name"] for f in parsed["functions"]]
    assert "SampleClass" not in names
    assert "__init__" not in names  # methods stay inside class


def test_classes_found(parsed):
    names = [c["name"] for c in parsed["classes"]]
    assert "SampleClass" in names
    assert "ChildClass" in names


def test_function_line_numbers(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "simple_function")
    assert fn["line_number"] > 0
    assert fn["end_line_number"] >= fn["line_number"]


def test_function_params(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "simple_function")
    param_names = [p["name"] for p in fn["params"]]
    assert "x" in param_names
    assert "y" in param_names


def test_type_hints_captured(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "simple_function")
    x_param = next(p for p in fn["params"] if p["name"] == "x")
    assert x_param["type_hint"] == "int"
    assert fn["return_type"] == "int"


def test_docstring_captured(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "simple_function")
    assert fn["docstring"] is not None
    assert "Add two numbers" in fn["docstring"]


def test_no_docstring_is_none(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "no_docstring")
    assert fn["docstring"] is None


def test_async_flag(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "async_function")
    assert fn["is_async"] is True


def test_sync_flag(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "simple_function")
    assert fn["is_async"] is False


def test_is_method_false_for_top_level(parsed):
    fn = next(f for f in parsed["functions"] if f["name"] == "simple_function")
    assert fn["is_method"] is False


def test_class_methods_present(parsed):
    cls = next(c for c in parsed["classes"] if c["name"] == "SampleClass")
    method_names = [m["name"] for m in cls["methods"]]
    assert "__init__" in method_names
    assert "static_method" in method_names
    assert "from_string" in method_names


def test_method_is_method_flag(parsed):
    cls = next(c for c in parsed["classes"] if c["name"] == "SampleClass")
    init = next(m for m in cls["methods"] if m["name"] == "__init__")
    assert init["is_method"] is True
    assert init["parent_class"] == "SampleClass"


def test_class_bases(parsed):
    child = next(c for c in parsed["classes"] if c["name"] == "ChildClass")
    assert "SampleClass" in child["bases"]


def test_class_docstring(parsed):
    cls = next(c for c in parsed["classes"] if c["name"] == "SampleClass")
    assert cls["docstring"] is not None


def test_imports_captured(parsed):
    assert len(parsed["imports"]) > 0
    assert "os" in parsed["imports"]


def test_syntax_error_file(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def oops(:\n    pass\n")
    result = parse_file(bad)
    assert result["functions"] == []
    assert "parse_error" in result


def test_empty_file(tmp_path):
    empty = tmp_path / "empty.py"
    empty.write_text("")
    result = parse_file(empty)
    assert result["functions"] == []
    assert result["classes"] == []
