# DesignCraft

## Choose this app

Page layout, stories and publishing. Native server key: `designcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `designcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`designcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/designcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots (since 0.9.0), but the catalog
launches plain `mcp` without them: assume OS-user-wide access.

## Discover before execution

Discover document structure, story reading/editing, image placement, page rendering, save and export. Tools include inspect_document, get_story, set_story_text, place_image, render_page, save_document and export_png; PDF, IDML, EPUB and PowerPoint (file.exportPptx, since 0.9.0) export run through execute (for example file.exportPdf). Inspect the running schema. A tool argument or an execute/batch params key the command does not take is refused (JSON-RPC -32602), and batch checks every step before the first runs.

## Workflow and risky operations

Text positions are UTF-8 byte offsets, not character counts or JavaScript string lengths. Compute a boundary with len(prefix.encode("utf-8")) only when the native schema requires it. Coordinates use points and spread space; render_page and export_png page indices are 0-based. Commands that create items take spread: a body spread index, or {"kind": "parent", "index": n} for a parent spread (its index in the parents list of inspect_document); any other value is an error. batch stops at the first error (failedIndex) and earlier steps stay applied. The catalog passes neither --automation-read-root nor --automation-write-root, so file paths are unconfined.

## Durable verification

Inspect overset text, fonts, linked images, pages and exported layout. Since 0.9.0 a path stored in a document (links, data sources, book chapters, IDML package links) resolves beside it and is followed only on this computer or the document's own share; any other reads as missing, with the reason in links.list and Preflight. Validate the actual saved/exported file and render relevant pages. CLI export options may apply only to following exports; do not use shell fallback without an explicit unique need.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-18 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/designcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
