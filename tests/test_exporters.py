"""Tests for JSON and CSV exporters."""
import csv
import json
from pathlib import Path

import pytest

from code_metadata.cli import extract_repo
from code_metadata.exporters import to_csv, to_json

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def repo():
    return extract_repo(FIXTURE_DIR, include_git=False)


# ── JSON ──────────────────────────────────────────────────────────────────────

def test_to_json_returns_string(repo):
    text = to_json(repo)
    assert isinstance(text, str)
    assert len(text) > 0


def test_to_json_valid_json(repo):
    data = json.loads(to_json(repo))
    assert "files" in data
    assert "total_functions" in data


def test_to_json_write_file(tmp_path, repo):
    out = tmp_path / "meta.json"
    to_json(repo, out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert "files" in data


def test_to_json_functions_present(repo):
    data = json.loads(to_json(repo))
    # flatten all functions across all files
    all_fns = [fn for f in data["files"] for fn in f["functions"]]
    names = [fn["name"] for fn in all_fns]
    assert "simple_function" in names


# ── CSV ───────────────────────────────────────────────────────────────────────

def test_to_csv_returns_string(repo):
    text = to_csv(repo)
    assert isinstance(text, str)


def test_to_csv_has_header(repo):
    text = to_csv(repo)
    rows = list(csv.DictReader(text.splitlines()))
    assert len(rows) > 0
    assert "name" in rows[0]
    assert "cyclomatic_complexity" in rows[0]
    assert "docstring_score" in rows[0]


def test_to_csv_write_file(tmp_path, repo):
    out = tmp_path / "meta.csv"
    to_csv(repo, out)
    assert out.exists()
    rows = list(csv.DictReader(out.read_text().splitlines()))
    assert len(rows) > 0


def test_to_csv_function_in_rows(repo):
    rows = list(csv.DictReader(to_csv(repo).splitlines()))
    names = [r["name"] for r in rows]
    assert "simple_function" in names


def test_to_csv_methods_included(repo):
    rows = list(csv.DictReader(to_csv(repo).splitlines()))
    names = [r["name"] for r in rows]
    assert "__init__" in names


def test_to_csv_empty_repo_returns_empty(tmp_path):
    # directory with no .py files
    from code_metadata.schema import RepositoryMetadata
    from datetime import datetime, timezone
    empty_repo = RepositoryMetadata(
        repository_path=str(tmp_path),
        analyzed_at=datetime.now(tz=timezone.utc),
        total_functions=0,
        total_classes=0,
        total_files=0,
        files=[],
    )
    assert to_csv(empty_repo) == ""
