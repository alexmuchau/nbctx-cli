# nbctx-notebook-cli

`nbctx-notebook-cli` is a Codex skill for inspecting, searching, validating, and safely editing Jupyter notebooks with `nbctx`.

It works in any repository that contains local `.ipynb` files. `nbctx` reads and writes notebooks with `nbformat` and does not execute notebook code.

## Install the Skill

```bash
npx skills add alexmuchau/nbctx-cli --skill nbctx-notebook-cli -a codex
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
3. Run `nbctx show NOTEBOOK.ipynb --cell CELL_ID` before replacing a cell.
4. Edit with `nbctx append`, `nbctx insert`, or `nbctx replace`.
5. Run `nbctx validate NOTEBOOK.ipynb`.

Use stable cell IDs from `metadata.nbctx.id` instead of notebook indexes, and run `nbctx index NOTEBOOK.ipynb` when you need to add missing IDs or generate `.notebook-cli/` context files.
