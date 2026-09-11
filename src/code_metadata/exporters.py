"""JSON and CSV export for RepositoryMetadata."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from code_metadata.schema import FunctionMetadata, RepositoryMetadata


def _fn_rows(repo: RepositoryMetadata) -> list[dict]:
    """Flatten every function/method to one CSV row each."""
    rows = []
    for file in repo.files:
        def _row(fn: FunctionMetadata) -> dict:
            git = fn.git_metadata
            cplx = fn.complexity
            dq = fn.docstring_quality
            return {
                "file_path": fn.file_path,
                "name": fn.name,
                "line_number": fn.line_number,
                "end_line_number": fn.end_line_number,
                "is_method": fn.is_method,
                "is_async": fn.is_async,
                "parent_class": fn.parent_class or "",
                "decorators": "|".join(fn.decorators),
                "return_type": fn.return_type or "",
                "type_annotation_coverage": fn.type_annotation_coverage,
                "cyclomatic_complexity": cplx.cyclomatic_complexity,
                "lines_of_code": cplx.lines_of_code,
                "docstring_lines": cplx.docstring_lines,
                "has_test": cplx.has_test,
                "has_docstring": dq.presence,
                "docstring_score": dq.quality_score,
                "docstring_style": dq.style,
                "callees": "|".join(fn.callees),
                "callers": "|".join(fn.callers),
                "summary": fn.summary or "",
                "git_author": git.author if git else "",
                "git_last_modified": git.last_modified.isoformat() if git else "",
                "git_commit_count": git.commit_count if git else "",
            }

        for fn in file.functions:
            rows.append(_row(fn))
        for cls in file.classes:
            for method in cls.methods:
                rows.append(_row(method))
    return rows


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Not serializable: {type(obj)}")


def to_json(repo: RepositoryMetadata, output: Optional[str | Path] = None) -> str:
    """Serialize repo metadata to JSON string; optionally write to file."""
    text = repo.model_dump_json(indent=2)
    if output:
        Path(output).write_text(text, encoding="utf-8")
    return text


def to_csv(repo: RepositoryMetadata, output: Optional[str | Path] = None) -> str:
    """Flatten functions/methods to CSV; optionally write to file."""
    rows = _fn_rows(repo)
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    text = buf.getvalue()
    if output:
        Path(output).write_text(text, encoding="utf-8")
    return text
