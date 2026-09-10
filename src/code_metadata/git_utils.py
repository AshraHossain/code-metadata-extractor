"""Git blame integration — cached per file, optional (null on non-git repos)."""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:
    import git
    _GIT_AVAILABLE = True
except ImportError:
    _GIT_AVAILABLE = False


# ── repo discovery ────────────────────────────────────────────────────────────

@lru_cache(maxsize=16)
def _find_repo(path: str) -> Optional[object]:
    """Return a git.Repo for the given path, or None if not a git repo."""
    if not _GIT_AVAILABLE:
        return None
    try:
        return git.Repo(path, search_parent_directories=True)
    except Exception:
        return None


def get_repo(path: str | Path) -> Optional[object]:
    return _find_repo(str(Path(path).resolve()))


# ── per-file blame cache ──────────────────────────────────────────────────────

@lru_cache(maxsize=256)
def _blame_lines(repo_path: str, rel_file: str) -> list[dict]:
    """Return per-line blame list (1-indexed; index 0 is a dummy placeholder).

    Each entry: {author, author_email, date: datetime, sha: str}
    One call per file — cached by (repo_path, rel_file).
    """
    repo = _find_repo(repo_path)
    if repo is None:
        return []
    try:
        blame = repo.blame("HEAD", rel_file)
    except Exception:
        return []

    lines: list[dict] = [{}]  # index 0 unused so line 1 == lines[1]
    for commit, file_lines in blame:
        entry = {
            "author": commit.author.name,
            "author_email": commit.author.email,
            "date": datetime.fromtimestamp(commit.authored_date, tz=timezone.utc),
            "sha": commit.hexsha,
        }
        for _ in file_lines:
            lines.append(entry)
    return lines


def _commit_count(repo: object, rel_file: str) -> int:
    try:
        return sum(1 for _ in repo.iter_commits(paths=rel_file))
    except Exception:
        return 0


# ── public API ────────────────────────────────────────────────────────────────

def git_metadata_for_lines(
    file_path: str | Path,
    start_line: int,
    end_line: int,
) -> Optional[dict]:
    """Return git metadata covering [start_line, end_line] (1-based), or None.

    Picks the most-recent commit in the line range as "last modified".
    """
    abs_path = Path(file_path).resolve()
    repo = get_repo(abs_path)
    if repo is None:
        return None

    repo_root = Path(repo.working_tree_dir).resolve()
    try:
        rel_file = str(abs_path.relative_to(repo_root))
    except ValueError:
        return None

    blame = _blame_lines(str(repo_root), rel_file)
    if not blame:
        return None

    # slice lines in range (clamp to available)
    relevant = [
        blame[i]
        for i in range(start_line, min(end_line + 1, len(blame)))
        if blame[i]
    ]
    if not relevant:
        return None

    # most-recent commit in range
    latest = max(relevant, key=lambda e: e["date"])

    commit_cnt = _commit_count(repo, rel_file)

    return {
        "last_modified": latest["date"],
        "author": latest["author"],
        "author_email": latest["author_email"],
        "commit_count": commit_cnt,
    }


def enrich_git(parsed: dict) -> dict:
    """Attach git_metadata to every function and class in a parsed-file dict."""
    file_path = parsed.get("file_path", "")

    def _attach(fn: dict) -> dict:
        fn["git_metadata"] = git_metadata_for_lines(
            file_path, fn["line_number"], fn["end_line_number"]
        )
        return fn

    parsed["functions"] = [_attach(f) for f in parsed.get("functions", [])]
    for cls in parsed.get("classes", []):
        cls["methods"] = [_attach(m) for m in cls.get("methods", [])]
        cls["git_metadata"] = git_metadata_for_lines(
            file_path, cls["line_number"], cls["end_line_number"]
        )
    return parsed
