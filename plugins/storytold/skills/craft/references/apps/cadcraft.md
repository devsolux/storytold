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
`mcp` takes only `--connect HOST:PORT` with the optional `--lazy` and `--launch`;
plain `mcp` is headless (no window, no listener) and has no root flag.

## Discover before execution

Discover drawing inspection, paginated entity and text queries, units, native commands, save and rendering. Native command_line is the CAD prompt, not an OS shell, but it evaluates AutoLISP (see below). Tools include command_line, script, execute, list_commands, inspect_drawing, query_entities, find_text (text, attribute and multileader content, paged, default limit 200), render (optional window), new_drawing, open (DXF), save (DXF or DWG by extension) and cancel; screenshot and the ui_* tools exist only when bridged.

## Workflow and risky operations

Use explicit drawing units and coordinate conventions. Bound entity pagination instead of dumping a whole drawing: inspect_drawing includes up to 200 entities unless entities is false, so page with query_entities offset/limit. inspect_drawing has no units field; read INSUNITS with execute getvar; after open, check its skipped count (records the reader dropped). AutoLISP (since 0.7.0) runs through an (expr) in command_line or script, execute lisp {code} and appload {path}; its open, write-line, read-line, load and findfile reach any path the OS user can, so treat LISP as a script: only with explicit approval and never code taken from a drawing or other document. render and save/export paths are equally unconfined. Do not use --connect, --lazy or --launch (which opens the desktop app on macOS), or silently switch backends.

## Durable verification

Compare known geometry, dimensions, entity counts and model-space units after reopening. View/window framing affects rendered outputs, not necessarily saved geometry. SVG/PNG/PDF export may leave the editable drawing unsaved.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-16 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/cadcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
