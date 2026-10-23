# PhotoCraft

## Choose this app

Raster images, layers, masks and PSD. Native server key: `photocraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `photocraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`photocraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/photocraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots; still test the pinned binary and OS boundary.

## Discover before execution

Discover document inspection, registry search and save/export tools. Tools include doc_inspect, doc_new, doc_open, doc_place, doc_save, doc_export, doc_export_layers, doc_export_data_sets, doc_import_data_sets, doc_render_preview/render_preview, command_list, command_run and command_batch; ui_* and control_call return a bridge-only error headless. doc_inspect reports hasMask, hasVectorMask and vectorMaskEnabled per layer, an adjustment {kind, params} on adjustment layers and, since 0.12, historySource (the History Brush source: a state row or a snapshot, null when unset). doc_save and doc_export take dpxBits (8, 10, 12 or 16) for DPX and, since 0.12, ddsCompression (none, bc1, bc2 or bc3; DXT1/3/5 spellings accepted) and ddsMipmaps for DDS, which is now writable; a quality outside 1..100 is refused instead of clamped. An index on doc_place, doc_export_layers, doc_export_data_sets or doc_import_data_sets targets that one call and no longer leaves that document active (since 0.12). .kra and .krz open import-only; a GIF opens in Indexed Color with its colour table, so a PNG export of it is an 8-bit palette PNG (warned). Resolve the actual tool names and schemas, never guess a command id.

## Workflow and risky operations

Inspect layer tree, dimensions, masks and colour mode/depth (doc_inspect has no ICC profile field); keep open/save warnings, including missing fonts. Work on a copy: image.duplicate or history.newDocument creates a new active document and leaves the source unchanged; image.duplicate with mergedOnly: true and image.trim refuse a document over 2^30 pixels as too large to flatten (since 0.12). file.saveACopy refuses a path that is the document's own file unless overwrite: true (since 0.11); a copy over the original in a flat or lossy format cannot be undone, so give it another path. command_batch stops at the first error by default (stop_on_error) and never rolls back: completed and the per-step results list what applied; recover with edit.undo once per history entry while inspecting history, and undo does not roll back files written to disk. Since 0.12 history.stepBackward, history.stepForward and history.clear (undoable; refused while a job runs) move along or prune the history, history.setSource picks the History Brush source by state row or snapshot, and brush.mixer.load/brush.mixer.clean are new; edit.fill with contents: history takes a History panel row as state (redo rows last) or a snapshot and defaults to that source, no longer the oldest state. file.automate.batch with format "same" saves camera raws and import-only inputs (.kra, .krz, .heic, .svg, .cin, .pcx, .xpm, .pdn, Affinity) as PSD and an extension-less input as PNG. Save the editable project separately from the delivery raster.

## Durable verification

Confirm pixel dimensions, layers where relevant, colour/profile expectations and visual appearance after reopening. PSD/interchange need not retain every native feature. A successful tool call is not a durable save: a flat PNG/JPEG/DPX/DDS export (a block-compressed DDS is lossy and BC1 keeps alpha only on or off) leaves the document unsaved; only a PSD, PSB or .pcraft save marks it saved. An ORA save counts only when OpenRaster loses nothing: with masks, styles, adjustment, text, shape or smart layers, clipping, alpha channels, metadata or a non-sRGB profile it writes a copy, the document stays unsaved and a path-less doc_save refuses.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-23 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/photocraft/blob/main/docs/mcp.md).
The binary has passed discovery and a read-only smoke call; see
[verification](../../../../docs/verification.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
