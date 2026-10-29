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

Use runtime discovery for document inspection, paths/shapes, paint, native save and export. Artboard indices/range syntax differ across tools (export artboard is 0-based, range is 1-based), so read each schema. Tools include doc_inspect/inspect_document, draw_path, draw_shape, set_paint, open_file, save_file and export; UI tools (answer_dialog too, 0.18.0) need a desktop connection and error headless. On a large document scope doc_inspect/inspect_document with depth, childLimit, ids, kind and limit/offset (the reply adds total). command_run and each batch step refuse an unknown top-level parameter key before running, naming the nearest key, so a misspelt key never runs the command with its default (an unknown command id names the nearest id, 0.18.0); the keys inside nested objects are the command's to read. list_commands/command_list take query, menu and brief (the catalogue is large). draw_path and draw_shape take dash, cap, join, opacity, name and effects; add_text takes vertical. Since 0.15.0 a draw_path or draw_shape call is one undo step, and a paint the engine refuses leaves the document unchanged. doc_inspect reports opacity as a 0–1 fraction and opacityPct in the 0–100 % the drawing tools take: pass opacityPct back (0.18.0). set_paint answers objects, the count painted; 0 means only the default for new art changed (0.18.0). save_file takes compress, version, preview and options (0.17.0). export adds ai (PDF-compatible, all artboards; options.aiVersion "7" writes legacy .ai, one file per artboard). export's scale (pixels per point) applies to raster formats only (since 0.14.0; before, it also resized a DXF); DXF takes its own scale in options. Since 0.17.0 an EPS export with artboard, range, artboards or useArtboards writes one file per artboard and, for two or more, first a central {stem}.eps of the visible art (none when no art shows). A .ait path or format "ait" is refused by export (document.export, serialize, exportSelection, exportForScreens) with an error naming file.saveAsTemplate, which writes it with every artboard and refuses aiVersion "7". open_file also reads Targa (.tga, .vda, .icb, .vst).

## Workflow and risky operations

Force --headless. Bare mcp may try a running desktop application first. Never remove that flag or add --connect to repair an error. Read/write roots are independent; since 0.15.0 each flag may be repeated, a path inside any root of its kind passing. Each command_batch step is its own undo step unless atomic: true makes the batch one undo step (since 0.17.0 also in each document a step opens or creates); a failing step stops the batch (stop_on_error, default true) and the steps that ran stay applied: the command_batch tool never rolls back. Only the engine command command.batch (through command_run) puts the documents back on failure, and neither undoes the disk (files a step saved or exported stay written), so put saves and exports last. edit.clearHistory (through command_run) removes every undo and redo step. A linked file a document names is followed only on this computer or on the document's own network share (on Windows also the share behind the document's mapped drive, 0.14.0; a link on a drive mapped to another share counts as missing, 0.15.0); another computer, a device or a URL counts as missing, and document.open lists it in missingLinks with refused. A step may also be draw_path or draw_shape with that tool's arguments as params; the reply lists the created ids. A batch holds at most 256 steps and 8 MiB of kept results, and one request line at most 16 MiB. Calls run one at a time: once one has run 2 s, any other request that needs the engine is refused with error -32003 (busy) and was not run, so retry it; ping, tools/list and the other list methods, and prompts/get are still answered. Both roots must exist before launch, and the app's own preference and font folders are outside them, so a confined server keeps no PDF presets, ICC profiles or plug-ins between runs. A plug-in filter whose plugin.inspect budget is heavy installs only with plugin.install allowHeavy: true, so ask the user first; its plugin.run may take minutes (0.17.0).

## Durable verification

Check artboard count, coordinates, paths, fonts and import/export warnings. Reopen SVG/PDF/native output as appropriate and inspect the rendered result. render_preview and screenshot draw what a PNG export on white draws (0.17.0), and Image Trace objects as their result unless traceViews: true (0.18.0). notifications/cancelled drops a queued call or stops a running export, flatten, bake, render or plug-in run at its next checkpoint, writing nothing; any other call runs to its end. A cancelled request gets no reply, so inspect the document afterwards. Text that does not fit its frame or path is drawn only up to the last fitting line: add_text answers overflow: true and text.create, text.setText and text.setStyle answer overflow with the ids, so fix the frame or the fit before exporting. An image whose pixel data cannot be decoded is not drawn; one past the 2 GiB decode allowance draws at reduced size (0.18.0) unless it cannot be read that way, and then is not drawn either (links.list note, open and place warnings). A raster, PDF, EPS, DXF or EMF/WMF export, .ai save or file.print leaves an undrawn image out and warns once. PNG, PDF, EPS, .ai, zip and .vectorcraft output records the time of writing, so two runs differ in bytes: set SOURCE_DATE_EPOCH (whole seconds) in the server's environment for byte-identical re-exports (0.14.0); a password-protected PDF still differs. An older native file opens as [Converted], and document.save without a path then answers with a suggested name instead of writing.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-29 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/vectorcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
