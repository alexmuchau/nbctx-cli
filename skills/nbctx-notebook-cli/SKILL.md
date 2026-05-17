---
name: nbctx-notebook-cli
description: Use nbctx when you need to inspect or search `.ipynb` files, work with stable Jupyter cell IDs, validate notebook structure, or make safe cell edits without executing notebook code.
---

# nbctx Notebook CLI

Use `nbctx` when working with local `.ipynb` files in any repository. Prefer it over ad hoc Python scripts for notebook inspection, search, validation, and cell edits.

## Prerequisites

Check whether `nbctx` is already installed:

```bash
command -v nbctx
```

If it is missing, install it with one of:

```bash
uv tool install nbctx
pipx install nbctx
pip install nbctx
```

## Workflow

1. Run `nbctx inspect NOTEBOOK.ipynb` and `nbctx cells NOTEBOOK.ipynb` before editing.
2. Refer to cells by stable nbctx ID, not by fragile notebook index.
3. Run `nbctx show NOTEBOOK.ipynb --cell CELL_ID` before replacing a cell.
4. Use `nbctx append`, `nbctx insert`, or `nbctx replace` for notebook edits.
5. Run `nbctx validate NOTEBOOK.ipynb` after edits.

## Output

- Prefer `--format json` for automation.
- Prefer `--format markdown` when summarizing notebook state for humans.
- JSON output may include a `markdown` field with the readable version.

## Commands

```bash
nbctx inspect NOTEBOOK.ipynb
nbctx cells NOTEBOOK.ipynb
nbctx show NOTEBOOK.ipynb --cell CELL_ID
nbctx search NOTEBOOK.ipynb QUERY
nbctx append NOTEBOOK.ipynb --type code --source -
nbctx replace NOTEBOOK.ipynb --cell CELL_ID --source new_source.py
nbctx insert NOTEBOOK.ipynb --after CELL_ID --type markdown --source notes.md
nbctx validate NOTEBOOK.ipynb
nbctx index NOTEBOOK.ipynb
```

Run `nbctx index NOTEBOOK.ipynb` only when a durable `.notebook-cli/` context folder is useful. The notebook remains the source of truth.

`nbctx` reads and writes notebooks with `nbformat`, but it does not execute notebook code.
