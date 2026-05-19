from __future__ import annotations

from pathlib import Path

import nbformat

from nbctx.notebooks import (
    append_cell,
    ensure_stable_ids,
    index_notebook,
    inspect_notebook,
    list_cells,
    read_notebook,
    repair_notebook_file,
    insert_cell,
    replace_cell_source,
    search_notebook,
    section_notebook,
    set_stable_id,
    stable_id,
    validate_notebook,
)


def test_read_valid_notebook(mixed_notebook: Path) -> None:
    notebook = read_notebook(mixed_notebook)
    result = inspect_notebook(mixed_notebook, notebook)
    assert result["cell_count"] == 2
    assert result["cell_counts"] == {"markdown": 1, "code": 1}
    assert result["language_info"]["name"] == "python"


def test_generate_stable_ids_only_when_missing(mixed_notebook: Path, missing_ids_notebook: Path) -> None:
    existing = read_notebook(mixed_notebook)
    assert ensure_stable_ids(existing) == []
    assert stable_id(existing.cells[0]) == "nbctx-markdown"

    missing = read_notebook(missing_ids_notebook)
    added = ensure_stable_ids(missing)
    assert len(added) == 2
    assert stable_id(missing.cells[0]) in added
    assert stable_id(missing.cells[1]) in added


def test_list_cells_shape(mixed_notebook: Path) -> None:
    result = list_cells(read_notebook(mixed_notebook))
    assert result["cell_count"] == 2
    assert result["cells"][0]["id"] == "nbctx-markdown"
    assert result["cells"][1]["execution_count"] == 7
    assert "markdown" in result


def test_search_returns_matching_cells(mixed_notebook: Path) -> None:
    result = search_notebook(read_notebook(mixed_notebook), "pandas")
    assert result["match_count"] == 2
    assert {match["id"] for match in result["matches"]} == {"nbctx-markdown", "nbctx-code"}


def test_section_returns_cells_until_next_sibling_heading(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("# Title 1"),
            nbformat.v4.new_markdown_cell("Intro"),
            nbformat.v4.new_markdown_cell("## Title 2"),
            nbformat.v4.new_markdown_cell("Body"),
            nbformat.v4.new_code_cell("c = 3"),
            nbformat.v4.new_markdown_cell("### Child"),
            nbformat.v4.new_code_cell("nested = True"),
            nbformat.v4.new_markdown_cell("## Next"),
            nbformat.v4.new_code_cell("outside = True"),
        ]
    )
    for index, cell in enumerate(notebook.cells):
        set_stable_id(cell, f"nbctx-cell-{index}")

    result = section_notebook(notebook, "## Title 2")

    assert result["section_count"] == 1
    assert result["cell_count"] == 4
    section = result["sections"][0]
    assert section["heading"] == {"id": "nbctx-cell-2", "index": 2, "level": 2, "text": "Title 2"}
    assert [cell["id"] for cell in section["cells"]] == [
        "nbctx-cell-3",
        "nbctx-cell-4",
        "nbctx-cell-5",
        "nbctx-cell-6",
    ]
    assert section["cells"][1]["source"] == "c = 3"


def test_section_parent_includes_nested_subsections(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("# Title 1"),
            nbformat.v4.new_markdown_cell("Intro"),
            nbformat.v4.new_markdown_cell("## Child"),
            nbformat.v4.new_code_cell("inside = True"),
            nbformat.v4.new_markdown_cell("# Outside"),
            nbformat.v4.new_code_cell("outside = True"),
        ]
    )
    for index, cell in enumerate(notebook.cells):
        set_stable_id(cell, f"nbctx-parent-{index}")

    result = section_notebook(notebook, "# Title 1")

    assert result["section_count"] == 1
    assert [cell["index"] for cell in result["sections"][0]["cells"]] == [1, 2, 3]


def test_section_normalizes_text_and_optional_closing_hashes() -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("##   Title   2   ###"),
            nbformat.v4.new_code_cell("matched = True"),
        ]
    )
    set_stable_id(notebook.cells[0], "nbctx-heading")
    set_stable_id(notebook.cells[1], "nbctx-body")

    result = section_notebook(notebook, "title 2")

    assert result["section_count"] == 1
    assert result["sections"][0]["heading"]["text"] == "Title 2"
    assert result["sections"][0]["cells"][0]["id"] == "nbctx-body"


def test_section_query_with_hashes_requires_matching_level() -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("## Title"),
            nbformat.v4.new_code_cell("matched = True"),
        ]
    )
    set_stable_id(notebook.cells[0], "nbctx-heading")
    set_stable_id(notebook.cells[1], "nbctx-body")

    result = section_notebook(notebook, "# Title")

    assert result["sections"] == []
    assert result["section_count"] == 0
    assert result["cell_count"] == 0


def test_section_duplicate_headings_return_in_order() -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("## Repeat"),
            nbformat.v4.new_code_cell("first = True"),
            nbformat.v4.new_markdown_cell("## Repeat"),
            nbformat.v4.new_code_cell("second = True"),
        ]
    )
    for index, cell in enumerate(notebook.cells):
        if index != 3:
            set_stable_id(cell, f"nbctx-repeat-{index}")

    result = section_notebook(notebook, "Repeat")

    assert result["section_count"] == 2
    assert result["cell_count"] == 2
    assert [section["heading"]["index"] for section in result["sections"]] == [0, 2]
    assert result["sections"][1]["cells"][0]["id"] is None


