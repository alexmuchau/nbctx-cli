from __future__ import annotations

import json
from pathlib import Path

import nbformat
import pytest

from nbctx.cli import build_parser, main
from nbctx.notebooks import read_notebook, set_stable_id, stable_id


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
    assert "Invalid JSON in notebook" in error["error"]


def test_schema_invalid_notebook_can_be_inspected(
    capsys: pytest.CaptureFixture[str],
    missing_stream_name_notebook: Path,
) -> None:
    assert main(["inspect", str(missing_stream_name_notebook)]) == 0
    inspect_output = json.loads(capsys.readouterr().out)
    assert inspect_output["cell_count"] == 1

    assert main(["cells", str(missing_stream_name_notebook)]) == 0
    cells_output = json.loads(capsys.readouterr().out)
    assert cells_output["cells"][0]["id"] == "nbctx-code"

    assert main(["show", str(missing_stream_name_notebook), "--cell", "nbctx-code"]) == 0
    show_output = json.loads(capsys.readouterr().out)
    assert show_output["source"] == "print('hello')"


def test_validate_reports_schema_error_with_repair_guidance(
    capsys: pytest.CaptureFixture[str],
    missing_stream_name_notebook: Path,
) -> None:
    assert main(["validate", str(missing_stream_name_notebook)]) == 1
    output = json.loads(capsys.readouterr().out)
    assert not output["ok"]
    assert any("schema/structure" in error for error in output["errors"])
    assert any("nbctx repair" in warning for warning in output["warnings"])


def test_repair_dry_run_reports_without_writing(
    capsys: pytest.CaptureFixture[str],
    missing_stream_name_notebook: Path,
) -> None:
    before = missing_stream_name_notebook.read_text(encoding="utf-8")
    assert main(["repair", str(missing_stream_name_notebook), "--dry-run"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["ok"]
    assert output["changed"]
    assert output["changes"] == ["Cell 0 output 0: set missing stream name to stdout"]
    assert missing_stream_name_notebook.read_text(encoding="utf-8") == before


def test_repair_writes_stream_name_and_preserves_text(
    capsys: pytest.CaptureFixture[str],
    missing_stream_name_notebook: Path,
) -> None:
    assert main(["repair", str(missing_stream_name_notebook)]) == 0
    output = json.loads(capsys.readouterr().out)
    notebook = nbformat.read(missing_stream_name_notebook, as_version=4)
    assert output["changed"]
    assert notebook.cells[0]["outputs"][0]["name"] == "stdout"
    assert notebook.cells[0]["outputs"][0]["text"] == "hello\n"
    assert notebook.cells[0]["execution_count"] == 3
    assert stable_id(notebook.cells[0]) == "nbctx-code"


def test_append_fails_on_unrepairable_schema_issue(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("print('bad outputs')")])
    set_stable_id(notebook.cells[0], "nbctx-code")
    path = tmp_path / "bad-structure.ipynb"
    nbformat.write(notebook, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["cells"][0]["outputs"] = [{"output_type": "stream", "name": 5, "text": "hello\n"}]
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    source = tmp_path / "cell.py"
    source.write_text("print('new')", encoding="utf-8")

    assert main(["append", str(path), "--type", "code", "--source", str(source)]) == 1
    error = json.loads(capsys.readouterr().err)
    assert "schema/structure" in error["error"]
    assert "Invalid JSON" not in error["error"]


def test_index_help_mentions_stable_ids() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "Add missing stable IDs and generate context files." in help_text
    assert "repair" in help_text
