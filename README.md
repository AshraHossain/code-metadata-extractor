# code-metadata-extractor

> Extract rich, structured metadata from Python repositories — deterministic, LLM-free, and production-ready.

`code-metadata` walks every `.py` file in a repository using Python's built-in `ast` module and a carefully designed enrichment pipeline. The result is a machine-readable snapshot of every function, method, and class: its complexity, docstring quality, type annotation coverage, call graph, git history, and inferred test coverage — with no API keys, no network calls, and no non-determinism.

[![CI](https://github.com/AshraHossain/code-metadata-extractor/actions/workflows/ci.yml/badge.svg)](https://github.com/AshraHossain/code-metadata-extractor/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Contents

- [Why this tool](#why-this-tool)
- [Features at a glance](#features-at-a-glance)
- [Installation](#installation)
- [Quick start](#quick-start)
- [CLI reference](#cli-reference)
- [Output schemas](#output-schemas)
  - [JSON](#json-schema)
  - [CSV](#csv-columns)
- [Pipeline architecture](#pipeline-architecture)
- [LLM summaries (optional)](#llm-summaries-optional)
- [Programmatic API](#programmatic-api)
- [Configuration and options](#configuration-and-options)
- [Development](#development)
- [Design decisions](#design-decisions)
- [License](#license)

---

## Why this tool

Static analysis tools tell you *what* is in a codebase. `code-metadata` tells you *how good* it is and *how it fits together* — in a structured format that downstream tools (dashboards, LLM pipelines, quality gates) can consume directly.

Common uses:

- **Automated code quality audits** — score every function on complexity, docstring completeness, type coverage, and test presence in a single pass.
- **LLM context enrichment** — feed the JSON output to a RAG pipeline or agent as grounded, structured context about a codebase.
- **Technical debt tracking** — diff two runs over time to see where quality is improving or regressing.
- **CI quality gates** — fail a build when cyclomatic complexity exceeds a threshold or docstring coverage drops below a target.
- **Onboarding documentation** — generate a CSV of every public function with its docstring and complexity for reviewers new to a codebase.

---

## Features at a glance

| Metadata field | Source | Notes |
|---|---|---|
| Cyclomatic complexity | `radon` | Per function/method |
| Lines of code (LOC) | `radon` | Excludes blank lines and comments |
| Docstring quality score (0–1) | Heuristic | Style detection + section presence |
| Docstring style | `ast` | `numpy` / `google` / `sphinx` / `unstructured` / `none` |
| Type annotation coverage (0–1) | `ast` | Ratio of annotated params + return to total |
| Call graph (callees / callers) | `ast` | Cross-file, resolved by function name |
| Git blame | `gitpython` | Author, email, last modified, commit count |
| Inferred test coverage | `ast` | Detects `test_<funcname>` in `test_*.py` / `*_test.py` |
| Async flag | `ast` | `is_async: true/false` |
| Decorators | `ast` | Full decorator list per function/method |
| Parameter list with type hints | `ast` | Name and type hint per param |
| LLM summary | Anthropic API | Optional; requires `pip install code-metadata[llm]` |

---

## Installation

### From PyPI

```bash
pip install code-metadata
```

### With LLM summary support

```bash
pip install "code-metadata[llm]"
```

The `llm` extra adds `anthropic>=0.34`. An `ANTHROPIC_API_KEY` environment variable is required at runtime when `--summarize` is passed.

### From source

```bash
git clone https://github.com/AshraHossain/code-metadata-extractor.git
cd code-metadata-extractor
pip install -e ".[dev]"
```

**Requires Python 3.11 or later.**

---

## Quick start

```bash
# Analyze a local repository, print JSON to stdout
code-metadata /path/to/your/repo

# Write CSV to a file (useful for spreadsheets and dashboards)
code-metadata /path/to/your/repo --format csv --output metadata.csv

# Analyze a non-git directory (skips blame, no crash)
code-metadata /path/to/your/repo --no-git

# Add LLM-generated one-line summaries to every function
ANTHROPIC_API_KEY=sk-... code-metadata /path/to/your/repo --summarize
```

---

## CLI reference

```
Usage: code-metadata [OPTIONS] REPO_PATH

  Extract metadata from a Python repository.

Arguments:
  REPO_PATH   Path to the Python repository to analyze.  [required]

Options:
  -f, --format TEXT   Output format: json or csv.  [default: json]
  -o, --output PATH   Write output to this file instead of stdout.
  --no-git            Skip git blame integration. Useful for non-git
                      directories or when git history is not needed.
  -s, --summarize     Attach an LLM-generated one-line summary to every
                      function and method. Requires the [llm] extra and
                      ANTHROPIC_API_KEY to be set.
  --help              Show this message and exit.
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Bad argument (path not found, unsupported format) |

Files that fail to parse are skipped with a warning on stderr; the run still exits `0` and produces output for all other files.

---

## Output schemas

### JSON schema

The top-level object is a `RepositoryMetadata` document.

```json
{
  "repository_path": "/absolute/path/to/repo",
  "analyzed_at": "2026-09-11T18:30:00Z",
  "language": "python",
  "total_files": 12,
  "total_functions": 84,
  "total_classes": 9,
  "files": [
    {
      "file_path": "/absolute/path/to/repo/module.py",
      "total_lines": 120,
      "import_count": 5,
      "functions": [
        {
          "name": "parse_record",
          "file_path": "/absolute/path/to/repo/module.py",
          "line_number": 14,
          "end_line_number": 38,
          "is_async": false,
          "is_method": false,
          "return_type": "dict",
          "decorators": [],
          "parent_class": null,
          "params": [
            { "name": "raw", "type_hint": "str" }
          ],
          "type_annotation_coverage": 1.0,
          "callees": ["json.loads", "re.match"],
          "callers": ["process_batch"],
          "summary": null,
          "complexity": {
            "cyclomatic_complexity": 4,
            "lines_of_code": 25,
            "docstring_lines": 6,
            "has_test": true,
            "test_files": ["tests/test_module.py"],
            "dependencies": ["json", "re"]
          },
          "docstring_quality": {
            "presence": true,
            "length": 85,
            "style": "google",
            "has_args_section": true,
            "has_return_section": true,
            "has_example": false,
            "quality_score": 0.75
          },
          "git_metadata": {
            "author": "Alice",
            "author_email": "alice@example.com",
            "last_modified": "2026-08-01T09:30:00Z",
            "commit_count": 7
          }
        }
      ],
      "classes": [
        {
          "name": "RecordParser",
          "file_path": "/absolute/path/to/repo/module.py",
          "line_number": 50,
          "end_line_number": 110,
          "docstring": "Parses raw records into structured dicts.",
          "decorators": ["dataclass"],
          "bases": ["BaseParser"],
          "git_metadata": { "...": "same shape as function git_metadata" },
          "methods": ["...same shape as functions, with is_method: true..."]
        }
      ]
    }
  ]
}
```

#### Field reference

**`RepositoryMetadata`**

| Field | Type | Description |
|---|---|---|
| `repository_path` | `string` | Absolute path passed to the CLI |
| `analyzed_at` | `datetime` (ISO 8601) | When the analysis ran |
| `language` | `string` | Always `"python"` in current version |
| `total_files` | `integer` | Count of `.py` files analyzed |
| `total_functions` | `integer` | All top-level functions across all files |
| `total_classes` | `integer` | All classes across all files |
| `files` | `FileMetadata[]` | Per-file results |

**`FileMetadata`**

| Field | Type | Description |
|---|---|---|
| `file_path` | `string` | Absolute path to the source file |
| `total_lines` | `integer` | Total line count including blank/comment lines |
| `import_count` | `integer` | Number of `import` and `from … import` statements |
| `functions` | `FunctionMetadata[]` | Top-level functions (not methods) |
| `classes` | `ClassMetadata[]` | Classes with their methods embedded |

**`FunctionMetadata` / method**

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Function or method name |
| `file_path` | `string` | Source file |
| `line_number` | `integer` | First line of the `def` statement |
| `end_line_number` | `integer` | Last line of the function body |
| `is_async` | `boolean` | `true` for `async def` |
| `is_method` | `boolean` | `true` when inside a class |
| `parent_class` | `string \| null` | Class name, or `null` for top-level functions |
| `decorators` | `string[]` | Decorator names (e.g. `["staticmethod", "cache"]`) |
| `params` | `ParamMetadata[]` | Parameter list with optional type hints |
| `return_type` | `string \| null` | Return annotation as written in source, or `null` |
| `docstring` | `string \| null` | Raw docstring text, or `null` |
| `type_annotation_coverage` | `float` [0, 1] | Fraction of params + return that are annotated |
| `callees` | `string[]` | Names of functions/methods called by this function |
| `callers` | `string[]` | Names of functions/methods that call this function |
| `summary` | `string \| null` | LLM-generated one-liner (only when `--summarize` is used) |
| `complexity` | `ComplexityMetrics` | See below |
| `docstring_quality` | `DocstringQuality` | See below |
| `git_metadata` | `GitMetadata \| null` | `null` when `--no-git` or directory is not a git repo |

**`ComplexityMetrics`**

| Field | Type | Description |
|---|---|---|
| `cyclomatic_complexity` | `integer` ≥ 1 | McCabe complexity via `radon` |
| `lines_of_code` | `integer` | SLOC (excludes blank and comment lines) |
| `docstring_lines` | `integer` | Line count of the docstring block |
| `dependencies` | `string[]` | Imported module names referenced in function body |
| `has_test` | `boolean` | `true` if a `test_<funcname>` symbol was found in a test file |
| `test_files` | `string[]` | Paths to test files where coverage was inferred |

**`DocstringQuality`**

| Field | Type | Description |
|---|---|---|
| `presence` | `boolean` | `true` if a docstring exists |
| `length` | `integer` | Character count of the docstring |
| `style` | `string` | `numpy` / `google` / `sphinx` / `unstructured` / `none` |
| `has_args_section` | `boolean` | Args / Parameters section detected |
| `has_return_section` | `boolean` | Returns / Return section detected |
| `has_example` | `boolean` | Examples / Example section detected |
| `quality_score` | `float` [0, 1] | Composite heuristic score |

**`GitMetadata`**

| Field | Type | Description |
|---|---|---|
| `author` | `string` | Most recent commit author name |
| `author_email` | `string` | Most recent commit author email |
| `last_modified` | `datetime` (ISO 8601) | Timestamp of most recent commit touching this function's line range |
| `commit_count` | `integer` | Number of commits that touched this function's line range |

---

### CSV columns

Each row represents one function or method. Class methods are promoted to top-level rows with `parent_class` set and `is_method: true`. Multi-value fields (`decorators`, `callees`, `callers`) are pipe-delimited (`|`).

| Column | Type | Description |
|---|---|---|
| `file_path` | string | Absolute path to source file |
| `name` | string | Function or method name |
| `line_number` | integer | Start line |
| `end_line_number` | integer | End line |
| `is_method` | bool | `True` for methods |
| `is_async` | bool | `True` for `async def` |
| `parent_class` | string | Class name or empty string |
| `decorators` | string | Pipe-delimited decorator names |
| `return_type` | string | Return annotation or empty string |
| `type_annotation_coverage` | float | 0.0–1.0 |
| `cyclomatic_complexity` | integer | McCabe complexity |
| `lines_of_code` | integer | SLOC |
| `docstring_lines` | integer | Lines in docstring |
| `has_test` | bool | Inferred test presence |
| `has_docstring` | bool | Docstring present |
| `docstring_score` | float | 0.0–1.0 quality score |
| `docstring_style` | string | Style label |
| `callees` | string | Pipe-delimited function names called |
| `callers` | string | Pipe-delimited function names that call this |
| `summary` | string | LLM summary or empty string |
| `git_author` | string | Author name or empty string |
| `git_last_modified` | string | ISO 8601 datetime or empty string |
| `git_commit_count` | integer or empty string | Commit count or empty |

---

## Pipeline architecture

Every `.py` file passes through a linear enrichment pipeline before Pydantic validation converts the result to the final schema:

```
parse_file(path)
  └─ AST parse: functions, classes, imports, line counts
  └─ Returns a plain dict — no schema objects yet

enrich_file(parsed, source, test_index)
  └─ radon: cyclomatic complexity, SLOC
  └─ AST: type annotation coverage, raw callees
  └─ Test index lookup: has_test, test_files
  └─ Stores raw callees for cross-file call graph resolution

enrich_docstrings(parsed)
  └─ Heuristic style detection (numpy/google/sphinx/unstructured/none)
  └─ Section detection: Args, Returns, Examples
  └─ Composite quality_score

enrich_git(parsed)       ← skipped with --no-git
  └─ git blame (one call per file, cached)
  └─ Slices blame output per function line range

_build_call_graph(all_parsed)   ← runs after all files are enriched
  └─ Resolves raw callees against all known function names
  └─ Populates callers list on each callee
  └─ Mutates dicts in place; cross-file resolution

enrich_summaries(parsed, source)   ← only with --summarize
  └─ Calls Anthropic Messages API per function
  └─ One-line natural-language description

_to_file_metadata(parsed)
  └─ Pydantic model_validate — first and only schema instantiation
  └─ Validation failure → file skipped, warning on stderr
```

**Key invariants:**

- All enrichment stages operate on plain `dict` objects. Pydantic models appear only at the final validation step.
- `build_test_index` runs once per repository, before the per-file loop. It pre-indexes all `test_*.py` / `*_test.py` files so per-function lookup is O(1).
- `git blame` runs once per file. Line ranges are sliced in memory — not one call per function.
- The call graph is a two-pass operation: raw callees are collected during per-file enrichment; cross-file caller/callee resolution happens in a single second pass over all parsed files.
- A `SyntaxError` in a source file does not abort the run. `parse_file` returns a partial result with an empty `functions` and `classes` list and a `parse_error` field.

---

## LLM summaries (optional)

When `--summarize` is passed, `code-metadata` calls the Anthropic API to generate a one-sentence natural-language description of each function and method.

```bash
# Install the LLM extra
pip install "code-metadata[llm]"

# Run with summaries
ANTHROPIC_API_KEY=sk-ant-... code-metadata /path/to/repo --summarize

# Output includes summary field on every function:
# "summary": "Validates a JWT token and returns the decoded payload."
```

**Cost note:** Each function is one API call. A repository with 200 functions will make approximately 200 API calls. Use `--no-git` to reduce wall-clock time, since git blame and LLM calls are both I/O-bound.

Without `--summarize`, `summary` is always `null` in the output — no API calls are made.

---

## Programmatic API

`code-metadata` is usable as a library. The primary entry point is `extract_repo`:

```python
from pathlib import Path
from code_metadata.cli import extract_repo
from code_metadata.schema import RepositoryMetadata

repo: RepositoryMetadata = extract_repo(
    root=Path("/path/to/repo"),
    include_git=True,   # set False to skip git blame
)

# Iterate functions across all files
for file in repo.files:
    for fn in file.functions:
        print(fn.name, fn.complexity.cyclomatic_complexity, fn.docstring_quality.quality_score)

# Export to JSON or CSV
from code_metadata.exporters import to_json, to_csv

json_str = to_json(repo)
csv_str  = to_csv(repo, output="metadata.csv")
```

### LLM summaries via API

```python
from code_metadata.summarizer import enrich_summaries

# parsed is a dict from parse_file / enrich_file / enrich_docstrings
parsed = enrich_summaries(parsed, source_code)
```

`enrich_summaries` mutates the dict in place and returns it. Requires `anthropic>=0.34` and `ANTHROPIC_API_KEY` in the environment.

---

## Configuration and options

There is no configuration file. All behavior is controlled by CLI flags. The tool is intentionally stateless — every run is independent.

| Option | Default | Effect |
|---|---|---|
| `--format json` | `json` | JSON output to stdout or file |
| `--format csv` | — | CSV output, one row per function/method |
| `--output PATH` | stdout | Write to file instead of stdout |
| `--no-git` | git enabled | Skip `git blame`; sets `git_metadata: null` for all functions |
| `--summarize` | disabled | Enable Anthropic API calls for LLM summaries |

---

## Development

### Setup

```bash
git clone https://github.com/AshraHossain/code-metadata-extractor.git
cd code-metadata-extractor
pip install -e ".[dev]"
```

### Running tests

```bash
# All tests with coverage report (fails if coverage < 80%)
pytest

# Single file
pytest tests/test_analyzer.py

# Single test
pytest tests/test_analyzer.py::test_cyclomatic_complexity_minimum -v

# Without coverage enforcement (useful for quick iteration)
pytest --no-cov
```

Current status: **95 tests · 94.6% coverage**.

### Lint and format

```bash
ruff check src/          # lint
ruff format src/ tests/  # format
```

### Project layout

```
src/code_metadata/
├── __init__.py
├── cli.py              # Entry point; orchestrates the enrichment pipeline
├── parser.py           # AST parsing → raw dict
├── analyzer.py         # Complexity, type coverage, call graph, test index
├── docstring_scorer.py # Docstring style detection and quality scoring
├── git_utils.py        # git blame integration
├── exporters.py        # JSON and CSV serializers
├── schema.py           # Pydantic v2 models
└── summarizer.py       # Optional Anthropic LLM integration

tests/
├── fixtures/           # Sample .py files used as test input
├── test_parser.py
├── test_analyzer.py
├── test_docstring_scorer.py
├── test_git_utils.py
├── test_exporters.py
├── test_summarizer.py  # Fully mocked — no API key required
└── test_integration.py # End-to-end CLI tests
```

### CI

GitHub Actions runs on Python 3.11 and 3.12 for every push and pull request to `master`. Publish to PyPI triggers automatically on `v*` tags via OIDC trusted publisher — no stored API tokens.

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Design decisions

**No LLM in the core pipeline.** All extraction is deterministic and free of API dependencies. The `--summarize` flag is an explicit opt-in and a separate code path. This keeps the tool usable in air-gapped environments, CI pipelines, and any context where network calls are restricted.

**Dicts until the final step.** The enrichment pipeline passes plain `dict` objects between stages. Pydantic validation runs exactly once, at the end of the pipeline in `_to_file_metadata`. This makes each stage independently testable with plain Python and avoids schema coupling between pipeline stages.

**Git blame is cached per file.** A single `git blame` call per file is issued; results are sliced by line range for each function. This keeps cost linear in files, not in functions.

**Test coverage is inferred, not measured.** The tool detects the presence of `test_<funcname>` in adjacent test files using AST symbol scanning. It does not execute the repository's test suite or read coverage XML. This means results are available without running tests and without `coverage.py`, but `has_test: true` does not guarantee the test actually covers the function.

**Docstring scoring is heuristic, not semantic.** Style detection (numpy / google / sphinx / unstructured / none) and section presence are determined by pattern matching on the docstring text. There is no LLM call involved. This is the intended MVP behavior — it is fast, free, and reproducible.

**Errors are contained per file.** A file that fails Pydantic validation is skipped with a console warning and does not abort the run. A file with a `SyntaxError` is returned by the parser with empty `functions` and `classes` rather than raising — downstream enrichment stages handle the empty lists gracefully.

---

## License

MIT. See [LICENSE](LICENSE).
