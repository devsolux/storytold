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

Discover document inspection, registry search and save/export tools. Tools include doc_inspect, doc_new, doc_open, doc_place, doc_save, doc_export, doc_export_layers, doc_export_data_sets, doc_import_data_sets, doc_render_preview/render_preview, command_list, command_run and command_batch; ui_* and control_call return a bridge-only error headless. doc_inspect reports hasMask, hasVectorMask and vectorMaskEnabled per layer. Resolve the actual tool names and schemas, never guess a command id.

## Workflow and risky operations

Inspect layer tree, dimensions, masks and colour mode/depth (doc_inspect has no ICC profile field); keep open/save warnings, including missing fonts. Work on a copy: image.duplicate or history.newDocument creates a new active document and leaves the source unchanged. command_batch stops at the first error by default (stop_on_error) and never rolls back: completed and the per-step results list what applied; recover with edit.undo once per history entry while inspecting history, and undo does not roll back files written to disk. Save the editable project separately from the delivery raster.

## Durable verification

Confirm pixel dimensions, layers where relevant, colour/profile expectations and visual appearance after reopening. PSD/interchange need not retain every native feature. A successful tool call is not a durable save: a flat PNG/JPEG export leaves the document unsaved; only a PSD, PSB, ORA or .pcraft save marks it saved.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-14 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/photocraft/blob/main/docs/mcp.md).
The binary has passed discovery and a read-only smoke call; see
[verification](../../../../docs/verification.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
