from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .errors import NbctxError
from .notebooks import (
    append_cell,
    index_notebook,
    inspect_notebook,
    insert_cell,
    list_cells,
    read_notebook,
    read_source,
    repair_notebook_file,
    replace_cell_source,
    search_notebook,
    section_notebook,
    show_cell,
    validate_notebook,
    validation_to_dict,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_command(args)
    except NbctxError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    emit(result, args.format)
    if args.command == "validate" and not result["ok"]:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nbctx", description="Agent-friendly Jupyter notebook CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = add_notebook_command(subparsers, "inspect", "Print notebook metadata and structure.")
    add_format(inspect_parser)

    cells_parser = add_notebook_command(subparsers, "cells", "List notebook cells.")
    add_format(cells_parser)

    show_parser = add_notebook_command(subparsers, "show", "Show full source for one cell.")
    show_parser.add_argument("--cell", required=True, help="Stable nbctx cell ID.")
    add_format(show_parser)

    search_parser = add_notebook_command(subparsers, "search", "Search code and markdown cell source.")
    search_parser.add_argument("query", help="Search query.")
    add_format(search_parser)

    section_parser = add_notebook_command(subparsers, "section", "Extract cells inside markdown heading sections.")
    section_parser.add_argument("query", help="Markdown heading text or ATX heading query.")
    add_format(section_parser)

    append_parser = add_notebook_command(subparsers, "append", "Append a new code or markdown cell.")
    append_parser.add_argument("--type", choices=["code", "markdown"], required=True)
    append_parser.add_argument("--source", required=True, help="Source file path or '-' for stdin.")
    add_format(append_parser)

    replace_parser = add_notebook_command(subparsers, "replace", "Replace one cell source by stable ID.")
    replace_parser.add_argument("--cell", required=True, help="Stable nbctx cell ID.")
    replace_parser.add_argument("--source", required=True, help="Source file path or '-' for stdin.")
    add_format(replace_parser)

    insert_parser = add_notebook_command(subparsers, "insert", "Insert a new cell after a target cell.")
    insert_parser.add_argument("--after", required=True, help="Stable nbctx cell ID to insert after.")
    insert_parser.add_argument("--type", choices=["code", "markdown"], required=True)
    insert_parser.add_argument("--source", required=True, help="Source file path or '-' for stdin.")
    add_format(insert_parser)

    validate_parser = add_notebook_command(subparsers, "validate", "Validate notebook structure and nbctx IDs.")
    add_format(validate_parser)

    repair_parser = add_notebook_command(subparsers, "repair", "Repair known safe notebook inconsistencies.")
    repair_parser.add_argument("--dry-run", action="store_true", help="Report repairs without writing the notebook.")
    add_format(repair_parser)

    index_parser = add_notebook_command(subparsers, "index", "Add missing stable IDs and generate context files.")
    add_format(index_parser)

    return parser


def add_notebook_command(subparsers: argparse._SubParsersAction, name: str, help_text: str) -> argparse.ArgumentParser:
    command = subparsers.add_parser(name, help=help_text)
    command.add_argument("notebook", type=Path, help="Path to a local .ipynb file.")
    return command


def add_format(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")


def run_command(args: argparse.Namespace) -> dict[str, Any]:
    path = args.notebook
    if args.command == "inspect":
        return inspect_notebook(path, read_notebook(path))
    if args.command == "cells":
        return list_cells(read_notebook(path))
    if args.command == "show":
        return show_cell(read_notebook(path), args.cell)
    if args.command == "search":
        return search_notebook(read_notebook(path), args.query)
    if args.command == "section":
        return section_notebook(read_notebook(path), args.query)
    if args.command == "append":
        return append_cell(path, args.type, read_source(args.source))
    if args.command == "replace":
        return replace_cell_source(path, args.cell, read_source(args.source))
    if args.command == "insert":
        return insert_cell(path, args.after, args.type, read_source(args.source))
    if args.command == "validate":
        return validation_to_dict(validate_notebook(path))
    if args.command == "repair":
        return repair_notebook_file(path, dry_run=args.dry_run)
    if args.command == "index":
        return index_notebook(path)
    raise NbctxError(f"Unknown command: {args.command}")


def emit(result: dict[str, Any], output_format: str) -> None:
    if output_format == "markdown":
        markdown = result.get("markdown")
        if markdown is None:
            markdown = json.dumps(result, indent=2)
        print(markdown, end="" if markdown.endswith("\n") else "\n")
        return
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
