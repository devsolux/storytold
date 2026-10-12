# CADCraft

## Choose this app

Drawing entities, units and geometry. Native server key: `cadcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `cadcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`cadcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/cadcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover drawing inspection, paginated entity queries, units, native commands, save and rendering. Native command_line is the CAD prompt, not an OS shell. Tools at 0.5.0: command_line, script, execute, list_commands, inspect_drawing, query_entities, render, new_drawing, open (DXF), save (DXF or DWG by extension) and cancel.

## Workflow and risky operations

Use explicit drawing units and coordinate conventions. Bound entity pagination instead of dumping a whole drawing: inspect_drawing includes up to 200 entities unless entities is false, so page with query_entities offset/limit. inspect_drawing has no units field; read INSUNITS with execute getvar. No native file-root flag is established. Do not use --connect or silently switch backends.

## Durable verification

Compare known geometry, dimensions, entity counts and model-space units after reopening. View/window framing affects rendered outputs, not necessarily saved geometry. SVG/PNG/PDF export may leave the editable drawing unsaved.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-12 against the v0.5.0 release
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation at v0.5.0](https://github.com/storytold/cadcraft/blob/v0.5.0/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
