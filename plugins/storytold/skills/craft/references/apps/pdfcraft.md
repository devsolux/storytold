# PdfCraft

## Choose this app

PDF inspection, operations and validation. Native server key: `pdfcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `pdfcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`pdfcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/pdfcraft-cli`); the
release also publishes a standalone `pdfcraft-cli-<version>-linux-x86_64.tar.gz`, which `setup` prefers.
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
The catalog launches `mcp` with `--automation-read-root` (the workspace),
`--automation-write-root` (outputs/) and `--root` (the workspace). Both kinds apply (since 0.9.0),
so reads stay in the workspace and writes in outputs/; still test the pinned binary and OS boundary.

## Discover before execution

Discover actual PDF tools; compact mode may expose tool_search/tool_call rather than every operation. The pinned build must include MCP support (on by default in releases). Compact mode lists fifteen core tools (doc_open, doc_info, doc_inspect, doc_save, doc_close, doc_combine, doc_split, edit_undo, page_render, render_preview, text_extract, text_find, command_list, command_run, command_batch) plus tool_search and tool_call; tool_call reaches all 171 tools by name (0.10.1 adds page_reverse; page_duplicate takes an optional at; doc_set_info also sets custom properties, which doc_info lists under custom). Inspect document and page structure before choosing edits.

## Workflow and risky operations

Every file a tool reads must lie inside the read root and every file it writes (doc_save, also in place, extracts, splits, exports, reports, signing output) inside the write root, so save to outputs/, never over an input; a refused path is an ordinary tool error (automation path rejected). Without directories, text_font_files searches the read root, not the installed fonts. Edits stay in memory until an explicit doc_save; saving in place appends an incremental update that keeps the original bytes, except after redaction, sanitizing or an encryption change, and for a file whose cross-reference index had to be rebuilt on open, which are written in full (the result's incremental field says which happened). A save never replaces a read-only file (refused before anything is written) and keeps a replaced file's Unix mode and macOS/Windows creation date (0.10.1). doc_close refuses a document with unsaved changes, a new or recovered one even after undo, unless discard_changes is true. Work on a new output. Destructive page/security/redaction/XFA changes require explicit permission (xfa_to_static, and doc_flatten of an XFA form's fields, remove its XFA template, data and scripts; text_edit refuses a rewrite that would remove text drawn as a clipping path); do not drive the separate desktop ui channel. Roots check file paths only: a doc_print job sent to a printer and a Keychain/Windows-store identity for sign_document are outside them.

## Durable verification

Reopen the saved PDF and check page count, text and rendering. For redactions, use a genuine content-removal audit and inspect sanitized output; visual rectangles are not enough. redact_mark removes nothing until redact_apply, whose verification pass must succeed; it also removes the replies of the comments it removes and clears image pixels under the marks, and it refuses, leaving the document unchanged, a tagged PDF whose structure tree it cannot clean completely (0.10.1); then check doc_hidden_info and doc_revisions. Sanitizing the hidden-layers category (doc_remove_hidden, doc_optimize's discard) decides what an optional-content membership dictionary hides by evaluating its /P policy and /VE expression against the default configuration (0.11.0): content under an AllOff or Not rule is removed even when every layer is on, an expression it cannot evaluate (malformed, cyclic or too deep) counts as hidden unless it names only layers that are on, and an off layer that visible content still refers to stays in the configuration; doc_hidden_info counts that content and the image, form and undecodable or too deeply nested XObjects the pass would drop, so its hidden-layers count can be non-zero with no layer switched off. The helper only checks PDF markers, not validity or confidentiality.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-23 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [automation guide](https://github.com/storytold/pdfcraft/blob/main/crates/automation/README.md) and [MCP documentation](https://github.com/storytold/pdfcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
