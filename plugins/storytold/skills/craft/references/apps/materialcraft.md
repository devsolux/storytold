# MaterialCraft

## Choose this app

Procedural PBR materials as node graphs saved as native SBS: base color, normal, roughness,
metallic, height and ambient-occlusion maps built from atomic primitives (uniform, blend, levels,
warp, gradient map, pixel and value processors, FX-Maps, …), function graphs and the bundled SBS
function library. The older noise, pattern and filter library was removed in 0.2.0. Native server
key: `materialcraft`. Plugin-provided or host-specific namespacing may change the callable tool
prefix; discover it.

## Launch and scope

Native executable: `materialcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`materialcraft-cli-<version>-macos-universal.zip` release asset. The Windows MSI and portable
ZIP and the Linux `.deb`, `.rpm` and tarball carry the CLI next to the app. The source-derived
launch arguments live in the single reviewed [app catalog](../../../../config/apps.json), not
in a copied engine registry.

The catalog launches `mcp` with `--read-root` (the workspace) and `--write-root` (outputs/).
Since 0.2.0 `--automation-read-root` and `--automation-write-root` are aliases of them (the
last root given wins). Both folders must exist at launch, and a root left out denies that kind
of access. The roots are held directory handles, so a request path is relative to its root in
forward slashes: `inputs/wall.sbs` to read, `wall.sbs` to write. Absolute paths, `..`, drive
prefixes and symlink or junction escapes are refused. Reads have no size cap since 0.3.0. A
write goes to a temporary file beside the target and renames over it, so it replaces an
existing file (package resources excepted, below). Never add `--bridge` or `--token`: they
drive a running desktop app.

Not confined: package_open also loads every other `.sbs` package the opened one instances (its
SBS dependency file names) with plain reads of the user's files, absolute or resolved against
the server's working directory, not the read root; one it cannot read only adds a `Could not
resolve` warning. Open only packages whose dependencies you trust. `sbs://` library references
read `MATERIALCRAFT_SBS_DIR`, else an `assets/sbs` folder beside the binary, else the bundled
`functions.sbs`; treat a set `MATERIALCRAFT_SBS_DIR` as a finding.

## Discover before execution

Discover the node library and the session before editing. Tools include session_inspect,
command_list, command_run, command_batch, library_list, graph_new, node_add, node_connect,
node_param, package_open, package_save, bitmap_import, outputs_export, material_export and
view_render. view_screenshot and the `ui_*` tools answer only over a bridge and do nothing here.
Every action is an engine command behind command_list; many Library categories (texture
generators, filters, PBR materials) are still empty.

## Workflow and risky operations

Start with graph_new (templates empty, pbr, atomics) or package_open, browse with library_list,
build with node_add, node_connect and node_param, and undo with `command_run edit.undo`.
package_open adds a package beside those already open (session_inspect `documents`, at most 64)
and switches to one whose path is already open instead of rereading it. command_batch stops at
the first error, at most 256 steps. command_run refuses every `file.*` command except `file.new`,
`file.newPackage` and `file.newAtomicSample`, and any command given `path` or `dir`. package_save
writes `.sbs` XML with its resources as new files in an adjacent `resources/` folder (a different
file of the same name there is refused), or a self-contained `.mcraft` ZIP (`package.sbs` and
`resources/`) when the path ends in `.mcraft`, and appends `.sbs` without a package extension; a
0.1.x `.mcraft` (`package.json`) no longer opens. Always give it a path: without one it reuses
the path the package was opened from, now relative to the write root. outputs_export creates its
folder and cooks at the graph's size unless given `size`, which can take a while on a large graph;
`outputs` and `colorSpaces` choose the maps and their encoding. material_export writes a version 2
`.mcmat` (cooked maps and `source.sbs`; `.mcmat` appended, the parent folder must exist, at most
256 MiB), which TextureCraft v0.6.1 refuses: hand it exported maps instead (see its card).

## Durable verification

package_open reports what an SBS file holds that MaterialCraft cannot read in `package.warnings`,
and keeps missing nodes as placeholders: surface those, and do not call an imported package
faithful because it reopened (upstream has not verified reopening in the reference application
or numerical parity with it). Check the saved package by reopening it from the read root
(`outputs/wall.sbs`) and comparing session_inspect (graphs, nodes, cook errors, exposed inputs);
check each map outputs_export returned for size, format and bit depth; look at view_render (3D,
or 2D for one node), which is CPU rendered, at most 2048 px a side and 5 MiB, and in 3D raises
the surface by the height output even without `hq`. JSON replies stop at 8 MiB, and a refused
oversized reply may follow a completed operation.

## Evidence and maintenance

Basis: upstream MaterialCraft source (CLI parser, control-protocol documentation, MCP tool
definitions, workspace confinement, packaging and release assets), rechecked on 2026-11-13 at
v0.4.1. MaterialCraft postdates the supplied Native MCP Project Plan and CLI/MCP Integration
Reference; it is integrated the same way. This card is source-grounded guidance, not a
runtime-tested capability contract. Upstream:
[control protocol and MCP](https://github.com/storytold/materialcraft/blob/main/docs/control-protocol.md),
[primitive workflow and limits](https://github.com/storytold/materialcraft/blob/main/docs/atomic-workflow.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
