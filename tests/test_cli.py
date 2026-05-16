from __future__ import annotations

import json
from pathlib import Path

import nbformat
import pytest

from nbctx.cli import main
from nbctx.notebooks import read_notebook, stable_id


def test_inspect_json_output_shape(capsys: pytest.CaptureFixture[str], mixed_notebook: Path) -> None:
    assert main(["inspect", str(mixed_notebook)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["cell_count"] == 2
    assert output["structure"][0]["id"] == "nbctx-markdown"
    assert "markdown" in output


def test_cells_markdown_output(capsys: pytest.CaptureFixture[str], mixed_notebook: Path) -> None:
    assert main(["cells", str(mixed_notebook), "--format", "markdown"]) == 0
    output = capsys.readouterr().out
    assert "# Cells" in output
    assert "`nbctx-code`" in output


def test_append_from_file(capsys: pytest.CaptureFixture[str], tmp_path: Path, empty_notebook: Path) -> None:
    source = tmp_path / "cell.py"
    source.write_text("print('from file')", encoding="utf-8")
    assert main(["append", str(empty_notebook), "--type", "code", "--source", str(source)]) == 0
    output = json.loads(capsys.readouterr().out)
    notebook = read_notebook(empty_notebook)
    assert output["ok"]
    assert notebook.cells[0]["source"] == "print('from file')"
    assert stable_id(notebook.cells[0]) is not None


def test_append_from_stdin(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    empty_notebook: Path,
) -> None:
    class Stdin:
        @staticmethod
        def read() -> str:
            return "# From stdin"

    monkeypatch.setattr("sys.stdin", Stdin())
    assert main(["append", str(empty_notebook), "--type", "markdown", "--source", "-"]) == 0
    capsys.readouterr()
    notebook = read_notebook(empty_notebook)
    assert notebook.cells[0]["source"] == "# From stdin"


def test_insert_after_cell(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, mixed_notebook: Path) -> None:
    class Stdin:
        @staticmethod
        def read() -> str:
            return "Inserted notes"

    monkeypatch.setattr("sys.stdin", Stdin())
    assert main(["insert", str(mixed_notebook), "--after", "nbctx-markdown", "--type", "markdown", "--source", "-"]) == 0
    output = json.loads(capsys.readouterr().out)
    notebook = nbformat.read(mixed_notebook, as_version=4)
    assert output["cell"]["index"] == 1
    assert notebook.cells[1]["cell_type"] == "markdown"
    assert notebook.cells[1]["source"] == "Inserted notes"


def test_validate_returns_nonzero_for_duplicate_ids(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("A"),
            nbformat.v4.new_markdown_cell("B"),
        ]
    )
    notebook.cells[0]["metadata"]["nbctx"] = {"id": "dup"}
    notebook.cells[1]["metadata"]["nbctx"] = {"id": "dup"}
    path = tmp_path / "dup.ipynb"
    nbformat.write(notebook, path)

    assert main(["validate", str(path)]) == 1
    output = json.loads(capsys.readouterr().out)
    assert not output["ok"]
    assert output["duplicate_ids"] == ["dup"]


def test_malformed_notebook_rejected(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    path = tmp_path / "bad.ipynb"
    path.write_text("{bad json", encoding="utf-8")
    assert main(["inspect", str(path)]) == 1
    error = json.loads(capsys.readouterr().err)
    assert not error["ok"]
    assert "Could not read notebook" in error["error"]
