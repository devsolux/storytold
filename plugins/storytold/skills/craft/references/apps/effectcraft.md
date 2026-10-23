# EffectCraft

## Choose this app

Motion graphics, compositions and keyframes. Native server key: `effectcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `effectcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`effectcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/effectcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots; still test the pinned binary and OS boundary.

## Discover before execution

Discover compositions, layer/property schemas, keyframe operations, native batches and frame/export jobs. Use the native progress/status APIs where present (progress notifications, renderQueue.list/renderQueue.stop) rather than adding a queue. Tools include get_project, get_comp, get_layer, get_property, set_property, add_keyframe, render_frame, save_project, batch and command_batch.

## Workflow and risky operations

The source-documented read/write roots enable restricted mode that refuses scripting and UI/control tools. Do not bypass it. Both roots must exist at launch; without a write root nothing is written. Keyframe-setting time may be layer time while sampling/render time is composition time; use the tool-specific timeBase when required. Layer and comp ids may be sent as strings; an all-digit string that matches no name is taken as an id. The viewer-resolution commands (view.res.*) change the saved project without an undo step. Since 0.13.0 anim.applyPreset and the property and link paste commands resolve effects/<match name>[#n]/<property> paths (the form presets and copied links carry) to the layer's effect instead of falling through silently; keys.delete returns the number of keys actually removed, so 0 means nothing changed.

## Durable verification

Check composition dimensions, timing, layer offset/stretch, expected frames and media. Preserve native warnings. batch rolls back when a step fails, while command_batch keeps one undo step per edit and stops at the first error; neither spans files or apps. Autosave is not enabled implicitly. A project saved by 0.13.0 also records each comp's current time (compTimes, editor state beside activeComp/openComps; older versions ignore it) and reopens there, so read the time back instead of assuming a reopened comp sits at 0. Since 0.11.1 a footage path stored in a project resolves beside it and is followed only on this computer or the project's own share; any other (a device or a non-file URL too) is marked missing without being read, so list missing footage with file.findMissing after opening.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-23 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [agent guide](https://github.com/storytold/effectcraft/blob/main/docs/agents.md) and [MCP documentation](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
