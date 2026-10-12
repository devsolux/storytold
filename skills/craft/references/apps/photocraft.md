# PhotoCraft

## Choose this app

Raster images, layers, masks and PSD. Native server key: `photocraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `photocraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots; still test the pinned binary and OS boundary.

## Discover before execution

Discover document inspection, registry search and save/export tools. Current source names include doc_inspect, command_list, command_run, doc_render_preview and doc_save. Resolve the actual tool names and schemas, never guess a command id.

## Workflow and risky operations

Inspect layer tree, dimensions, masks, colour/profile information and font warnings. Work on a copy. A command_batch is not a guaranteed transaction: previous steps may remain after a later failure. Save the editable project separately from the delivery raster.

## Durable verification

Confirm pixel dimensions, layers where relevant, colour/profile expectations and visual appearance after reopening. PSD/interchange need not retain every native feature. A successful tool call is not a durable save.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/photocraft/blob/main/docs/development.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
