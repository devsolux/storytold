# PdfCraft

## Choose this app

PDF inspection, operations and validation. Native server key: `pdfcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `pdfcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`pdfcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/pdfcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents one root; it does not separate read and write authority.

## Discover before execution

Discover actual PDF tools; compact mode may expose tool_search/tool_call rather than every operation. The pinned build must include MCP support (on by default in releases). The 0.6.0 compact core is doc_open, doc_info, doc_inspect, page_render, text_extract, text_find, doc_save, command_list, command_run and command_batch, plus tool_search and tool_call. Inspect document and page structure before choosing edits.

## Workflow and risky operations

--root confines one tree, not a separate read-only input directory. Edits stay in memory until an explicit doc_save; saving in place appends an incremental update that keeps the original bytes, except after redaction or sanitizing, which force a full rewrite. Work on a new output. Destructive page/security/redaction changes require explicit permission; do not drive the separate desktop ui channel.

## Durable verification

Reopen the saved PDF and check page count, text and rendering. For redactions, use a genuine content-removal audit and inspect sanitized output; visual rectangles are not enough. redact_mark removes nothing until redact_apply, whose verification pass must succeed; then check doc_hidden_info and doc_revisions. The helper only checks PDF markers, not validity or confidentiality.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-12 against the v0.6.0 release
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [automation guide at v0.6.0](https://github.com/storytold/pdfcraft/blob/v0.6.0/crates/automation/README.md) and [MCP notes at v0.6.0](https://github.com/storytold/pdfcraft/blob/v0.6.0/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
