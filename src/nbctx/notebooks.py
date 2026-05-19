from __future__ import annotations

import json
import sys
import uuid
from copy import deepcopy
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import nbformat

from .errors import NbctxError

NBCTX_METADATA_KEY = "nbctx"
NBCTX_ID_KEY = "id"
PREVIEW_CHARS = 120


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    cell_count: int
    missing_ids: list[int]
    duplicate_ids: list[str]


@dataclass(frozen=True)
class RepairResult:
    changed: bool
    changes: list[str]
    warnings: list[str]


def read_notebook(path: Path) -> Any:
    if not path.exists():
        raise NbctxError(f"Notebook not found: {path}")
    if not path.is_file():
        raise NbctxError(f"Notebook path is not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
        json.loads(text)
    except UnicodeDecodeError as exc:
        raise NbctxError(f"Could not read notebook {path}: {exc}") from exc
    except JSONDecodeError as exc:
        raise NbctxError(f"Invalid JSON in notebook {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    try:
        return nbformat.reads(text, as_version=4)
    except Exception as exc:
        raise NbctxError(f"Notebook structure error in {path}: {exc}") from exc


def write_notebook(path: Path, notebook: Any) -> None:
    try:
        nbformat.write(notebook, path)
    except Exception as exc:
        raise NbctxError(f"Could not write notebook {path}: {exc}") from exc


def validate_schema(notebook: Any) -> str | None:
    try:
        nbformat.validate(notebook)
    except Exception as exc:
        return str(exc)
    return None


def ensure_writable_notebook(path: Path, notebook: Any) -> RepairResult:
    repairs = repair_notebook(notebook)
    schema_error = validate_schema(notebook)
    if schema_error:
        guidance = ""
        if repairs.changed:
            guidance = f" Known safe repairs were applied, but additional schema issues remain. Run nbctx validate {path}"
        raise NbctxError(f"Notebook schema/structure validation failed: {schema_error}{guidance}")
    return repairs


def repair_notebook(notebook: Any, apply: bool = True) -> RepairResult:
    changes: list[str] = []
    warnings: list[str] = []
    cells = notebook.get("cells", [])
    for cell_index, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        outputs = cell.get("outputs", [])
        if not isinstance(outputs, list):
            warnings.append(f"Cell {cell_index} outputs are not a list; skipped stream-name repair scan")
            continue
        for output_index, output in enumerate(outputs):
            if not isinstance(output, dict):
                warnings.append(f"Cell {cell_index} output {output_index} is not an object; skipped")
                continue
            if output.get("output_type") != "stream":
                continue
            if output.get("name"):
                continue
            changes.append(f"Cell {cell_index} output {output_index}: set missing stream name to stdout")
            if apply:
                output["name"] = "stdout"
    return RepairResult(changed=bool(changes), changes=changes, warnings=warnings)


def repair_notebook_file(path: Path, dry_run: bool = False) -> dict[str, Any]:
    notebook = read_notebook(path)
    target = deepcopy(notebook) if dry_run else notebook
    repairs = repair_notebook(target)
    warnings = list(repairs.warnings)
    schema_error = validate_schema(target)
    if schema_error and dry_run:
        warnings.append(f"Additional notebook schema/structure issues remain: {schema_error}")
    if schema_error and not dry_run:
        if repairs.changed:
            raise NbctxError(f"Notebook schema/structure validation failed after repair: {schema_error}")
        raise NbctxError(f"Notebook schema/structure validation failed; no known safe repairs apply: {schema_error}")
    if not dry_run and repairs.changed:
        write_notebook(path, target)
    result = {
        "ok": True,
        "action": "repair",
        "changed": repairs.changed,
        "changes": repairs.changes,
        "warnings": warnings,
    }
    result["markdown"] = render_repair_markdown(path, result, dry_run)
    return result


def repairs_to_dict(repairs: RepairResult) -> dict[str, Any]:
    return {
        "changed": repairs.changed,
        "changes": repairs.changes,
        "warnings": repairs.warnings,
    }


def stable_id(cell: Any) -> str | None:
    metadata = cell.get("metadata", {})
    nbctx_metadata = metadata.get(NBCTX_METADATA_KEY, {})
    value = nbctx_metadata.get(NBCTX_ID_KEY)
    return value if isinstance(value, str) and value else None


def set_stable_id(cell: Any, value: str) -> None:
    metadata = cell.setdefault("metadata", {})
    nbctx_metadata = metadata.setdefault(NBCTX_METADATA_KEY, {})
    nbctx_metadata[NBCTX_ID_KEY] = value


def existing_ids(notebook: Any) -> set[str]:
    return {value for cell in notebook.cells if (value := stable_id(cell))}


def generate_stable_id(used: set[str]) -> str:
    while True:
        candidate = f"nbctx-{uuid.uuid4().hex[:12]}"
        if candidate not in used:
            used.add(candidate)
            return candidate


def ensure_stable_ids(notebook: Any) -> list[str]:
    used = existing_ids(notebook)
    added: list[str] = []
    for cell in notebook.cells:
        if stable_id(cell) is None:
            new_id = generate_stable_id(used)
            set_stable_id(cell, new_id)
            added.append(new_id)
    return added


def find_cell(notebook: Any, cell_id: str) -> tuple[int, Any]:
    matches = [(index, cell) for index, cell in enumerate(notebook.cells) if stable_id(cell) == cell_id]
    if not matches:
        raise NbctxError(f"Cell not found: {cell_id}")
    if len(matches) > 1:
        raise NbctxError(f"Duplicate stable cell ID prevents safe edit: {cell_id}")
    return matches[0]


def read_source(source_path: str) -> str:
    if source_path == "-":
        return sys.stdin.read()
    path = Path(source_path)
    if not path.exists():
        raise NbctxError(f"Source file not found: {path}")
    if not path.is_file():
        raise NbctxError(f"Source path is not a file: {path}")
    return path.read_text(encoding="utf-8")


def make_cell(cell_type: str, source: str, used: set[str]) -> Any:
    if cell_type == "code":
        cell = nbformat.v4.new_code_cell(source=source)
    elif cell_type == "markdown":
        cell = nbformat.v4.new_markdown_cell(source=source)
    else:
        raise NbctxError(f"Unsupported cell type: {cell_type}")
    set_stable_id(cell, generate_stable_id(used))
    return cell


def first_lines(source: str, line_count: int = 3) -> list[str]:
    return source.splitlines()[:line_count]


def preview(source: str, limit: int = PREVIEW_CHARS) -> str:
    text = " ".join(source.strip().split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}..."


def cell_record(index: int, cell: Any) -> dict[str, Any]:
    source = cell.get("source", "")
    metadata = cell.get("metadata", {})
    return {
        "id": stable_id(cell),
        "index": index,
        "type": cell.get("cell_type"),
        "first_lines": first_lines(source),
        "tags": list(metadata.get("tags", [])),
        "execution_count": cell.get("execution_count"),
        "source_length": len(source),
        "preview": preview(source),
    }


def inspect_notebook(path: Path, notebook: Any) -> dict[str, Any]:
    cell_counts: dict[str, int] = {}
    for cell in notebook.cells:
        cell_type = cell.get("cell_type", "unknown")
        cell_counts[cell_type] = cell_counts.get(cell_type, 0) + 1

    metadata = notebook.get("metadata", {})
    language_info = metadata.get("language_info", {})
    kernelspec = metadata.get("kernelspec", {})
    records = [cell_record(index, cell) for index, cell in enumerate(notebook.cells)]
    result = {
        "notebook": str(path),
        "nbformat": notebook.get("nbformat"),
        "nbformat_minor": notebook.get("nbformat_minor"),
        "cell_count": len(notebook.cells),
        "cell_counts": cell_counts,
        "language_info": language_info,
        "kernelspec": kernelspec,
        "structure": [
            {
                "id": record["id"],
                "index": record["index"],
                "type": record["type"],
                "preview": record["preview"],
            }
            for record in records
        ],
    }
    result["markdown"] = render_inspect_markdown(result)
    return result


def list_cells(notebook: Any) -> dict[str, Any]:
    records = [cell_record(index, cell) for index, cell in enumerate(notebook.cells)]
    result = {"cells": records, "cell_count": len(records)}
    result["markdown"] = render_cells_markdown(result)
    return result


def show_cell(notebook: Any, cell_id: str) -> dict[str, Any]:
    index, cell = find_cell(notebook, cell_id)
    source = cell.get("source", "")
    result = {
        "cell": cell_record(index, cell),
        "source": source,
    }
    result["markdown"] = render_show_markdown(result)
    return result


def search_notebook(notebook: Any, query: str) -> dict[str, Any]:
    query_lower = query.lower()
    matches: list[dict[str, Any]] = []
    for index, cell in enumerate(notebook.cells):
        source = cell.get("source", "")
        if query_lower not in source.lower():
            continue
        snippets = matching_snippets(source, query_lower)
        matches.append(
            {
                "id": stable_id(cell),
                "index": index,
                "type": cell.get("cell_type"),
                "snippets": snippets,
            }
        )
    result = {"query": query, "matches": matches, "match_count": len(matches)}
    result["markdown"] = render_search_markdown(result)
    return result


def matching_snippets(source: str, query_lower: str, context: int = 60) -> list[str]:
    source_lower = source.lower()
    snippets: list[str] = []
    start = 0
    while True:
        match_index = source_lower.find(query_lower, start)
        if match_index == -1:
            break
        snippet_start = max(0, match_index - context)
        snippet_end = min(len(source), match_index + len(query_lower) + context)
        snippet = source[snippet_start:snippet_end].replace("\n", "\\n")
        snippets.append(snippet)
        start = match_index + len(query_lower)
    return snippets[:5]


def validate_notebook(path: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    missing_ids: list[int] = []
    duplicate_ids: list[str] = []
    notebook = read_notebook(path)

    schema_error = validate_schema(notebook)
    if schema_error:
        errors.append(f"Notebook schema/structure validation failed: {schema_error}")
        repairs = repair_notebook(notebook, apply=False)
        if repairs.changed:
            warnings.append(f"Known safe repairs are available. Run nbctx repair {path}")

    seen: set[str] = set()
    duplicated_seen: set[str] = set()
    for index, cell in enumerate(notebook.cells):
        if cell.get("cell_type") not in {"code", "markdown", "raw"}:
            errors.append(f"Cell {index} has unsupported or missing cell_type")
        if "source" not in cell:
            errors.append(f"Cell {index} is missing source")
        value = stable_id(cell)
        if value is None:
            missing_ids.append(index)
            continue
        if value in seen and value not in duplicated_seen:
            duplicate_ids.append(value)
            duplicated_seen.add(value)
        seen.add(value)

    if missing_ids:
        warnings.append(f"{len(missing_ids)} cell(s) missing stable nbctx IDs")
    if duplicate_ids:
        errors.append(f"Duplicate stable nbctx IDs: {', '.join(duplicate_ids)}")
    if not path.parent.exists():
        errors.append(f"Notebook parent directory does not exist: {path.parent}")

    return ValidationResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        cell_count=len(notebook.cells),
        missing_ids=missing_ids,
        duplicate_ids=duplicate_ids,
    )


def validation_to_dict(result: ValidationResult) -> dict[str, Any]:
    output = {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "cell_count": result.cell_count,
        "missing_ids": result.missing_ids,
        "duplicate_ids": result.duplicate_ids,
    }
    output["markdown"] = render_validation_markdown(output)
    return output


def append_cell(path: Path, cell_type: str, source: str) -> dict[str, Any]:
    notebook = read_notebook(path)
    repairs = ensure_writable_notebook(path, notebook)
    used = existing_ids(notebook)
    cell = make_cell(cell_type, source, used)
    notebook.cells.append(cell)
    write_notebook(path, notebook)
    result = {"ok": True, "action": "append", "cell": cell_record(len(notebook.cells) - 1, cell)}
    if repairs.changed:
        result["repairs"] = repairs_to_dict(repairs)
    return result


def insert_cell(path: Path, after_id: str, cell_type: str, source: str) -> dict[str, Any]:
    notebook = read_notebook(path)
    repairs = ensure_writable_notebook(path, notebook)
    target_index, _ = find_cell(notebook, after_id)
    used = existing_ids(notebook)
    cell = make_cell(cell_type, source, used)
    insert_index = target_index + 1
    notebook.cells.insert(insert_index, cell)
    write_notebook(path, notebook)
    result = {"ok": True, "action": "insert", "after": after_id, "cell": cell_record(insert_index, cell)}
    if repairs.changed:
        result["repairs"] = repairs_to_dict(repairs)
    return result


def replace_cell_source(path: Path, cell_id: str, source: str) -> dict[str, Any]:
    notebook = read_notebook(path)
    repairs = ensure_writable_notebook(path, notebook)
    index, cell = find_cell(notebook, cell_id)
    cell["source"] = source
    write_notebook(path, notebook)
    result = {"ok": True, "action": "replace", "cell": cell_record(index, cell)}
    if repairs.changed:
        result["repairs"] = repairs_to_dict(repairs)
    return result


def index_notebook(path: Path) -> dict[str, Any]:
    notebook = read_notebook(path)
    repairs = ensure_writable_notebook(path, notebook)
    added_ids = ensure_stable_ids(notebook)
    if added_ids or repairs.changed:
        write_notebook(path, notebook)

    records = [cell_record(index, cell) for index, cell in enumerate(notebook.cells)]
    context_dir = path.parent / ".notebook-cli" / path.stem
    context_dir.mkdir(parents=True, exist_ok=True)
    cell_map_path = context_dir / "cell-map.json"
    summary_path = context_dir / "summary.md"
    notes_path = context_dir / "notes.md"

    cell_map = {"notebook": str(path), "cells": records, "cell_count": len(records)}
    cell_map_path.write_text(json.dumps(cell_map, indent=2) + "\n", encoding="utf-8")
    summary = render_index_summary(path, cell_map, added_ids)
    summary_path.write_text(summary, encoding="utf-8")
    if not notes_path.exists():
        notes_path.write_text("# Notes\n\n", encoding="utf-8")

    result = {
        "ok": True,
        "notebook": str(path),
        "added_ids": added_ids,
        "context_dir": str(context_dir),
        "cell_map": str(cell_map_path),
        "summary": str(summary_path),
        "notes": str(notes_path),
        "markdown": summary,
    }
    if repairs.changed:
        result["repairs"] = repairs_to_dict(repairs)
    return result


def render_inspect_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# {Path(result['notebook']).name}",
        "",
        f"- Cells: {result['cell_count']}",
        f"- nbformat: {result['nbformat']}.{result['nbformat_minor']}",
    ]
    language = result.get("language_info", {}).get("name")
    kernel = result.get("kernelspec", {}).get("display_name")
    if language:
        lines.append(f"- Language: {language}")
    if kernel:
        lines.append(f"- Kernel: {kernel}")
    lines.extend(["", "## Structure"])
    for item in result["structure"]:
        cell_id = item["id"] or "(missing nbctx id)"
        lines.append(f"- {item['index']}: `{cell_id}` {item['type']} - {item['preview']}")
    return "\n".join(lines) + "\n"


def render_cells_markdown(result: dict[str, Any]) -> str:
    lines = ["# Cells", ""]
    for cell in result["cells"]:
        cell_id = cell["id"] or "(missing nbctx id)"
        lines.append(f"## {cell['index']}: `{cell_id}` ({cell['type']})")
        lines.append(f"- Tags: {', '.join(cell['tags']) if cell['tags'] else '(none)'}")
        lines.append(f"- Execution count: {cell['execution_count']}")
        lines.append(f"- Source length: {cell['source_length']}")
        if cell["first_lines"]:
            lines.append("")
            lines.append("```")
            lines.extend(cell["first_lines"])
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def render_show_markdown(result: dict[str, Any]) -> str:
    cell = result["cell"]
    cell_id = cell["id"] or "(missing nbctx id)"
    fence = "python" if cell["type"] == "code" else "markdown"
    return f"# Cell `{cell_id}`\n\nIndex: {cell['index']}\n\n```{fence}\n{result['source']}\n```\n"


def render_search_markdown(result: dict[str, Any]) -> str:
    lines = [f"# Search: {result['query']}", "", f"Matches: {result['match_count']}", ""]
    for match in result["matches"]:
        cell_id = match["id"] or "(missing nbctx id)"
        lines.append(f"## {match['index']}: `{cell_id}` ({match['type']})")
        for snippet in match["snippets"]:
            lines.append(f"- `{snippet}`")
        lines.append("")
    return "\n".join(lines)


def render_validation_markdown(result: dict[str, Any]) -> str:
    lines = ["# Validation", "", f"- OK: {result['ok']}", f"- Cells: {result['cell_count']}"]
    if result["errors"]:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in result["errors"])
    if result["warnings"]:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in result["warnings"])
    return "\n".join(lines) + "\n"


def render_repair_markdown(path: Path, result: dict[str, Any], dry_run: bool) -> str:
    mode = "Dry run" if dry_run else "Applied"
    lines = [
        "# Repair",
        "",
        f"- Notebook: `{path}`",
        f"- Mode: {mode}",
        f"- Changed: {result['changed']}",
    ]
    if result["changes"]:
        lines.extend(["", "## Changes"])
        lines.extend(f"- {change}" for change in result["changes"])
    if result["warnings"]:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in result["warnings"])
    return "\n".join(lines) + "\n"


def render_index_summary(path: Path, cell_map: dict[str, Any], added_ids: list[str]) -> str:
    lines = [
        f"# Notebook Context: {path.name}",
        "",
        f"- Notebook: `{path}`",
        f"- Cells: {cell_map['cell_count']}",
        f"- Added stable IDs: {len(added_ids)}",
        "",
        "## Cell Map",
    ]
    for cell in cell_map["cells"]:
        lines.append(f"- {cell['index']}: `{cell['id']}` {cell['type']} - {cell['preview']}")
    return "\n".join(lines) + "\n"
