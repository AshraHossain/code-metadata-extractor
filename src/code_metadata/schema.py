from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ParamMetadata(BaseModel):
    name: str
    type_hint: Optional[str] = None


class DocstringQuality(BaseModel):
    presence: bool
    length: int
    has_args_section: bool
    has_return_section: bool
    has_example: bool
    style: Literal["numpy", "google", "sphinx", "unstructured", "none"]
    quality_score: float = Field(ge=0.0, le=1.0)


class GitMetadata(BaseModel):
    last_modified: datetime
    author: str
    author_email: str
    commit_count: int


class ComplexityMetrics(BaseModel):
    cyclomatic_complexity: int
    lines_of_code: int
    docstring_lines: int
    dependencies: list[str]
    has_test: bool
    test_files: list[str]


class FunctionMetadata(BaseModel):
    name: str
    file_path: str
    line_number: int
    end_line_number: int
    params: list[ParamMetadata]
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    is_method: bool
    is_async: bool
    decorators: list[str]
    parent_class: Optional[str] = None
    complexity: ComplexityMetrics
    docstring_quality: DocstringQuality
    git_metadata: Optional[GitMetadata] = None
    type_annotation_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    callees: list[str] = []
    callers: list[str] = []
    summary: Optional[str] = None


class ClassMetadata(BaseModel):
    name: str
    file_path: str
    line_number: int
    end_line_number: int
    docstring: Optional[str] = None
    decorators: list[str]
    methods: list[FunctionMetadata]
    bases: list[str]
    git_metadata: Optional[GitMetadata] = None


class FileMetadata(BaseModel):
    file_path: str
    functions: list[FunctionMetadata]
    classes: list[ClassMetadata]
    total_lines: int
    import_count: int


class RepositoryMetadata(BaseModel):
    repository_path: str
    analyzed_at: datetime
    language: str = "python"
    total_functions: int
    total_classes: int
    total_files: int
    files: list[FileMetadata]
