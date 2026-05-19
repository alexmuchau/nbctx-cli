# nbctx

[![skills.sh](https://skills.sh/b/alexmuchau/nbctx-cli)](https://skills.sh/alexmuchau/nbctx-cli)

`nbctx` is a command line tool for inspecting, searching, and safely editing Jupyter notebooks.

It is built for developers and coding agents that need to work with `.ipynb` files without writing one-off notebook parsing scripts. `nbctx` reads and writes notebooks with `nbformat`, gives cells stable IDs, and returns structured JSON by default.

V1 focuses on notebook structure and cell manipulation. It does not execute notebook code.

## Install

With `pip`:

```bash
pip install nbctx
```

With `pipx`:

```bash
pipx install nbctx
```

With `uv`:

```bash
uv tool install nbctx
```

From GitHub:

```bash
pip install git+https://github.com/alexmuchau/nbctx-cli.git
```

## Agent Skill

Install the reusable Agent skill from this repository with:

```bash
npx skills add alexmuchau/nbctx-cli --skill nbctx-notebook-cli
```

The skill helps agents inspect `.ipynb` files, search notebook sources, work with stable cell IDs, validate notebook structure, and make safe cell edits without executing notebook code.

## Quick Start

Inspect a notebook:

```bash
nbctx inspect notebook.ipynb
```

List cells:

```bash
nbctx cells notebook.ipynb
```

Search all cell sources:

```bash
nbctx search notebook.ipynb "train_test_split"
```

Show one cell by stable ID:

```bash
nbctx show notebook.ipynb --cell nbctx-a1b2c3d4e5f6
```

Validate notebook safety:

```bash
nbctx validate notebook.ipynb
```

Repair known safe notebook inconsistencies:

```bash
nbctx repair notebook.ipynb
```

## Commands

### `inspect`

Print notebook metadata, cell counts, kernel info, language info, and a compact structure preview.

```bash
nbctx inspect notebook.ipynb
```

### `cells`

List cells with stable ID, index, type, tags, execution count, source length, and first lines.

```bash
nbctx cells notebook.ipynb
```

Use markdown output for a readable overview:

```bash
nbctx cells notebook.ipynb --format markdown
```

### `show`

Show the full source for one cell.

```bash
nbctx show notebook.ipynb --cell nbctx-a1b2c3d4e5f6
```

### `search`

Search code and markdown cells. Results include matching cell IDs, indexes, types, and snippets.

```bash
nbctx search notebook.ipynb "accuracy"
```

### `append`

Append a new code or markdown cell from a file:

```bash
nbctx append notebook.ipynb --type code --source analysis.py
```

Append from stdin:

```bash
printf 'print("hello")\n' | nbctx append notebook.ipynb --type code --source -
```

### `insert`

Insert a new cell after another cell by stable ID.

```bash
nbctx insert notebook.ipynb --after nbctx-a1b2c3d4e5f6 --type markdown --source notes.md
```

### `replace`

Replace one cell's source by stable ID.

```bash
nbctx replace notebook.ipynb --cell nbctx-a1b2c3d4e5f6 --source updated_cell.py
```

### `validate`

Check that the notebook is readable, has valid cell structure, and does not contain duplicate stable IDs.

```bash
nbctx validate notebook.ipynb
```

Schema/structure errors are reported separately from malformed JSON. When `nbctx` recognizes a safe repair, validation output includes guidance to run `nbctx repair`.

### `repair`

Repair known safe notebook inconsistencies without executing notebook code.

```bash
nbctx repair notebook.ipynb
```

Preview repairs without writing:

```bash
nbctx repair notebook.ipynb --dry-run
```

The first repair rule fixes code-cell `stream` outputs that are missing a `name` field by setting `name` to `"stdout"`. Existing output text, metadata, execution counts, cell ordering, and stable nbctx IDs are preserved.

### `index`

Add stable nbctx IDs to cells that are missing them and generate lightweight context files under `.notebook-cli/`.

```bash
nbctx index notebook.ipynb
```

Generated files:

- `.notebook-cli/<notebook-name>/cell-map.json`
- `.notebook-cli/<notebook-name>/summary.md`
- `.notebook-cli/<notebook-name>/notes.md`

The notebook remains the source of truth.

## Output Formats

Default output is JSON:

```bash
nbctx search notebook.ipynb "loss"
```

Use markdown when you want readable context for humans:

```bash
nbctx inspect notebook.ipynb --format markdown
```

Many JSON responses include a `markdown` field so tools can consume structured data and still display a readable summary.

## Stable Cell IDs

Notebook cell indexes are fragile because they change when cells are inserted or deleted. `nbctx` uses stable IDs stored in cell metadata:

```json
{
  "metadata": {
    "nbctx": {
      "id": "nbctx-a1b2c3d4e5f6"
    }
  }
}
```

Jupyter `cell.id` values are not the same as stable nbctx IDs. If `inspect`, `cells`, or `validate` shows missing stable nbctx IDs, run:

```bash
nbctx index notebook.ipynb
nbctx validate notebook.ipynb
```

## Safe Editing Workflow

For manual work or agent workflows:

1. Run `nbctx inspect notebook.ipynb`.
2. Run `nbctx cells notebook.ipynb`.
3. Use `nbctx show` before replacing a cell.
4. Edit with `append`, `insert`, or `replace`.
5. Run `nbctx validate notebook.ipynb`.

This keeps edits targeted and avoids relying on fragile cell indexes.

Edit commands (`append`, `insert`, and `replace`) and `index` automatically apply known safe repairs before writing. If a notebook has schema issues that `nbctx` cannot safely repair, the command fails with a notebook schema/structure error instead of treating the file as malformed JSON.
