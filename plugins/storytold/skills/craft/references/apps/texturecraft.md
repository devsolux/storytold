# TextureCraft

## Choose this app

3D texture painting: PBR layers and masks on a mesh, baked mesh maps, smart materials, and
texture export for an engine. Native server key: `texturecraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `texturecraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`texturecraft-cli-<version>-macos-universal.zip` release asset. The Windows MSI and portable
ZIP and the Linux `.deb`, `.rpm` and tarball carry the CLI next to the app. The source-derived
launch arguments live in the single reviewed [app catalog](../../../../config/apps.json), not
in a copied engine registry.

The catalog launches `mcp` with `--automation-read-root` (the workspace) and
`--automation-write-root` (outputs/), the same flags as `--read-root` and `--write-root`. Both
folders must exist at launch, and a root left out denies that kind of access. The roots are
held directory handles, so a request path is relative to its root in forward slashes:
`inputs/crate.glb` to read, `crate.tcraft` to write. Absolute paths, `..`, drive prefixes, device
names and symlink or junction escapes are refused. A write replaces an existing file. Never add
`--bridge` or `--token`: they drive a running desktop app.

Not confined: a `.mcraft` package given to material_load, and the `material.link.*` commands
that re-cook a linked MaterialCraft layer (`material.link.set` does by default), run
`materialcraft-cli` as a child process with this user's full access and the system temp folder
for its files. It is taken from `MATERIALCRAFT_CLI`, then beside this binary, then PATH. Load a
`.mcraft` only from a trusted source, and treat a set `MATERIALCRAFT_CLI` as a finding. A
`.mcmat` or `.tcmat` needs no child process to load. `resource.text` reads the system font
folders.

The MaterialCraft link does not work at the pinned pair: this release reads `.mcmat` version 1
and recognises a `.mcraft` by its `package.json`, while MaterialCraft v0.4.1 writes version 2
`.mcmat` files and `.mcraft` files holding `package.sbs`, and cannot read the old package a
re-cook hands it. Bring MaterialCraft's outputs_export maps in with resource_import instead.

## Discover before execution

Discover the commands and the session before editing. Tools include session_inspect,
command_list, command_run, command_batch, project_new, project_open, project_save, mesh_import,
mesh_reimport, mesh_export, bake, bake_mesh_add, resource_import, material_save, material_load,
textures_export, paint_stroke and viewport_render. viewport_screenshot and the `ui_*` tools
answer only over a bridge and do nothing here.

## Workflow and risky operations

Start with project_new (a built-in mesh) or project_open/mesh_import, add layers with command_run
(`layer.add.fill`, `mask.add.black`, `effect.add.generator`), bake before mesh-driven generators
and smart materials, and undo with `command_run edit.undo`. command_batch stops at the first
error, at most 256 steps, and reports `completed`, `results` and `failed`. command_run refuses
every `file.*` command but `file.close`, `file.removeUnused` and `file.reimportMesh` without a
path, and any command given `path` or `dir`, at the top level or in a `files` entry: use the
workspace tools (for `textureSet.meshMap.import`, resource_import each baked map file and set it
with `textureSet.meshMap.set`). paint_stroke points are viewport pixels; the default render size
is the session viewport (1280×800), so they can be read straight off a viewport_render image.
bake uses the GPU when there is one (`cpu: true` forces the CPU), and viewport_render with
`samples` path traces, which is costly. mesh_import opens a new project: save the current one
first. Always give project_save a path: without one it reuses the path the project was opened
from, now relative to the write root.

## Durable verification

Check the saved `.tcraft` by reopening it and comparing session_inspect (texture sets,
resolution, layers, masks, baked maps); check every texture textures_export returned for size,
format and channel packing against the preset; reimport a mesh_export rather than trusting the
returned path; look at viewport_render, at most 2048 px a side and 5 MiB. JSON replies stop at
8 MiB. A project with UV tiles saved before 0.4 keeps its baked pixels unconverted: rebake it.

## Evidence and maintenance

Basis: upstream TextureCraft source (CLI parser, control-protocol documentation, MCP tool
definitions, workspace confinement, the MaterialCraft link, packaging and release assets),
rechecked on 2026-11-13 at v0.6.1. TextureCraft postdates the supplied Native MCP Project Plan
and CLI/MCP Integration Reference; it is integrated the same way. This card is source-grounded
guidance, not a runtime-tested capability contract. Upstream:
[control protocol and MCP](https://github.com/storytold/texturecraft/blob/main/docs/control-protocol.md),
[features](https://github.com/storytold/texturecraft/blob/main/docs/features.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
