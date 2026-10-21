# FigCraft

## Choose this app

Interface design, components and prototypes. Native server key: `figcraft`. Plugin-provided
or host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `figcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`figcraft-cli-<version>-macos-universal.zip` release asset. The Windows portable ZIP ships
`figcraft-cli.exe` next to the app, the Linux tarball ships `bin/figcraft-cli`, and the
Linux AppImage runs the same CLI as `FigCraft.AppImage cli <args>`; `setup` uses the
tarball. The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots (since 0.7.0 for mcp; since 0.8.0 the CLI's info, export, convert, render and run take the same flags, which the catalog does not use); still test the pinned binary and OS boundary.

## Discover before execution

Discover document and layer inspection, node creation and property edits, the command registry, selection, save, export and screenshots. Every menu action is a command: run one with run_command (list_commands shows id, params and whether it is undoable); commands act on `ids` when given, otherwise on the selection, and new layers become the selection. Tools include list_commands, run_command, batch, create_node, set_properties, inspect_document, get_node, select, export, screenshot, open_file, save_file, undo, redo, pointer, key, type_text and inspect_ui; the same tools serve the headless session and, only with --attach, a running desktop app.

## Workflow and risky operations

Bare `mcp` is headless: an in-process session with one untitled document, no window and no plugins (import them first). Never add `--attach` (a loopback control port into the running app) to repair an error; attached calls are never replayed after a transport failure because the app may already have applied them. Coordinates are page units, y down; create_node and set_properties take x/y relative to the parent frame, and children of auto-layout frames are placed by the layout (set layout, gap, padding, alignment and sizing instead of x/y). Each mutation is one undo step, a failing command leaves the document unchanged, and batch is one undo step without rollback of preferences or clipboard; since 0.7.0 a batch step can use an earlier step's result through `{"$step": n}` (zero-based), so `$step` is a reserved key in step params. Edits inside an instance are refused (edit the main component or resize the instance); sections live only on the page or in sections; headless text is black on a #F5F5F5 page. A `.fig` input is opened best effort and never saved over. `--no-system-fonts` (or FIGCRAFT_NO_SYSTEM_FONTS=1) restricts text to the built-in fonts; it is not in the catalog, so text lays out with the machine's fonts like the desktop app. A request line above 32 MiB closes the session with JSON-RPC -32600. The catalog launches `mcp` with `--automation-read-root` (the workspace) and `--automation-write-root` (outputs/): every file a call reads must lie inside a read or write root and every file it writes inside the write root (open_file, save_file, export with a path, imports, library, variable and plugin files); a refused path is an ordinary tool error (automation path rejected), and export without a path still returns the image. Both folders must exist at launch and `--attach` with them is an error. Not confined: the app's own preference, recovery, plug-in and font folders. Since 0.8.0 a refused path whose existing part resolves into a root carries the OS reason (automation path rejected: <path>: <why>), and a link that leads out of a root is outside. text.loadFont {path | data} adds a font file through the same check, text.rescanFonts picks up fonts installed since launch, and text.missingFonts lists the families the document names that are not installed (their text draws in a fallback font; text.refit refits auto-sized text). An effect object given to set_properties, node.set or effect.set with a key the effect does not read is refused naming the keys it takes; an explicit edit of a variable-bound field (node.set, transform.resize, text.set, a canvas drag) detaches that field's variable while untouched fields stay bound. create_node {type: vector, path} and vector.create scale the path to width/height (one alone keeps the proportion) and refuse a path that draws nothing or a size of 0.

## Durable verification

save_file writes the editable `.figcraft`; export writes png, jpg, svg, webp or pdf (one PDF page per top-level frame) only when `path` is set, otherwise the image comes back inline, and the `fig` format is experimental (round trips are tested through FigCraft's own importer; only the example documents and small test files were opened in other software); save_file to a `.fig` path writes such a copy and leaves the document's path and unsaved changes alone. set_properties lists in `warnings` the layers it skipped (auto layout keys apply only to frames, components and instances) and a fontStyle drawn in the nearest face of another weight or slant. get_node and inspect_document report pluginData ({key: value}, strings) when a layer or page carries layer data written through set_properties {props: {pluginData}}. Reopen the output and compare frame count, bounds (inspect_document adds absoluteBounds in page coordinates), text, fonts and the colour profile: Display P3 documents convert to sRGB on SVG and PDF export and out-of-gamut colours clip. Verify numbers with inspect_document or get_node and pixels with screenshot or the exported image; a successful tool call is not a durable save.

## Evidence and maintenance

Basis: upstream FigCraft source (CLI parser, MCP documentation, MCP tool definitions,
packaging and release assets), rechecked on 2026-10-21. FigCraft postdates the supplied
Native MCP Project Plan and CLI/MCP Integration Reference, which enumerate twelve apps;
it is integrated the same way. This card is source-grounded guidance, not a
runtime-tested capability contract. Upstream:
[MCP documentation](https://github.com/storytold/figcraft/blob/main/docs/mcp.md),
[CLI documentation](https://github.com/storytold/figcraft/blob/main/docs/cli.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
