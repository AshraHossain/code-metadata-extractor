# code-metadata-extractor

Python-only repository metadata extraction tool. AST-based, no LLM in MVP.

## Stack

- Python 3.11+
- `radon` — cyclomatic complexity + LOC
- `gitpython` — git blame (author, date, commit count)
- `pydantic` v2 — schema / validation
- `typer` + `rich` — CLI
- `ruff` — lint/format
- `pytest` + `pytest-cov` — tests (target: 80%+)

## Layout

```
src/code_metadata/
  schema.py          # Pydantic models
  parser.py          # AST walker
  analyzer.py        # radon complexity + LOC
  git_utils.py       # git blame, cached per file
  docstring_scorer.py# heuristic docstring quality (0-1)
  exporters.py       # JSON + CSV output
  cli.py             # typer CLI entry point

tests/
  fixtures/
    sample_module.py        # fixture: functions, classes, async, decorators
    test_sample_module.py   # fixture: matching test file (coverage inference)
  test_parser.py
  test_analyzer.py
  test_docstring_scorer.py
  test_git_utils.py
  test_exporters.py
  test_integration.py
```

## CLI

```bash
code-metadata extract /path/to/repo --format json
code-metadata extract /path/to/repo --format csv --output out.csv
```

## Dev setup

```bash
pip install -e ".[dev]"
pytest
ruff check src/
```

## Design decisions

- Git integration is optional: non-git repos produce `git_metadata: null`, no crash.
- Blame is cached per file (one call per file, not per function line).
- Docstring style detection: numpy / google / sphinx / unstructured / none — heuristic, no LLM.
- Test coverage is *inferred*: presence of `test_<funcname>` in `test_*.py` or `*_test.py`.
- No domain-agnostic abstraction in MVP — code domain only, generalize after shipping.
