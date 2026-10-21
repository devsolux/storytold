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
Native source documents distinct read/write roots (since 0.9.0); still test the pinned binary and OS boundary.

## Discover before execution

Discover document structure, story reading/editing, image placement, page rendering, save and export. Tools include inspect_document, get_story, set_story_text, place_image, render_page, save_document and export_png; PDF, IDML, EPUB and PowerPoint (file.exportPptx, since 0.9.0) export run through execute (for example file.exportPdf). Inspect the running schema. A tool argument or an execute/batch params key the command does not take is refused (JSON-RPC -32602), and batch checks every step before the first runs.

## Workflow and risky operations

Text positions are UTF-8 byte offsets, not character counts or JavaScript string lengths. Compute a boundary with len(prefix.encode("utf-8")) only when the native schema requires it. Since 0.10.0 story.replaceRange refuses an offset inside a character, an end past the story or start > end (the error gives the story length in bytes and nothing changes) where 0.9.0 snapped and clamped; in text parameters \u000b is a forced line break like \n. Coordinates use points and spread space; render_page and export_png page indices are 0-based. Commands that create items take spread: a body spread index, or {"kind": "parent", "index": n} for a parent spread (its index in the parents list of inspect_document); any other value is an error. batch stops at the first error (failedIndex) and earlier steps stay applied. The catalog launches mcp with --automation-read-root (the workspace) and --automation-write-root (outputs/): every open, place, relink, load or import with a path, and the files a document names (links, data sources, book chapters, Document Fonts), must read inside the read root, so a stored path outside it reads as missing; every save, export, package, book and library write inside the write root; a refused path is an ordinary tool error (automation path rejected). Both folders must exist at launch, each flag is given once, --connect with them is an error, and the desktop app is never confined. Not covered: path-less commands, the system font scan (also font.reload, 0.10.0, which rescans the installed font folders on request), the recovery folder, and file.print, which hands a PDF to the system print spooler. layout.parents.delete {id} (0.10.0) removes a parent spread's shared artwork and its assignments in one undoable step; local overrides stay as ordinary items.

## Durable verification

Inspect overset text, fonts, linked images, pages and exported layout. Since 0.9.0 a path stored in a document (links, data sources, book chapters, IDML package links) resolves beside it and is followed only on this computer or the document's own share; any other reads as missing, with the reason in links.list and Preflight. Since 0.10.0 file.package writes the packaged document's and IDML's links relative to the package (Links/<name>), which resolve beside the document when it is reopened; links.copyTo still relinks the open document by full path. Validate the actual saved/exported file and render relevant pages. CLI export options may apply only to following exports; do not use shell fallback without an explicit unique need.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-21 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/designcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
