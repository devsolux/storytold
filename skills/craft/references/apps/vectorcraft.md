# VectorCraft

## Choose this app

Vector illustrations and artboards. Native server key: `vectorcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `vectorcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`vectorcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/vectorcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots; still test the pinned binary and OS boundary.

## Discover before execution

Use runtime discovery for document inspection, paths/shapes, paint, native save and export. Artboard indices/range syntax differ across tools (export artboard is 0-based, range is 1-based), so read each schema. Tools include doc_inspect/inspect_document, draw_path, draw_shape, set_paint, open_file, save_file and export; UI tools need a desktop connection and error headless. command_run and each batch step refuse an unknown top-level parameter key before running, naming the nearest key, so a misspelt key never runs the command with its default; the keys inside nested objects are the command's to read.

## Workflow and risky operations

Force --headless. Bare mcp may try a running desktop application first. Never remove that flag or add --connect to repair an error. Read/write roots are independent. Each command_batch step is its own undo step unless atomic: true makes the batch one undo step; a failing atomic batch puts the documents back but never the disk (files a step saved or exported stay written), so put saves and exports last. A batch holds at most 256 steps and 8 MiB of kept results, and one request line at most 16 MiB. Both roots must exist before launch, and the app's own preference and font folders are outside them.

## Durable verification

Check artboard count, coordinates, paths, fonts and import/export warnings. Reopen SVG/PDF/native output as appropriate and inspect the rendered result. Synchronous native operations may not support active cancellation. Text that does not fit its frame or path is drawn only up to the last fitting line: add_text answers overflow: true and text.create, text.setText and text.setStyle answer overflow with the ids, so fix the frame or the fit before exporting. An image too large to decode is not drawn (links.list note, open and place warnings). An older native file opens as [Converted], and document.save without a path then answers with a suggested name instead of writing.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-14 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/vectorcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
