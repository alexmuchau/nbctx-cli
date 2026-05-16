from __future__ import annotations

from pathlib import Path

import nbformat
import pytest

from nbctx.notebooks import set_stable_id


@pytest.fixture
def empty_notebook(tmp_path: Path) -> Path:
    notebook = nbformat.v4.new_notebook()
    path = tmp_path / "empty.ipynb"
    nbformat.write(notebook, path)
    return path


@pytest.fixture
def mixed_notebook(tmp_path: Path) -> Path:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("# Title\n\nSome notes about pandas."),
            nbformat.v4.new_code_cell("import pandas as pd\npd.DataFrame({'x': [1, 2]})"),
        ],
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
    )
    set_stable_id(notebook.cells[0], "nbctx-markdown")
    set_stable_id(notebook.cells[1], "nbctx-code")
    notebook.cells[1]["execution_count"] = 7
    notebook.cells[1]["outputs"] = [
        nbformat.v4.new_output("stream", name="stdout", text="hello\n"),
    ]
    path = tmp_path / "mixed.ipynb"
    nbformat.write(notebook, path)
    return path


@pytest.fixture
def missing_ids_notebook(tmp_path: Path) -> Path:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("No ID here"),
            nbformat.v4.new_code_cell("print('also missing')"),
        ]
    )
    path = tmp_path / "missing.ipynb"
    nbformat.write(notebook, path)
    return path