def test_section_no_match_is_successful_empty_result(mixed_notebook: Path) -> None:
    result = section_notebook(read_notebook(mixed_notebook), "Missing")

    assert result["sections"] == []
    assert result["section_count"] == 0
    assert result["cell_count"] == 0


def test_append_preserves_existing_output(mixed_notebook: Path) -> None:
    result = append_cell(mixed_notebook, "markdown", "## Added")
    notebook = read_notebook(mixed_notebook)
    assert result["cell"]["type"] == "markdown"
    assert len(notebook.cells) == 3
    assert notebook.cells[1]["outputs"][0]["text"] == "hello\n"
    assert notebook.cells[1]["execution_count"] == 7


def test_repair_file_preserves_stream_text_and_stable_ids(missing_stream_name_notebook: Path) -> None:
    result = repair_notebook_file(missing_stream_name_notebook)
    notebook = nbformat.read(missing_stream_name_notebook, as_version=4)
    assert result["changed"]
    assert notebook.cells[0]["outputs"][0]["name"] == "stdout"
    assert notebook.cells[0]["outputs"][0]["text"] == "hello\n"
    assert notebook.cells[0]["execution_count"] == 3
    assert stable_id(notebook.cells[0]) == "nbctx-code"


def test_validate_succeeds_after_repair(missing_stream_name_notebook: Path) -> None:
    repair_notebook_file(missing_stream_name_notebook)
    result = validate_notebook(missing_stream_name_notebook)
    assert result.ok


def test_replace_preserves_metadata_outputs_and_execution_count(mixed_notebook: Path) -> None:
    replace_cell_source(mixed_notebook, "nbctx-code", "print('changed')")
    notebook = read_notebook(mixed_notebook)
    assert notebook.cells[1]["source"] == "print('changed')"
    assert stable_id(notebook.cells[1]) == "nbctx-code"
    assert notebook.cells[1]["outputs"][0]["text"] == "hello\n"
    assert notebook.cells[1]["execution_count"] == 7


def test_append_auto_repairs_before_writing(missing_stream_name_notebook: Path) -> None:
    result = append_cell(missing_stream_name_notebook, "markdown", "## Added")
    notebook = nbformat.read(missing_stream_name_notebook, as_version=4)
    assert result["repairs"]["changed"]
    assert notebook.cells[0]["outputs"][0]["name"] == "stdout"
    assert notebook.cells[0]["outputs"][0]["text"] == "hello\n"
    assert notebook.cells[1]["source"] == "## Added"


def test_insert_auto_repairs_before_writing(missing_stream_name_notebook: Path) -> None:
    result = insert_cell(missing_stream_name_notebook, "nbctx-code", "markdown", "Inserted")
    notebook = nbformat.read(missing_stream_name_notebook, as_version=4)
    assert result["repairs"]["changed"]
    assert notebook.cells[0]["outputs"][0]["name"] == "stdout"
    assert notebook.cells[1]["source"] == "Inserted"


def test_replace_auto_repairs_before_writing(missing_stream_name_notebook: Path) -> None:
    result = replace_cell_source(missing_stream_name_notebook, "nbctx-code", "print('changed')")
    notebook = nbformat.read(missing_stream_name_notebook, as_version=4)
    assert result["repairs"]["changed"]
    assert notebook.cells[0]["source"] == "print('changed')"
    assert notebook.cells[0]["outputs"][0]["name"] == "stdout"
    assert notebook.cells[0]["outputs"][0]["text"] == "hello\n"


def test_validate_detects_duplicate_stable_ids(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("A"),
            nbformat.v4.new_code_cell("B"),
        ]
    )
    set_stable_id(notebook.cells[0], "same")
    set_stable_id(notebook.cells[1], "same")
    path = tmp_path / "dupes.ipynb"
    nbformat.write(notebook, path)

    result = validate_notebook(path)
    assert not result.ok
    assert result.duplicate_ids == ["same"]


def test_index_creates_context_and_adds_missing_ids(missing_ids_notebook: Path) -> None:
    result = index_notebook(missing_ids_notebook)
    context_dir = Path(result["context_dir"])
    assert context_dir.exists()
    assert (context_dir / "cell-map.json").exists()
    assert (context_dir / "summary.md").exists()
    assert (context_dir / "notes.md").exists()
    assert len(result["added_ids"]) == 2

    notebook = read_notebook(missing_ids_notebook)
    assert stable_id(notebook.cells[0]) is not None
    assert stable_id(notebook.cells[1]) is not None


def test_index_auto_repairs_before_writing(missing_stream_name_notebook: Path) -> None:
    result = index_notebook(missing_stream_name_notebook)
    notebook = nbformat.read(missing_stream_name_notebook, as_version=4)
    assert result["repairs"]["changed"]
    assert notebook.cells[0]["outputs"][0]["name"] == "stdout"
    assert notebook.cells[0]["outputs"][0]["text"] == "hello\n"
