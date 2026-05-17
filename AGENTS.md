# AGENTS.md

## What This CLI Does

`nbctx` is a small CLI for inspecting, searching, validating, and safely editing Jupyter notebooks.

It reads and writes `.ipynb` files with `nbformat`, does not execute notebook code, and returns JSON by default. Most JSON responses also include a `markdown` field for readable summaries.

## Core Pattern

- Use stable cell IDs instead of notebook indexes.
- Stable IDs live in cell metadata at `metadata.nbctx.id`.
- Run `nbctx index NOTEBOOK.ipynb` to add missing IDs and create `.notebook-cli/` context files.
- Treat the notebook as the source of truth.

## Main Commands

```bash
nbctx inspect NOTEBOOK.ipynb
nbctx cells NOTEBOOK.ipynb
nbctx show NOTEBOOK.ipynb --cell CELL_ID
nbctx search NOTEBOOK.ipynb QUERY
nbctx append NOTEBOOK.ipynb --type code --source file.py
nbctx insert NOTEBOOK.ipynb --after CELL_ID --type markdown --source notes.md
nbctx replace NOTEBOOK.ipynb --cell CELL_ID --source updated.py
nbctx validate NOTEBOOK.ipynb
nbctx index NOTEBOOK.ipynb
```

Use `--format markdown` when a human-readable view is better than JSON.

## Safe Editing Workflow

1. Run `nbctx inspect NOTEBOOK.ipynb`.
2. Run `nbctx cells NOTEBOOK.ipynb`.
3. Run `nbctx show NOTEBOOK.ipynb --cell CELL_ID` before replacing a cell.
4. Edit with `append`, `insert`, or `replace`.
5. Run `nbctx validate NOTEBOOK.ipynb`.

## Development Notes

- CLI routing lives in `src/nbctx/cli.py`.
- Notebook behavior lives in `src/nbctx/notebooks.py`.
- Expected user-facing errors use `NbctxError`.
- Tests are under `tests/` and focus on CLI output, stable IDs, validation, and preserving notebook contents.
- Use `uv run pytest -q` for verification.

## GitHub Development Flow

- Start unclear bugs, features, or behavior changes with an issue.
- Small docs or test fixes can go straight to a PR.
- Use one focused branch per change.
- Use semantic branch names: `<type>-<short_description>`.
- Good branch examples: `feat-add-cell-delete`, `fix-empty-search-query`, `docs-update-agent-flow`.
- Keep PRs small and easy to review.
- Use semantic commits.
- Commit types should describe intent, such as `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, or `release`.
- Each commit must include a clear description of what it does.
- Commits should be feature-level or adjustment-level, not file-level.
- Good commit examples: `fix: reject empty search queries`, `docs: describe GitHub development flow`.
- Avoid commits like `update notebooks.py` or `change tests`.
- PR descriptions should be medium-length: explain the feature or fix applied, why it matters, and how it was tested.
- PR descriptions should mention user-facing behavior changes and any notebook safety implications.
- Use the GitHub CLI (`gh`) to create PRs, add descriptions, link issues, and manage PR metadata.
- Mention notebook safety implications when changing edit, validation, or ID behavior.
- Update `README.md`, `CHANGELOG.md`, or `docs/releasing.md` when behavior or release process changes.

## Known Things To Watch

- Empty search queries should be avoided.
- `replace` changes source only; existing outputs and execution counts are preserved.
- Markdown output is convenient context, not a strict notebook renderer.
