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
Native source documents distinct read/write roots (since 0.8.0); still test the pinned binary and OS boundary.

## Discover before execution

Discover presentation/slide inspection, shape/text/chart operations, save and export. Read the actual export schema before exporting PDF: when pdf is listed it takes layout (slides, notes, handouts), perPage, dpi, paper and orientation (notes/handouts) and slide options; gif (one frame per slide) takes width, secondsPerSlide and loop. Since 0.11.1 format rtf (also picked by a .rtf path, in save_presentation too) writes only the slide outline, and open_presentation turns an RTF file into a new outline deck. Every tool refuses an argument that is not in its schema; keys inside run_command's params are the command's. A PNG without the slide background (0.9.0) is therefore run_command file.export {path, transparentBackground: true}, not an export or render_slide argument; with any other format it is an error. Tools include inspect_document, inspect_slide, render_slide, add_shape, set_text, insert_chart, save_presentation and export; screenshot and call_app are listed headless but need --connect.

## Workflow and risky operations

Preserve approved narrative/data and make layout changes only within scope. The catalog launches mcp with --automation-read-root (the workspace) and --automation-write-root (outputs/): open_presentation and every command that reads a path (inserts, picture.change, slide.reuse, design.browseTheme, review.compare) must read inside the read root, since 0.11.1 a regular file of at most 2 GiB, and every save, export and render_slide with a path (with the .saving temporary file) inside the write root; a refused path is an ordinary tool error (automation path rejected). Both folders must exist at launch, each flag is given once, --connect with them is an error, and the desktop app is never confined. Not covered: path-less commands still read and change the open deck, and the system font and spelling-dictionary scans, the user dictionary file review.addToDictionary appends to, and the recovery folder are not checked. batch stops at the first error without rollback. A headless session starts with no presentation open (inspect_document returns "no presentation open"); call new_presentation or open_presentation first. open_presentation returns damagedMedia and, since 0.9.0, lostSlides (a .pptx slide that could not be read is left out and the title gets "(Repaired)"): check both before saving a copy. comment.delete without index removes every comment on the current slide (all: true on every slide); since 0.9.0 an index that is not a non-negative integer is refused. Since 0.12.0 an `ids` entry or a slide, table row/column, animation or layout index that is negative or fractional is refused instead of acting on the selection (an empty `ids` still means the selection). shape.move, shape.resize and shape.setBounds clamp sizes to 0..15840 pt and positions to ±100000 pt (0.9.0). Since 0.11.1 design.browseTheme with a .pptx or .potx replaces the current slide's master and layouts and moves its slides to matching layouts (a .thmx changes only the theme). Save a separate editable native deck and requested interchange export when required.

## Durable verification

Reopen PPTX/native output, check slide count/content and render every slide. Review text overflow, charts, fonts, notes/handouts and warnings. Since 0.12.0 a PDF keeps only http, https, mailto and slide-to-slide links; other link text stays unlinked. A ZIP/XML check does not establish PowerPoint fidelity.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-29 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/deckcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
