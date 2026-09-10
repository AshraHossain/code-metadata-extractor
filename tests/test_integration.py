"""End-to-end integration tests — full pipeline on fixture directory."""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from code_metadata.cli import app, extract_repo
from code_metadata.schema import RepositoryMetadata

FIXTURE_DIR = Path(__file__).parent / "fixtures"
runner = CliRunner()


@pytest.fixture(scope="module")
def repo():
    return extract_repo(FIXTURE_DIR, include_git=False)


# ── schema validation ─────────────────────────────────────────────────────────

def test_extract_repo_returns_repository_metadata(repo):
    assert isinstance(repo, RepositoryMetadata)


def test_total_files_positive(repo):
    assert repo.total_files > 0


def test_total_functions_positive(repo):
    assert repo.total_functions > 0


def test_total_classes_positive(repo):
    assert repo.total_classes > 0


def test_all_functions_have_complexity(repo):
    for file in repo.files:
        for fn in file.functions:
            assert fn.complexity is not None
            assert fn.complexity.cyclomatic_complexity >= 1


def test_all_functions_have_docstring_quality(repo):
    for file in repo.files:
        for fn in file.functions:
            assert fn.docstring_quality is not None
            assert 0.0 <= fn.docstring_quality.quality_score <= 1.0


def test_git_metadata_none_when_skipped(repo):
    for file in repo.files:
        for fn in file.functions:
            assert fn.git_metadata is None


def test_simple_function_full_metadata(repo):
    all_fns = [fn for f in repo.files for fn in f.functions]
    fn = next((f for f in all_fns if f.name == "simple_function"), None)
    assert fn is not None
    assert fn.return_type == "int"
    assert fn.docstring_quality.has_args_section is True
    assert fn.docstring_quality.has_return_section is True
    assert fn.complexity.has_test is True


def test_async_function_flagged(repo):
    all_fns = [fn for f in repo.files for fn in f.functions]
    fn = next((f for f in all_fns if f.name == "async_function"), None)
    assert fn is not None
    assert fn.is_async is True


def test_methods_under_class(repo):
    all_classes = [cls for f in repo.files for cls in f.classes]
    sample = next((c for c in all_classes if c.name == "SampleClass"), None)
    assert sample is not None
    method_names = [m.name for m in sample.methods]
    assert "__init__" in method_names


# ── CLI ───────────────────────────────────────────────────────────────────────

def test_cli_json_output():
    result = runner.invoke(app, [str(FIXTURE_DIR), "--format", "json", "--no-git"])
    assert result.exit_code == 0
    # strip rich status lines before the JSON object
    json_start = result.output.index("{")
    data = json.loads(result.output[json_start:])
    assert "files" in data


def test_cli_csv_output():
    result = runner.invoke(app, [str(FIXTURE_DIR), "--format", "csv", "--no-git"])
    assert result.exit_code == 0
    assert "simple_function" in result.output


def test_cli_write_json_file(tmp_path):
    out = tmp_path / "out.json"
    result = runner.invoke(app, [str(FIXTURE_DIR), "--format", "json", "--output", str(out), "--no-git"])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "files" in data


def test_cli_write_csv_file(tmp_path):
    out = tmp_path / "out.csv"
    result = runner.invoke(app, [str(FIXTURE_DIR), "--format", "csv", "--output", str(out), "--no-git"])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_bad_path():
    result = runner.invoke(app, ["/nonexistent/path"])
    assert result.exit_code == 1


def test_cli_bad_format():
    result = runner.invoke(app, [str(FIXTURE_DIR), "--format", "xml", "--no-git"])
    assert result.exit_code == 1
