"""Complexity, LOC, dependencies, and test-coverage inference."""
from __future__ import annotations

import ast
from pathlib import Path

from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze


# ── complexity via radon ──────────────────────────────────────────────────────

def _radon_complexity_map(source: str) -> dict[str, int]:
    """Return {function_name: cyclomatic_complexity} for all functions/methods."""
    try:
        results = cc_visit(source)
    except Exception:
        return {}
    return {r.name: r.complexity for r in results}


def file_raw_metrics(source: str) -> dict:
    """Return radon raw metrics dict (loc, sloc, comments, blank, multi)."""
    try:
        m = raw_analyze(source)
        return {"loc": m.loc, "sloc": m.sloc, "comments": m.comments, "blank": m.blank}
    except Exception:
        return {"loc": 0, "sloc": 0, "comments": 0, "blank": 0}


# ── dependency extraction ─────────────────────────────────────────────────────

def _call_names(node: ast.AST) -> list[str]:
    """Names of all calls made inside a function/method node."""
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                # e.g. os.path.join → "os.path.join"
                parts: list[str] = [func.attr]
                obj = func.value
                while isinstance(obj, ast.Attribute):
                    parts.append(obj.attr)
                    obj = obj.value
                if isinstance(obj, ast.Name):
                    parts.append(obj.id)
                names.append(".".join(reversed(parts)))
    return list(dict.fromkeys(names))  # deduplicate, preserve order


def extract_dependencies(func_node: ast.AST, imported_names: list[str]) -> list[str]:
    """Calls made inside func_node that match something imported at module level."""
    calls = _call_names(func_node)
    imported_set = set(imported_names)
    # keep call if its root matches an import name
    deps: list[str] = []
    for call in calls:
        root = call.split(".")[0]
        if root in imported_set:
            deps.append(call)
    return deps


# ── test-coverage inference ───────────────────────────────────────────────────

def _test_function_names(test_file: Path) -> set[str]:
    """Parse a test file and return all function names defined in it."""
    try:
        source = test_file.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except Exception:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def build_test_index(repo_path: str | Path) -> dict[str, list[str]]:
    """Scan repo for test files; return {func_name: [test_file, ...]}."""
    root = Path(repo_path)
    test_files = list(root.rglob("test_*.py")) + list(root.rglob("*_test.py"))
    index: dict[str, list[str]] = {}
    for tf in test_files:
        for name in _test_function_names(tf):
            # strip leading "test_" to get the target function name
            target = name[5:] if name.startswith("test_") else name
            index.setdefault(target, []).append(str(tf))
    return index


# ── main enrichment entry point ───────────────────────────────────────────────

def enrich_file(parsed: dict, source: str, test_index: dict[str, list[str]]) -> dict:
    """Attach complexity/LOC/deps/test fields to a parsed-file dict (mutates in place).

    Args:
        parsed: dict from parser.parse_file
        source: raw source text of the file
        test_index: from build_test_index, covers the whole repo
    """
    complexity_map = _radon_complexity_map(source)
    raw = file_raw_metrics(source)
    parsed["sloc"] = raw["sloc"]

    # re-parse for AST nodes so we can walk into function bodies
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None

    func_nodes: dict[str, ast.AST] = {}
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_nodes[node.name] = node

    imports = parsed.get("imports", [])

    def _enrich_fn(fn: dict) -> dict:
        name = fn["name"]
        ast_node = func_nodes.get(name)
        fn["complexity"] = {
            "cyclomatic_complexity": complexity_map.get(name, 1),
            "lines_of_code": fn.get("_loc", 0),
            "docstring_lines": fn.get("_docstring_lines", 0),
            "dependencies": extract_dependencies(ast_node, imports) if ast_node else [],
            "has_test": name in test_index,
            "test_files": test_index.get(name, []),
        }
        fn.pop("_loc", None)
        fn.pop("_docstring_lines", None)
        return fn

    parsed["functions"] = [_enrich_fn(f) for f in parsed.get("functions", [])]
    for cls in parsed.get("classes", []):
        cls["methods"] = [_enrich_fn(m) for m in cls.get("methods", [])]

    return parsed
