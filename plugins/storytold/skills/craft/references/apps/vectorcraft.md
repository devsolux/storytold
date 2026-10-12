# VectorCraft

## Choose this app

Vector illustrations and artboards. Native server key: `vectorcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `vectorcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots; still test the pinned binary and OS boundary.

## Discover before execution

Use runtime discovery for document inspection, paths/shapes, paint, native save and export. Artboard indices/range syntax differ across tools, so read each schema.

## Workflow and risky operations

Force --headless. Bare mcp may try a running desktop application first. Never remove that flag or add --connect to repair an error. Read/write roots are independent. Grouped undo is not a multi-file transaction.

## Durable verification

Check artboard count, coordinates, paths, fonts and import/export warnings. Reopen SVG/PDF/native output as appropriate and inspect the rendered result. Synchronous native operations may not support active cancellation.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/vectorcraft/blob/main/apps/vectorcraft-cli/src/main.rs).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
