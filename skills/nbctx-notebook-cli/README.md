# nbctx-notebook-cli

`nbctx-notebook-cli` is a agent skill for inspecting, searching, extracting markdown sections, validating, and safely editing Jupyter notebooks with `nbctx`.

It works in any repository that contains local `.ipynb` files. `nbctx` reads and writes notebooks with `nbformat` and does not execute notebook code.

## Install the Skill

```bash
npx skills add alexmuchau/nbctx-cli --skill nbctx-notebook-cli
```

## Install `nbctx`

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

## Safe Notebook Editing Workflow

1. Run `nbctx inspect NOTEBOOK.ipynb`.
2. Run `nbctx cells NOTEBOOK.ipynb`.
3. Run `nbctx section NOTEBOOK.ipynb "## Heading"` when you need the cells under a markdown heading.
4. If `inspect`, `cells`, or `validate` reports missing stable nbctx IDs, run `nbctx index NOTEBOOK.ipynb`, then run `nbctx validate NOTEBOOK.ipynb`.
5. Run `nbctx show NOTEBOOK.ipynb --cell CELL_ID` before replacing a cell.
6. Edit with `nbctx append`, `nbctx insert`, or `nbctx replace`.
7. Run `nbctx validate NOTEBOOK.ipynb`.

Use stable cell IDs from `metadata.nbctx.id` instead of notebook indexes. Jupyter `cell.id` values are different from stable nbctx IDs.

Run `nbctx index NOTEBOOK.ipynb` when you need to add missing stable nbctx IDs or generate `.notebook-cli/` context files.

## Extract Markdown Sections

Use `section` when you need the cells that belong to a notebook heading:

```bash
nbctx section NOTEBOOK.ipynb "## Results"
nbctx section NOTEBOOK.ipynb "Results" --format markdown
```

`section` is read-only. It uses existing stable nbctx IDs, reports missing IDs as `null`, and does not execute code or change notebook metadata.
