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

Discover document inspection, registry search and save/export tools. The 0.7.0 binary lists doc_inspect, doc_new, doc_open, doc_save, doc_export, doc_render_preview/render_preview, command_list, command_run and command_batch; ui_* and control_call return a bridge-only error headless. Resolve the actual tool names and schemas, never guess a command id.

## Workflow and risky operations

Inspect layer tree, dimensions, masks and colour mode/depth (doc_inspect has no ICC profile field); keep open/save warnings, including missing fonts. Work on a copy. A command_batch is not a guaranteed transaction: previous steps may remain after a later failure. Save the editable project separately from the delivery raster.

## Durable verification

Confirm pixel dimensions, layers where relevant, colour/profile expectations and visual appearance after reopening. PSD/interchange need not retain every native feature. A successful tool call is not a durable save: a flat PNG/JPEG export leaves the document unsaved; only a PSD, PSB, ORA or .pcraft save marks it saved.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-12 against the v0.7.0 release
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP conventions at v0.7.0](https://github.com/storytold/photocraft/blob/v0.7.0/docs/mcp.md).
The 0.7.0 binary has passed discovery and a read-only smoke call; see
[verification](../../../../docs/verification.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
