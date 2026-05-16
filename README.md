# nbctx

`nbctx` is an agent-friendly command line tool for inspecting, summarizing, searching, and safely editing local Jupyter notebooks.

V1 focuses on notebook structure and cell manipulation. It does not execute notebook code.

## Install for development

```bash
uv sync
```

## Usage

```bash
uv run nbctx inspect NOTEBOOK.ipynb
uv run nbctx cells NOTEBOOK.ipynb --format markdown
uv run nbctx show NOTEBOOK.ipynb --cell CELL_ID
uv run nbctx search NOTEBOOK.ipynb QUERY
uv run nbctx append NOTEBOOK.ipynb --type code --source -
uv run nbctx replace NOTEBOOK.ipynb --cell CELL_ID --source new_source.py
uv run nbctx insert NOTEBOOK.ipynb --after CELL_ID --type markdown --source notes.md
uv run nbctx validate NOTEBOOK.ipynb
uv run nbctx index NOTEBOOK.ipynb
```

Default output is JSON. Commands with readable summaries also support `--format markdown`.
