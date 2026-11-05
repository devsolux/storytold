# MaterialCraft

## Choose this app

Procedural PBR materials as node graphs: tileable base color, normal, roughness, metallic,
height and ambient-occlusion maps built from noises, patterns and filters. Native server key:
`materialcraft`. Plugin-provided or host-specific namespacing may change the callable tool
prefix; discover it.

## Launch and scope

Native executable: `materialcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`materialcraft-cli-<version>-macos-universal.zip` release asset. The Windows MSI and portable
ZIP and the Linux `.deb`, `.rpm` and tarball carry the CLI next to the app. The source-derived
launch arguments live in the single reviewed [app catalog](../../../../config/apps.json), not
in a copied engine registry.

The catalog launches `mcp` with `--read-root` (the workspace) and `--write-root` (outputs/).
MaterialCraft has only these spellings: it refuses `--automation-read-root`. Both folders must
exist at launch, and a root left out denies that kind of access. The roots are held directory
handles, so a request path is relative to its root in forward slashes: `inputs/wall.sbs` to
read, `wall.mcraft` to write. Absolute paths, `..`, drive prefixes and symlink or junction
escapes are refused. Reads take regular files up to 256 MiB; a write goes to a temporary file
beside the target and renames over it, so it replaces an existing file. Never add `--bridge` or
`--token`: they drive a running desktop app.

## Discover before execution

Discover the node library and the session before editing. Tools include session_inspect,
command_list, command_run, command_batch, library_list, graph_new, node_add, node_connect,
node_param, package_open, package_save, bitmap_import, outputs_export and view_render.
view_screenshot and the `ui_*` tools answer only over a bridge and do nothing here. Every
action is an engine command behind command_list.

## Workflow and risky operations

Start with graph_new (templates such as pbr, bricks, wood) or package_open, browse with
library_list, build with node_add, node_connect and node_param, and undo with `command_run
edit.undo`. command_batch stops at the first error, at most 256 steps. command_run refuses every
`file.*` command except `file.new` and `file.newPackage`, and any command given `path` or `dir`,
so a `.mcmat` portable material cannot be written from here: that export runs only in the CLI
and the desktop app. package_save writes SBS unless the path ends in `.mcraft`, and appends `.sbs`
without a package extension. Always give it a path: without one it reuses the path the package
was opened from, now relative to the write root. outputs_export creates its folder and cooks at
full size, which can take a while on a large graph.

## Durable verification

package_open reports what an SBS file holds that MaterialCraft cannot read in `package.warnings`,
and keeps missing nodes as placeholders: surface those, and do not call an imported package
faithful because it reopened. Check the saved package by reopening it and comparing
session_inspect (graphs, nodes, cook errors, exposed inputs); check each map outputs_export
returned for size, format and bit depth; look at view_render (3D, or 2D for one node), which is
CPU rendered, at most 2048 px a side and 5 MiB. JSON replies stop at 8 MiB, and a refused oversized
reply may follow a completed operation.

## Evidence and maintenance

Basis: upstream MaterialCraft source (CLI parser, control-protocol documentation, MCP tool
definitions, workspace confinement, packaging and release assets), reviewed on 2026-11-05 at
v0.1.2. MaterialCraft postdates the supplied Native MCP Project Plan and CLI/MCP Integration
Reference; it is integrated the same way. This card is source-grounded guidance, not a
runtime-tested capability contract. Upstream:
[control protocol and MCP](https://github.com/storytold/materialcraft/blob/main/docs/control-protocol.md),
[known gaps](https://github.com/storytold/materialcraft/blob/main/docs/gaps.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
