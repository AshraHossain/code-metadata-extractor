"""Tests for git_utils — covers both git and non-git paths."""
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from code_metadata.git_utils import (
    _blame_lines,
    enrich_git,
    get_repo,
    git_metadata_for_lines,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_module.py"


# ── non-git fallback ──────────────────────────────────────────────────────────

def test_get_repo_non_git(tmp_path):
    result = get_repo(tmp_path)
    assert result is None


def test_git_metadata_non_git_returns_none(tmp_path):
    py = tmp_path / "x.py"
    py.write_text("def f(): pass\n")
    result = git_metadata_for_lines(py, 1, 1)
    assert result is None


def test_enrich_git_non_git_sets_none(tmp_path):
    py = tmp_path / "x.py"
    py.write_text("def f(): pass\n")
    parsed = {
        "file_path": str(py),
        "functions": [{"name": "f", "line_number": 1, "end_line_number": 1}],
        "classes": [],
    }
    result = enrich_git(parsed)
    assert result["functions"][0]["git_metadata"] is None


# ── mock-based git path ───────────────────────────────────────────────────────

def _make_commit(author="Alice", email="alice@example.com", ts=1_700_000_000, sha="abc123"):
    commit = MagicMock()
    commit.author.name = author
    commit.author.email = email
    commit.authored_date = ts
    commit.hexsha = sha
    return commit


def test_git_metadata_returns_dict_when_blame_available(tmp_path):
    """Smoke test the happy path via a minimal fake repo."""
    # set up a fake git.Repo
    fake_commit = _make_commit()
    fake_repo = MagicMock()
    fake_repo.working_tree_dir = str(tmp_path)
    fake_repo.blame.return_value = [(fake_commit, ["line1", "line2"])]
    fake_repo.iter_commits.return_value = iter([fake_commit])

    py = tmp_path / "mod.py"
    py.write_text("def f():\n    pass\n")

    with patch("code_metadata.git_utils._find_repo", return_value=fake_repo):
        result = git_metadata_for_lines(py, 1, 2)

    assert result is not None
    assert result["author"] == "Alice"
    assert result["author_email"] == "alice@example.com"
    assert isinstance(result["last_modified"], datetime)
    assert result["commit_count"] == 1


def test_git_metadata_picks_most_recent(tmp_path):
    """When multiple commits in range, most-recent wins."""
    old_commit = _make_commit(author="Bob", ts=1_000_000_000, sha="old111")
    new_commit = _make_commit(author="Alice", ts=1_700_000_000, sha="new222")
    fake_repo = MagicMock()
    fake_repo.working_tree_dir = str(tmp_path)
    fake_repo.blame.return_value = [
        (old_commit, ["line1"]),
        (new_commit, ["line2", "line3"]),
    ]
    fake_repo.iter_commits.return_value = iter([old_commit, new_commit])

    py = tmp_path / "mod.py"
    py.write_text("def f():\n    x = 1\n    return x\n")

    with patch("code_metadata.git_utils._find_repo", return_value=fake_repo):
        result = git_metadata_for_lines(py, 1, 3)

    assert result["author"] == "Alice"


def test_blame_error_returns_none(tmp_path):
    fake_repo = MagicMock()
    fake_repo.working_tree_dir = str(tmp_path)
    fake_repo.blame.side_effect = Exception("git error")

    py = tmp_path / "mod.py"
    py.write_text("def f(): pass\n")

    with patch("code_metadata.git_utils._find_repo", return_value=fake_repo):
        result = git_metadata_for_lines(py, 1, 1)

    assert result is None


def test_enrich_git_populates_classes(tmp_path):
    fake_commit = _make_commit()
    fake_repo = MagicMock()
    fake_repo.working_tree_dir = str(tmp_path)
    fake_repo.blame.return_value = [(fake_commit, ["l1", "l2", "l3", "l4", "l5"])]
    fake_repo.iter_commits.return_value = iter([fake_commit])

    py = tmp_path / "mod.py"
    py.write_text("class C:\n    def m(self):\n        pass\n")

    parsed = {
        "file_path": str(py),
        "functions": [],
        "classes": [{
            "name": "C",
            "line_number": 1,
            "end_line_number": 3,
            "methods": [{"name": "m", "line_number": 2, "end_line_number": 3}],
        }],
    }

    with patch("code_metadata.git_utils._find_repo", return_value=fake_repo):
        result = enrich_git(parsed)

    cls = result["classes"][0]
    assert cls["git_metadata"] is not None
    assert cls["methods"][0]["git_metadata"] is not None


def test_commit_count_in_result(tmp_path):
    commits = [_make_commit(sha=f"sha{i}") for i in range(5)]
    fake_repo = MagicMock()
    fake_repo.working_tree_dir = str(tmp_path)
    fake_repo.blame.return_value = [(commits[0], ["line1"])]
    fake_repo.iter_commits.return_value = iter(commits)

    py = tmp_path / "mod.py"
    py.write_text("def f(): pass\n")

    with patch("code_metadata.git_utils._find_repo", return_value=fake_repo):
        result = git_metadata_for_lines(py, 1, 1)

    assert result["commit_count"] == 5
