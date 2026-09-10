# code-metadata-extractor

Extract rich metadata from Python repositories — no LLM, no API keys, fully deterministic.

Walks every `.py` file via AST and produces structured data on functions, methods, and classes: complexity, docstring quality, git history, and inferred test coverage.

## Features

| Metadata | Source |
|---|---|
| Cyclomatic complexity | `radon` |
| Lines of code | `radon` |
| Docstring quality score (0–1) | Heuristic: style detection + section presence |
| Docstring style | numpy / google / sphinx / unstructured / none |
| Git blame (author, date, commit count) | `gitpython` — cached per file |
| Test coverage (inferred) | Detect `test_<funcname>` in `test_*.py` / `*_test.py` |
| Type hints, decorators, async flag | `ast` |
| Import-level dependencies per function | `ast` call-site analysis |

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Usage

```bash
# JSON to stdout
code-metadata extract /path/to/repo

# CSV to file
code-metadata extract /path/to/repo --format csv --output metadata.csv

# Skip git blame (faster, works on non-git directories)
code-metadata extract /path/to/repo --no-git
```

## Output shape (JSON)

```json
{
  "repository_path": "/path/to/repo",
  "analyzed_at": "2026-09-10T12:00:00Z",
  "total_files": 12,
  "total_functions": 84,
  "total_classes": 9,
  "files": [
    {
      "file_path": "/path/to/repo/module.py",
      "total_lines": 120,
      "import_count": 5,
      "functions": [
        {
          "name": "parse_record",
          "line_number": 14,
          "end_line_number": 38,
          "is_async": false,
          "is_method": false,
          "return_type": "dict",
          "params": [{"name": "raw", "type_hint": "str"}],
          "complexity": {
            "cyclomatic_complexity": 4,
            "lines_of_code": 25,
            "has_test": true,
            "test_files": ["tests/test_module.py"],
            "dependencies": ["json.loads", "re.match"]
          },
          "docstring_quality": {
            "presence": true,
            "style": "google",
            "has_args_section": true,
            "has_return_section": true,
            "has_example": false,
            "quality_score": 0.7
          },
          "git_metadata": {
            "author": "Alice",
            "author_email": "alice@example.com",
            "last_modified": "2026-08-01T09:30:00Z",
            "commit_count": 7
          }
        }
      ],
      "classes": []
    }
  ]
}
```

## CSV columns

`file_path`, `name`, `line_number`, `end_line_number`, `is_method`, `is_async`, `parent_class`, `decorators`, `return_type`, `cyclomatic_complexity`, `lines_of_code`, `docstring_lines`, `has_test`, `has_docstring`, `docstring_score`, `docstring_style`, `git_author`, `git_last_modified`, `git_commit_count`

## Development

```bash
# Run tests with coverage
pytest

# Lint
ruff check src/

# Format
ruff format src/ tests/
```

95 tests, 94.6% coverage.

## Design notes

- **No LLM in MVP** — all extraction is deterministic and free. LLM-based semantic docstring scoring is a planned post-MVP addition.
- **Git is optional** — non-git directories produce `git_metadata: null`, no crash.
- **Blame is cached per file** — one `git blame` call per file, not per function line.
- **Test coverage is inferred** — presence of `test_<funcname>` in test files, not actual execution coverage.
- **Single domain first** — code only; generalise to other domains after shipping value.

## License

MIT
