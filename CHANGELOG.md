# Changelog

## Unreleased

- Add `nbctx repair` with `--dry-run` to fix known safe notebook inconsistencies, starting with code-cell `stream` outputs missing `name`.
- Distinguish malformed JSON errors from valid JSON notebooks that fail notebook schema/structure validation.
- Auto-apply known safe repairs before `append`, `insert`, `replace`, and `index` write notebooks; these commands now include `repairs` metadata when repairs are applied.
- Preserve notebook safety during repair by keeping output text, metadata, execution counts, cell ordering, and stable nbctx IDs unchanged.

## 0.1.0 - 2026-05-16

- Add `nbctx` CLI for inspecting, listing, showing, searching, appending, inserting, replacing, validating, and indexing Jupyter notebooks.
- Store stable cell IDs under `metadata.nbctx.id`.
- Add `.notebook-cli/` context generation through `nbctx index`.
- Add JSON output by default and markdown output for agent-readable summaries.
