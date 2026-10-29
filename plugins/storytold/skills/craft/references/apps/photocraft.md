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
Since 0.16 a repeated launch option or a stray argument is a usage error (exit 2), and a
non-empty `PHOTOCRAFT_CONTROL_PORT` inherited by the server switches `mcp` to the desktop
bridge, which next to the root flags stops the launch (exit 2): unset it or leave it empty.

## Discover before execution

Discover document inspection, registry search and save/export tools. Tools include doc_inspect, doc_new, doc_open, doc_place, doc_replace_smart_object, doc_save, doc_export, doc_export_layers, doc_export_data_sets, doc_import_data_sets, doc_render_preview/render_preview, command_list, command_run and command_batch; ui_* and control_call return a bridge-only error headless. doc_inspect reports hasMask, hasVectorMask and vectorMaskEnabled per layer, an adjustment {kind, params} on adjustment layers and, since 0.12, historySource (the History Brush source: a state row or a snapshot, null when unset). doc_save and doc_export take dpxBits (8, 10, 12 or 16) for DPX and, since 0.12, ddsCompression (none, bc1, bc2 or bc3; DXT1/3/5 spellings accepted) and ddsMipmaps for DDS, which is now writable; a quality outside 1..100 is refused instead of clamped. An index on doc_place, doc_export_layers, doc_export_data_sets or doc_import_data_sets targets that one call and no longer leaves that document active (since 0.12). Since 0.16 doc_replace_smart_object replaces a Smart Object's contents (layer: id or name, default the active layer; index headless only) with a read-root file, keeping its transform and filters, and doc_export_layers also returns skipped (hidden layers under visible_only, adjustments without pixels). .kra and .krz open import-only; a GIF opens in Indexed Color with its colour table, so a PNG export of it is an 8-bit palette PNG (warned). Resolve the actual tool names and schemas, never guess a command id.

## Workflow and risky operations

Inspect layer tree, dimensions, masks and colour mode/depth (doc_inspect has no ICC profile field); keep open/save warnings, including missing fonts. Work on a copy: image.duplicate or history.newDocument creates a new active document and leaves the source unchanged; image.duplicate with mergedOnly: true and image.trim refuse a document over 2^30 pixels as too large to flatten (since 0.12). command_run refuses every file.* command except file.new, file.newFromClipboard, the file.close commands, file.fileInfo, file.export.exportPreferences and a few in-document file.automate/file.scripts helpers ("uses ambient filesystem paths"), so file.open, file.saveACopy and file.automate.batch are desktop-only: open, save and export with doc_open, doc_save and doc_export, which stay inside the roots. Since 0.17 doc_save and doc_export replace an existing write-root file only when it is a regular file of a format PhotoCraft writes (by extension or image header); anything else is refused, so save to a new name. While confined, a path on layer.layerStyle.contours.load/save (new in 0.13) or style.presets.importAsl/exportAsl (0.16) is refused (pass or take base64 data), and so is file.new with a profile path or a working-space alias other than working (0.13); since 0.14 a PSD/PSB or layered TIFF save writes a Linked smart object as pixels instead of embedding its file. command_batch stops at the first error by default (stop_on_error) and never rolls back: completed and the per-step results list what applied; recover with edit.undo once per history entry while inspecting history, and undo does not roll back files written to disk. Since 0.12 history.stepBackward, history.stepForward and history.clear (undoable; refused while a job runs) move along or prune the history, history.setSource picks the History Brush source by state row or snapshot, and brush.mixer.load/brush.mixer.clean are new; edit.fill with contents: history takes a History panel row as state (redo rows last) or a snapshot and defaults to that source, no longer the oldest state. Since 0.17 history.options sets allowNonLinearHistory (default off: an edit after stepping back drops the later states) and makeLayerVisibilityChangesUndoable (default on). Save the editable project separately from the delivery raster.

## Durable verification

Confirm pixel dimensions, layers where relevant, colour/profile expectations and visual appearance after reopening. PSD/interchange need not retain every native feature. A successful tool call is not a durable save: a flat PNG/JPEG/DPX/DDS export (a block-compressed DDS is lossy and BC1 keeps alpha only on or off) leaves the document unsaved; only a PSD, PSB or .pcraft save marks it saved. An ORA save counts only when OpenRaster loses nothing: with masks, styles, adjustment, text, shape or smart layers, clipping, alpha channels, metadata or a non-sRGB profile it writes a copy, the document stays unsaved and a path-less doc_save refuses.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-29 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/photocraft/blob/main/docs/mcp.md).
The binary has passed discovery and a read-only smoke call; see
[verification](../../../../docs/verification.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
