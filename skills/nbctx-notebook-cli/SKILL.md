---
name: nbctx-notebook-cli
description: Use nbctx whenever the user asks to inspect, summarize, search, validate, index, or safely edit local `.ipynb` notebooks. This skill is especially important for notebook work that needs stable `metadata.nbctx.id` cell references, missing-ID remediation, append/insert/replace operations, or JSON/markdown notebook summaries without executing notebook code.
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
2. If `inspect`, `cells`, or `validate` reports missing stable nbctx IDs, run `nbctx index NOTEBOOK.ipynb`, then run `nbctx validate NOTEBOOK.ipynb`.
3. Refer to cells by stable nbctx ID, not by fragile notebook index.
4. Run `nbctx show NOTEBOOK.ipynb --cell CELL_ID` before replacing a cell.
5. Use `nbctx append`, `nbctx insert`, or `nbctx replace` for notebook edits.
6. Run `nbctx validate NOTEBOOK.ipynb` after edits.

## Stable IDs

Stable nbctx IDs live in `metadata.nbctx.id`. Jupyter `cell.id` values are not the same thing and do not mean the notebook is ready for stable nbctx references.

Run `nbctx index NOTEBOOK.ipynb` when a notebook is missing stable nbctx IDs. This persists missing `metadata.nbctx.id` values and refreshes the optional `.notebook-cli/` context files. The notebook remains the source of truth.

## Output

- Prefer `--format json` for automation.
- Prefer `--format markdown` when summarizing notebook state for humans.
- JSON output may include a `markdown` field with the readable version.

## Commands

Use these commands as a safe progression from read-only inspection to targeted edits.

### `inspect`

Use `inspect` first when you need notebook-level context: cell count, cell order, cell types, stable nbctx IDs, and structural warnings.

```bash
nbctx inspect NOTEBOOK.ipynb
nbctx inspect NOTEBOOK.ipynb --format markdown
```

If the output shows missing stable nbctx IDs, normalize the notebook with `index` before relying on cell references.

### `cells`

Use `cells` to list cells with stable IDs and previews. This is the normal way to choose the target ID for `show`, `insert`, or `replace`.

```bash
nbctx cells NOTEBOOK.ipynb
nbctx cells NOTEBOOK.ipynb --format markdown
```

Do not use notebook indexes as edit targets. They shift when cells are inserted or deleted.

### `show`

Use `show` before replacing a cell. It returns the full source for one stable nbctx ID, which helps avoid overwriting the wrong cell.

```bash
nbctx show NOTEBOOK.ipynb --cell CELL_ID
nbctx show NOTEBOOK.ipynb --cell CELL_ID --format markdown
```

### `search`

Use `search` to find code or markdown cells by source text.

```bash
nbctx search NOTEBOOK.ipynb "QUERY"
nbctx search NOTEBOOK.ipynb "QUERY" --format markdown
```

Use a non-empty, specific query. After search finds candidates, run `show` on the chosen cell before editing.

### `append`

Use `append` to add a new code or markdown cell at the end of the notebook. The new cell receives a stable nbctx ID.

```bash
nbctx append NOTEBOOK.ipynb --type code --source new_cell.py
nbctx append NOTEBOOK.ipynb --type markdown --source notes.md
printf 'print("hello")\n' | nbctx append NOTEBOOK.ipynb --type code --source -
```

Use `--source -` for stdin when the source is generated inline. Use a file path when the source already exists in the workspace.

### `insert`

Use `insert` to add a new cell after a known stable nbctx ID. This keeps placement intentional even if notebook indexes change.

```bash
nbctx insert NOTEBOOK.ipynb --after CELL_ID --type markdown --source notes.md
nbctx insert NOTEBOOK.ipynb --after CELL_ID --type code --source new_cell.py
```

Run `cells` or `show` first if there is any doubt about the target cell.

### `replace`

Use `replace` to change only one cell's source by stable nbctx ID.

```bash
nbctx replace NOTEBOOK.ipynb --cell CELL_ID --source updated_cell.py
printf 'x = 1\n' | nbctx replace NOTEBOOK.ipynb --cell CELL_ID --source -
```

`replace` changes the source only. Existing outputs and execution counts are preserved, so call out that notebook safety implication when it matters.

### `validate`

Use `validate` after edits and whenever notebook structure or IDs are in question.

```bash
nbctx validate NOTEBOOK.ipynb
nbctx validate NOTEBOOK.ipynb --format markdown
```

Validation fails for duplicate stable nbctx IDs and warns about missing stable nbctx IDs. If IDs are missing, run `index`, then validate again.

### `index`

Use `index` to normalize a notebook that is missing stable nbctx IDs and to refresh optional context files.

```bash
nbctx index NOTEBOOK.ipynb
nbctx validate NOTEBOOK.ipynb
```

`index` persists missing `metadata.nbctx.id` values into the notebook and writes `.notebook-cli/` context files. It is not only a context-generation command.

`nbctx` reads and writes notebooks with `nbformat`, but it does not execute notebook code.
