"""AST walker — extracts functions, classes, imports from a Python source file."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional


def _annotation_to_str(node: Optional[ast.expr]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _decorator_names(decorator_list: list[ast.expr]) -> list[str]:
    return [_annotation_to_str(d) or "" for d in decorator_list]


def _extract_params(args: ast.arguments) -> list[dict]:
    params = []
    all_args = args.posonlyargs + args.args + args.kwonlyargs
    if args.vararg:
        all_args.append(args.vararg)
    if args.kwarg:
        all_args.append(args.kwarg)
    for arg in all_args:
        params.append({
            "name": arg.arg,
            "type_hint": _annotation_to_str(arg.annotation),
        })
    return params


def _count_lines(node: ast.AST) -> int:
    """Lines spanned by a function/class body (end_lineno - lineno + 1)."""
    end = getattr(node, "end_lineno", None)
    start = getattr(node, "lineno", None)
    if end is not None and start is not None:
        return end - start + 1
    return 0


def _extract_imports(tree: ast.Module) -> list[str]:
    """Top-level import names from the module."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                names.append(alias.asname or f"{module}.{alias.name}")
    return names


def _parse_function(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    file_path: str,
    parent_class: Optional[str] = None,
    is_method: bool = False,
) -> dict:
    docstring = ast.get_docstring(node)
    docstring_lines = 0
    if docstring:
        docstring_lines = docstring.count("\n") + 1
    return {
        "name": node.name,
        "file_path": file_path,
        "line_number": node.lineno,
        "end_line_number": getattr(node, "end_lineno", node.lineno),
        "params": _extract_params(node.args),
        "return_type": _annotation_to_str(node.returns),
        "docstring": docstring,
        "is_method": is_method,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "decorators": _decorator_names(node.decorator_list),
        "parent_class": parent_class,
        # complexity fields filled later by analyzer
        "_loc": _count_lines(node),
        "_docstring_lines": docstring_lines,
    }


def _parse_class(node: ast.ClassDef, file_path: str) -> dict:
    methods = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_parse_function(item, file_path, parent_class=node.name, is_method=True))
    return {
        "name": node.name,
        "file_path": file_path,
        "line_number": node.lineno,
        "end_line_number": getattr(node, "end_lineno", node.lineno),
        "docstring": ast.get_docstring(node),
        "decorators": _decorator_names(node.decorator_list),
        "methods": methods,
        "bases": [_annotation_to_str(b) or "" for b in node.bases],
    }


def parse_file(source_path: str | Path) -> dict:
    """Parse one Python file; return raw dicts (schema applied later).

    Returns:
        {
          "file_path": str,
          "functions": [...],   # top-level only
          "classes": [...],
          "imports": [...],
          "total_lines": int,
        }
    """
    path = Path(source_path)
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {
            "file_path": str(path),
            "functions": [],
            "classes": [],
            "imports": [],
            "total_lines": source.count("\n") + 1,
            "parse_error": str(exc),
        }

    functions: list[dict] = []
    classes: list[dict] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_parse_function(node, str(path)))
        elif isinstance(node, ast.ClassDef):
            classes.append(_parse_class(node, str(path)))

    return {
        "file_path": str(path),
        "functions": functions,
        "classes": classes,
        "imports": _extract_imports(tree),
        "total_lines": source.count("\n") + 1,
    }
