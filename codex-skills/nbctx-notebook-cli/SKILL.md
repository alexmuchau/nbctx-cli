---
name: nbctx-notebook-cli
description: Use nbctx to inspect, summarize, search, and safely edit Jupyter notebooks without writing custom notebook-parsing scripts.
---

# nbctx Notebook CLI

Use `nbctx` when working with local `.ipynb` files. Prefer it over ad hoc Python scripts for notebook inspection and cell edits.

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
