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

Discover document structure, story reading/editing, image placement, page rendering, save and export. Tools include inspect_document, get_story, set_story_text, place_image, render_page, save_document and export_png; PDF, IDML, EPUB and PowerPoint (file.exportPptx, since 0.9.0) export run through execute (for example file.exportPdf; standard x1a, PDF/X-1a:2003, since 0.14.0). Inspect the running schema. A tool argument or an execute/batch params key the command does not take is refused (JSON-RPC -32602), and batch checks every step before the first runs.

## Workflow and risky operations

Text positions are UTF-8 byte offsets, not character counts or JavaScript string lengths. Compute a boundary with len(prefix.encode("utf-8")) only when the native schema requires it. Since 0.10.0 story.replaceRange refuses an offset inside a character, an end past the story or start > end (the error gives the story length in bytes and nothing changes) where 0.9.0 snapped and clamped; in text parameters \u000b is a forced line break like \n. Since 0.13.0 find.find and find.change in document scope also reach table cells: such a match carries cell {table, row, col} and its start/end count from the cell's text. Coordinates use points and spread space; render_page and export_png page indices are 0-based. Commands that create items take spread: a body spread index, or {"kind": "parent", "index": n} for a parent spread (its index in the parents list of inspect_document); any other value is an error. batch stops at the first error (failedIndex) and earlier steps stay applied. Since 0.13.0 a type size outside 0.1 to 1296 pt and an Insert Pages count outside 1 to 9999 are refused. The catalog launches mcp with --automation-read-root (the workspace) and --automation-write-root (outputs/): every open, place, relink, load or import with a path, and the files a document names (links, data sources, book chapters, Document Fonts), must read inside the read root, so a stored path outside it reads as missing; every save, export, package, book and library write inside the write root; a refused path is an ordinary tool error (automation path rejected). Both folders must exist at launch, --connect with them is an error, and the desktop app is never confined; since 0.13.0 each flag may be repeated to add a folder of its kind (a path inside any one passes, their common parent does not). Not covered: path-less commands, the system font scan (also font.reload, 0.10.0, which rescans the installed font folders on request), the recovery folder, and file.print, which hands a PDF to the system print spooler. layout.parents.delete {id} (0.10.0) removes a parent spread's shared artwork and its assignments in one undoable step; local overrides stay as ordinary items. Since 0.11.0 the PDF reader is the shared craft-pdf backend with a 512 MiB input bound: file.place (place_image) and links.relink, links.relinkFolder and links.update refuse a larger PDF before parsing it, as an ordinary tool error naming the command or the path; the bound applies to PDFs only. Since 0.13.0 links.update, links.relink and links.relinkFolder also refuse, by name, any linked file over 256 MiB before reading it, and links.relinkFolder takes only a file directly in the chosen folder.

## Durable verification

Inspect overset text, fonts, linked images, pages and exported layout. Since 0.9.0 a path stored in a document (links, data sources, book chapters, IDML package links) resolves beside it and is followed only on this computer or the document's own share; any other reads as missing, with the reason in links.list and Preflight. Since 0.10.0 file.package writes the packaged document's and IDML's links relative to the package (Links/<name>), which resolve beside the document when it is reopened; links.copyTo still relinks the open document by full path. Since 0.13.0 file.exportPdf keeps a placed PDF's Object Layer Options choice as vector optional content and fails, naming the placed file, when that choice cannot be preserved safely or names a layer the file no longer has (recoverable layer problems become warnings); file.exportIdml with embedImages false refuses a document holding such a choice. Only standard a2b still rasterizes those PDFs, failing since 0.11.0 with the placed file and the reason (a missing page, layers that could not be hidden, an undecodable image, an unsupported font, truncated content) and otherwise warning "N placed PDF(s) with hidden layers exported as images". Since 0.14.0 file.print spools exactly the PDF file.exportPdf writes with the same settings and returns its warnings, and ink.separations (a query) separates a page's spread as that PDF prints, with each ink's coverage, the maximum total ink and areas over inkLimit. Validate the actual saved/exported file and render relevant pages. CLI export options may apply only to following exports; do not use shell fallback without an explicit unique need.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-29 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/designcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
