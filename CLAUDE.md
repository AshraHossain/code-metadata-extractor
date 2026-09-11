# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# code-metadata-extractor

Python-only repository metadata extraction tool. AST-based, no LLM in MVP.

## Stack

- Python 3.11+
- `radon` — cyclomatic complexity + LOC
- `gitpython` — git blame (author, date, commit count)
- `pydantic` v2 — schema / validation
- `typer` + `rich` — CLI
- `ruff` — lint/format
- `pytest` + `pytest-cov` — tests (target: 80%+, currently 95 tests / 94.6%)

## Commands

```bash
# Setup
pip install -e ".[dev]"

# Run all tests (coverage enforced via pyproject addopts, fails under 80%)
pytest

# Run a single test file / test
pytest tests/test_parser.py
pytest tests/test_parser.py::test_parses_function_params -v

# Lint / format
ruff check src/
ruff format src/ tests/

# Run the CLI locally
code-metadata extract /path/to/repo --format json
code-metadata extract /path/to/repo --format csv --output out.csv
code-metadata extract /path/to/repo --no-git   # skip git blame, works on non-git dirs
```

## Architecture

The extractor is a linear enrichment pipeline, orchestrated by `extract_repo()` in `cli.py`. Each `.py` file under the target repo flows through the same sequence of mutation passes before being validated into the final Pydantic schema:

```
parser.parse_file(path)            → raw dict: functions/classes/imports/total_lines (per file, AST-only)
  → analyzer.enrich_file(parsed, source, test_index)  → adds complexity (radon), LOC, has_test/test_files
  → docstring_scorer.enrich_docstrings(parsed)        → adds docstring style + quality_score (0-1)
  → git_utils.enrich_git(parsed)                      → adds git_metadata (or None if --no-git / non-git repo)
  → cli._to_file_metadata(parsed)                     → validates into schema.FileMetadata (Pydantic)
```

Key points for working in this codebase:

- **Dicts until the end.** `parser.py`, `analyzer.py`, `docstring_scorer.py`, and `git_utils.py` all mutate plain `dict` structures in place (functions/classes as nested dicts with a `methods` list). Pydantic validation (`schema.py` models) only happens once, at the very end, in `cli._to_file_metadata` / `_to_class_metadata` / `_to_function_metadata`. Don't introduce schema objects earlier in the pipeline — the enrichment stages are intentionally schema-agnostic.
- **`build_test_index(root)` runs once per repo** (in `analyzer.py`), before the per-file loop, and is passed into every `enrich_file` call — it scans all `test_*.py`/`*_test.py` files up front so each function lookup for `has_test` is a dict lookup, not a re-scan.
- **Git blame is cached per file**, not per function/method — `git_utils.py` calls `git blame` once per file and slices results per line range, keeping cost linear in files rather than functions.
- **Errors are contained per-file.** A file that fails Pydantic validation in `extract_repo` is caught and skipped with a console warning (`cli.py`), not aborted — the run always produces output for whatever parsed successfully. A file with a Python `SyntaxError` is not skipped outright; `parser.parse_file` returns it with empty functions/classes and a `parse_error` field instead of raising.
- **Docstring scoring is heuristic, not semantic** (`docstring_scorer.py`): style detection (numpy/google/sphinx/unstructured/none) plus presence of args/returns/example sections, no LLM. This is called out in design decisions below because it's the most likely thing a future contributor will assume is "just a stub" — it's the intended MVP behavior.
- **Test coverage is inferred, not measured**: `analyzer.py` looks for a `test_<funcname>` symbol in `test_*.py`/`*_test.py` files, it does not run the target repo's test suite or read coverage data.
- **Exporters (`exporters.py`) consume the fully-validated `RepositoryMetadata`** — CSV flattening logic (methods promoted to top-level rows with `parent_class` set) lives only there, not upstream.

## Design decisions

- Git integration is optional: non-git repos produce `git_metadata: null`, no crash.
- Blame is cached per file (one call per file, not per function line).
- Docstring style detection: numpy / google / sphinx / unstructured / none — heuristic, no LLM.
- Test coverage is *inferred*: presence of `test_<funcname>` in `test_*.py` or `*_test.py`.
- No domain-agnostic abstraction in MVP — code domain only, generalize after shipping.
