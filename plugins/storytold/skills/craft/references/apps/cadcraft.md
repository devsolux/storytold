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
`mcp` takes `--connect HOST:PORT` with the optional `--lazy` and `--launch` and, since
0.14.0, `--config-dir DIR`, `--fontalt FONT` and `--fontfallback FONTS` (fallbacks
`CADCRAFT_CONFIG_DIR`, `CADCRAFT_FONTALT`, `CADCRAFT_FONTFALLBACK`; the settings folder holds
plotter configurations, an empty one means none); anything else is a usage error (exit 2).
Plain `mcp` is headless (no window, no listener) and has no root flag; `--config-dir` is not one.

## Discover before execution

Discover drawing inspection, paginated entity and text queries, units, native commands, save and rendering. Native command_line is the CAD prompt, not an OS shell, but it evaluates AutoLISP (see below). Tools include command_line, script, execute, list_commands, inspect_drawing, query_entities, find_text (text, attribute and multileader content, paged, default limit 200), render (optional window), new_drawing, open (described as DXF or DWG since 0.13.0, but the reader also takes SVG/SVGZ; an imported SVG leaves the drawing without a file name, and the result's warnings list what reading left out), save (DXF or DWG by extension) and cancel; screenshot and the ui_* tools exist only when bridged. Since 0.10.0 query_entities takes selected: true (the current selection in the active space, combined with type, layer and window before paging) and execute shapes reports closed-shape facts (perimeter, area, centroid, winding, self-intersections). Since 0.13.0 execute also runs usage (read-only use of layers, blocks, text styles and linetypes; past 5,000,000 objects incomplete: true) and loops (implied closed loops from loose LINE and ARC chains; pairing stops at maxPairs, default 1,000,000, as capped), shapes adds selfCheck (found, analysed, skipped, caps, implausible values), compareexport opens the comparison as a new untitled drawing, and appload returns the commands the file defined and refuses a path that is not .lsp.

## Workflow and risky operations

Use explicit drawing units and coordinate conventions. Bound entity pagination instead of dumping a whole drawing: inspect_drawing includes up to 200 entities unless entities is false, so page with query_entities offset/limit. inspect_drawing has no units field; read INSUNITS with execute getvar; after open, check its skipped count (records the reader dropped). AutoLISP (since 0.7.0) runs through an (expr) in command_line or script, execute lisp {code} and appload {path}; its open, write-line, read-line, load and findfile reach any path the OS user can, so treat LISP as a script: only with explicit approval and never code taken from a drawing or other document. render and save/export paths are equally unconfined, and with the system variable AUDITCTL set to 1 (default 0, since 0.10.0) audit and recover also write a <drawing>.adt log beside a drawing that has a path. Since 0.14.0 execute layout.saveas {name?, path} (LAYOUT SAveas) writes a layout as a template (.dwt, .dwg or .dxf; no extension adds .dwt, another is refused), replacing an existing file. Since 0.12.0 open, script and the LISP open, load and appload reads take regular files only, up to 512 MiB for a drawing and 64 MiB otherwise. open also loads the drawing's attached xrefs: since 0.8.0 a path stored in a drawing (xref, table data link) resolves beside it and is followed only on this computer or the drawing's own network share (otherwise the xref stays Unresolved, "not opened"); paths given to XATTACH, -XREF Path or DATALINK are used as given. Do not use --connect, --lazy or --launch (which opens the desktop app on macOS), or silently switch backends.

## Durable verification

Compare known geometry, dimensions, entity counts and model-space units after reopening. View/window framing affects rendered outputs, not necessarily saved geometry. SVG/PNG/PDF export may leave the editable drawing unsaved.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-29 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/cadcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
