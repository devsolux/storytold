# LightCraft

## Choose this app

RAW development and photo catalogs. Native server key: `lightcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `lightcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`lightcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/lightcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

The documented --compact mode keeps discovery/dispatch while reducing generated tools. Discover photo query/import, controls, develop state, preview and export schemas as needed; compact mode keeps command_list, command_run, command_batch, doc_inspect, render_preview and helpers such as query_photos, get_develop, set_develop, render_photo and export. export writes .png, .jpg, .tif, .webp, .avif, .jxl, a flat .psd, DNG or the original with an XMP sidecar; read the live schema for the format-specific options.

## Workflow and risky operations

Default to an ephemeral headless session. Persistent --library is deliberately not configured: it needs an explicit lock/ownership decision. Never open the same library in GUI and headless processes or remove its lock. Move-import can remove originals and needs separate consent. Import onDeleted now defaults to restore (a file found in Recently Deleted comes back with its edits) rather than skip; pass it explicitly. export with addToPhotos (macOS) hands the written files to Apple Photos through Apple Events, into photosAlbum, after a one-time macOS consent prompt, and headless waits for Photos: that writes into the user's Photos (and iCloud) library outside any workspace, so it needs its own approval and is never a default. Never start lightcraft-cli denoise-serve, a plain-TCP listener for remote denoise, or set LIGHTCRAFT_DENOISE_URL.

## Durable verification

Verify RAW/develop expectations, rendered pixels, output filename and image properties. Exports may choose a new name on collision; repeated calls are not idempotent. Denoise runs in-process from per-user model folders (no weights are bundled); this plugin starts no denoise server, remote denoise-serve listener or live --connect session.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-14 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/lightcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
