"""CLI entry point and repo-level orchestration."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from code_metadata.analyzer import build_test_index, enrich_file
from code_metadata.docstring_scorer import enrich_docstrings
from code_metadata.exporters import to_csv, to_json
from code_metadata.git_utils import enrich_git
from code_metadata.parser import parse_file
from code_metadata.schema import (
    ClassMetadata,
    FileMetadata,
    FunctionMetadata,
    RepositoryMetadata,
)

app = typer.Typer(help="Extract metadata from Python repositories.")
console = Console(stderr=True)


# ── orchestration (importable for tests) ─────────────────────────────────────

def _to_function_metadata(fn: dict) -> FunctionMetadata:
    return FunctionMetadata.model_validate(fn)


def _to_class_metadata(cls: dict) -> ClassMetadata:
    methods = [_to_function_metadata(m) for m in cls.get("methods", [])]
    return ClassMetadata.model_validate({**cls, "methods": methods})


def _to_file_metadata(parsed: dict) -> FileMetadata:
    functions = [_to_function_metadata(f) for f in parsed.get("functions", [])]
    classes = [_to_class_metadata(c) for c in parsed.get("classes", [])]
    return FileMetadata(
        file_path=parsed["file_path"],
        functions=functions,
        classes=classes,
        total_lines=parsed.get("total_lines", 0),
        import_count=len(parsed.get("imports", [])),
    )


def _build_call_graph(all_parsed: list[dict]) -> None:
    """Compute callers/callees across all files; mutates parsed dicts in place."""
    all_fn_names: set[str] = set()
    all_fns: list[dict] = []
    for parsed in all_parsed:
        for fn in parsed.get("functions", []):
            all_fn_names.add(fn["name"])
            all_fns.append(fn)
        for cls in parsed.get("classes", []):
            for m in cls.get("methods", []):
                all_fn_names.add(m["name"])
                all_fns.append(m)

    callers: dict[str, list[str]] = {n: [] for n in all_fn_names}
    for fn in all_fns:
        raw = fn.pop("_raw_callees", [])
        callees = [c for c in raw if c in all_fn_names and c != fn["name"]]
        fn["callees"] = list(dict.fromkeys(callees))
        for callee in fn["callees"]:
            callers[callee].append(fn["name"])

    for fn in all_fns:
        fn["callers"] = list(dict.fromkeys(callers.get(fn["name"], [])))


def extract_repo(
    repo_path: str | Path,
    include_git: bool = True,
    summarize: bool = False,
) -> RepositoryMetadata:
    """Parse every .py file in repo_path; return RepositoryMetadata."""
    root = Path(repo_path).resolve()
    py_files = sorted(root.rglob("*.py"))

    test_index = build_test_index(root)

    # Phase 1: enrich all files (dicts), keep sources for summarizer
    all_parsed: list[dict] = []
    sources: list[str] = []
    for py in py_files:
        source = py.read_text(encoding="utf-8", errors="replace")
        parsed = parse_file(py)
        enrich_file(parsed, source, test_index)
        enrich_docstrings(parsed)
        if include_git:
            enrich_git(parsed)
        else:
            for fn in parsed.get("functions", []):
                fn["git_metadata"] = None
            for cls in parsed.get("classes", []):
                cls["git_metadata"] = None
                for m in cls.get("methods", []):
                    m["git_metadata"] = None
        all_parsed.append(parsed)
        sources.append(source)

    # Phase 2: cross-file call graph
    _build_call_graph(all_parsed)

    # Phase 3: optional LLM summaries
    if summarize:
        from code_metadata.summarizer import enrich_summaries
        for parsed, source in zip(all_parsed, sources):
            enrich_summaries(parsed, source)

    # Phase 4: validate into Pydantic schema
    file_metas: list[FileMetadata] = []
    for parsed in all_parsed:
        try:
            file_metas.append(_to_file_metadata(parsed))
        except Exception as exc:
            console.print(f"[yellow]Skipping {Path(parsed['file_path']).name}: {exc}[/yellow]")

    total_functions = sum(
        len(f.functions) + sum(len(c.methods) for c in f.classes)
        for f in file_metas
    )
    total_classes = sum(len(f.classes) for f in file_metas)

    return RepositoryMetadata(
        repository_path=str(root),
        analyzed_at=datetime.now(tz=timezone.utc),
        total_functions=total_functions,
        total_classes=total_classes,
        total_files=len(file_metas),
        files=file_metas,
    )


# ── CLI commands ──────────────────────────────────────────────────────────────

@app.command()
def extract(
    repo_path: Path = typer.Argument(..., help="Path to the Python repository."),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json or csv."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path."),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git blame integration."),
    summarize: bool = typer.Option(False, "--summarize", "-s", help="Add LLM summaries (requires anthropic)."),
) -> None:
    """Extract metadata from a Python repository."""
    if not repo_path.exists():
        console.print(f"[red]Path not found: {repo_path}[/red]")
        raise typer.Exit(1)

    console.print(f"Scanning [bold]{repo_path}[/bold] ...")
    repo = extract_repo(repo_path, include_git=not no_git, summarize=summarize)
    console.print(
        f"Found [green]{repo.total_files}[/green] files, "
        f"[green]{repo.total_functions}[/green] functions, "
        f"[green]{repo.total_classes}[/green] classes."
    )

    fmt = format.lower()
    if fmt == "json":
        text = to_json(repo, output)
    elif fmt == "csv":
        text = to_csv(repo, output)
    else:
        console.print(f"[red]Unknown format '{format}'. Use json or csv.[/red]")
        raise typer.Exit(1)

    if output:
        console.print(f"Written to [bold]{output}[/bold]")
    else:
        typer.echo(text)


if __name__ == "__main__":
    app()
