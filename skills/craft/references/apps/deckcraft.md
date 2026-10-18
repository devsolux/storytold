# DeckCraft

## Choose this app

Slide decks and presentations. Native server key: `deckcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `deckcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`deckcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/deckcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots (since 0.8.0), but the catalog
launches plain `mcp` without them: assume OS-user-wide access.

## Discover before execution

Discover presentation/slide inspection, shape/text/chart operations, save and export. Read the actual export schema before exporting PDF: when pdf is listed it takes layout (slides, notes, handouts), perPage, dpi, paper and orientation (notes/handouts) and slide options; gif (one frame per slide) takes width, secondsPerSlide and loop. Every tool refuses an argument that is not in its schema; keys inside run_command's params are the command's. Tools include inspect_document, inspect_slide, render_slide, add_shape, set_text, insert_chart, save_presentation and export; screenshot and call_app are listed headless but need --connect.

## Workflow and risky operations

Preserve approved narrative/data and make layout changes only within scope. The catalog passes neither --automation-read-root nor --automation-write-root, so file paths are unconfined. batch stops at the first error without rollback. A headless session starts with no presentation open (inspect_document returns "no presentation open"); call new_presentation or open_presentation first. Save a separate editable native deck and requested interchange export when required.

## Durable verification

Reopen PPTX/native output, check slide count/content and render every slide. Review text overflow, charts, fonts, notes/handouts and warnings. A ZIP/XML check does not establish PowerPoint fidelity.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-18 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/deckcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
