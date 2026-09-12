# Graph Report - code-metadata-extractor  (2026-09-11)

## Corpus Check
- Corpus is ~8,566 words - fits in a single context window. You may not need a graph.

## Summary
- 284 nodes · 484 edges · 15 communities (10 shown, 2 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Analyzer & Test Coverage
- CLI & Orchestration
- Docstring Scoring
- Git Blame Integration
- AST Node Types
- Integration Tests
- Fixture Module
- Parser Tests
- LLM Summarizer
- Architecture Docs
- CI/CD Pipeline
- Package Root

## God Nodes (most connected - your core abstractions)
1. `score_docstring` - 26 edges
2. `enrich_file` - 18 edges
3. `extract_repo` - 18 edges
4. `parse_file` - 15 edges
5. `to_csv` - 14 edges
6. `FunctionMetadata` - 14 edges
7. `git_metadata_for_lines` - 13 edges
8. `build_test_index` - 12 edges
9. `RepositoryMetadata` - 12 edges
10. `to_json` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Inferred test coverage concept` --references--> `build_test_index`  [INFERRED]
  CLAUDE.md → src/code_metadata/analyzer.py
- `Git blame cached per file concept` --references--> `enrich_git`  [INFERRED]
  CLAUDE.md → src/code_metadata/git_utils.py
- `No LLM in MVP design decision` --references--> `summarize_function`  [INFERRED]
  CLAUDE.md → src/code_metadata/summarizer.py
- `test_extract_repo_returns_repository_metadata()` --uses--> `RepositoryMetadata`  [INFERRED]
  tests/test_integration.py → src/code_metadata/schema.py
- `Linear enrichment pipeline concept` --semantically_similar_to--> `README features and output shape`  [INFERRED] [semantically similar]
  CLAUDE.md → README.md

## Import Cycles
- None detected.

## Communities (15 total, 2 thin omitted)

### Community 0 - "Analyzer & Test Coverage"
Cohesion: 0.06
Nodes (37): Inferred test coverage concept, build_test_index, _call_names(), enrich_file, _enrich_fn(), extract_all_calls, extract_dependencies, file_raw_metrics (+29 more)

### Community 1 - "CLI & Orchestration"
Cohesion: 0.09
Nodes (44): BaseModel, command, _build_call_graph, extract (CLI command), extract_repo, Path, CLI entry point and repo-level orchestration., Extract metadata from a Python repository. (+36 more)

### Community 2 - "Docstring Scoring"
Cohesion: 0.11
Nodes (32): DocstringStyle, _detect_style, enrich_docstrings, _attach_fn(), _quality_score, Heuristic docstring quality scoring — no LLM, pure string matching., Attach docstring_quality to every function and class in a parsed-file dict., Return a DocstringQuality-shaped dict for one function/method/class. Args:… (+24 more)

### Community 3 - "Git Blame Integration"
Cohesion: 0.12
Nodes (26): Git blame cached per file concept, _blame_lines, _commit_count(), enrich_git, _attach(), _find_repo, get_repo, git_metadata_for_lines (+18 more)

### Community 4 - "AST Node Types"
Cohesion: 0.13
Nodes (23): arguments, AsyncFunctionDef, ClassDef, expr, FunctionDef, Module, _annotation_to_str(), _count_lines() (+15 more)

### Community 5 - "Integration Tests"
Cohesion: 0.08
Nodes (4): fixture, End-to-end integration tests — full pipeline on fixture directory., repo(), test_extract_repo_returns_repository_metadata()

### Community 6 - "Fixture Module"
Cohesion: 0.11
Nodes (16): async_function, ChildClass, complex_function, no_docstring, A sample module used as a test fixture for AST parsing tests., Add two numbers. Args: x: First number. y: Second number. Returns: Sum of x and…, Fetch something asynchronously. Args: url: Target URL. Returns: Response body…, A sample class for testing class-level metadata extraction. (+8 more)

### Community 7 - "Parser Tests"
Cohesion: 0.09
Nodes (3): parsed(), fixture, Tests for the AST parser.

### Community 8 - "LLM Summarizer"
Cohesion: 0.19
Nodes (14): No LLM in MVP design decision, patch, _client(), enrich_summaries, Optional LLM summarization via Anthropic API (claude-haiku-4-5-20251001)., Return a one-sentence summary of a function via Claude Haiku., Attach LLM-generated summary to each function/method in a parsed file dict., summarize_function (+6 more)

### Community 9 - "Architecture Docs"
Cohesion: 0.67
Nodes (3): Linear enrichment pipeline concept, README features and output shape, Serena project config (python LSP)

## Knowledge Gaps
- **9 isolated node(s):** `code-metadata`, `complex_function`, `CI test job (matrix: 3.11/3.12)`, `CI publish job (PyPI on tag)`, `No LLM in MVP design decision` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 130 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `extract_repo` connect `CLI & Orchestration` to `Analyzer & Test Coverage`, `Docstring Scoring`, `Git Blame Integration`, `AST Node Types`, `Integration Tests`, `LLM Summarizer`?**
  _High betweenness centrality (0.147) - this node is a cross-community bridge._
- **Why does `enrich_docstrings` connect `Docstring Scoring` to `Analyzer & Test Coverage`, `CLI & Orchestration`, `Git Blame Integration`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `enrich_file` (e.g. with `build_test_index` and `enrich_docstrings`) actually correct?**
  _`enrich_file` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `extract_repo` (e.g. with `FileMetadata` and `RepositoryMetadata`) actually correct?**
  _`extract_repo` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `code-metadata`, `complex_function`, `CI test job (matrix: 3.11/3.12)` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Analyzer & Test Coverage` be split into smaller, more focused modules?**
  _Cohesion score 0.06259426847662142 - nodes in this community are weakly interconnected._
- **Should `CLI & Orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.09061224489795919 - nodes in this community are weakly interconnected._