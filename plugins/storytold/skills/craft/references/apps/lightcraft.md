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

The documented --compact mode keeps discovery/dispatch while reducing generated tools. Discover photo query/import, controls, develop state, preview and export schemas as needed; compact mode keeps command_list, command_run, command_batch, doc_inspect, render_preview and helpers such as query_photos, get_develop, set_develop, render_photo and export. export writes .png, .jpg, .tif, .webp, .avif, .jxl, a flat .psd, DNG, rendereddng (a linear 16-bit float DNG with the edit baked in) or the original with an XMP sidecar; read the live schema for the format-specific options. Since 0.11.0 `export`, `render_photo` and the bridged `screenshot` are annotated `destructiveHint: true` because their `path` can replace a file; the annotations are client hints, not a file-access sandbox.

## Workflow and risky operations

Default to an ephemeral headless session. Persistent --library is deliberately not configured: it needs an explicit lock/ownership decision. Never open the same library in GUI and headless processes or remove its lock. Move-import can remove originals and needs separate consent. Import onDeleted now defaults to restore (a file found in Recently Deleted comes back with its edits) rather than skip; pass it explicitly. An imported JPEG or TIFF beside a raw of its stem reads its own `<file>.xmp`, never the raw's shared stem sidecar (0.11.0). export with addToPhotos (macOS) hands the written files to Apple Photos through Apple Events, into photosAlbum, after a one-time macOS consent prompt, and headless waits for Photos: that writes into the user's Photos (and iCloud) library outside any workspace, so it needs its own approval and is never a default. export destinationMode sameAsOriginal writes each file into its original's folder instead of dir, and merge.* writes its -HDR/-Pano/-HDR-Pano DNG beside the first source photo (merge.hdrBatch once per bracket set): both write into photo folders and need approval. An explicit export `path` (likewise render_photo and screenshot `path`) replaces an ordinary file already there, while a catalogued original or its XMP sidecar is refused with nothing written; `dir` batches follow `conflict` (default unique). export refuses a `bitDepth` the format lacks (8 for JPEG, 8 or 16 for PNG, 8, 16 or 32 for TIFF), judged against the format actually written: a headless `path` whose extension names no format writes PNG. `photo.reload` re-reads the targeted files from disk and commits the result as one undo step (saved, and XMP auto-written where that is on). Lightroom import (`library.inspectLightroom`, `library.importLightroom`) reads `.lrcat` pages on demand up to 16 GiB (WAL still 1 GiB) and skips, listed under `skipped` with a reason, images whose file, folder or root record is gone instead of failing the import; close Lightroom first. `metadata.reverseGeocode` takes `maxDistance` (metres, positive): past it City stays empty and the town found is reported as `nearestCity`. slideshow.templates save/import/delete change JSON files in the user's settings folder. Never start lightcraft-cli denoise-serve, a plain-TCP listener for remote denoise, or set LIGHTCRAFT_DENOISE_URL.

## Durable verification

Verify RAW/develop expectations, rendered pixels, output filename and image properties. Exports may choose a new name on collision; repeated calls are not idempotent. Opaque 8-bit PNG, TIFF and WebP exports are written without an alpha channel (a photo with real transparency keeps it; 0.10.0), so expect RGB, not RGBA, in image properties. slideshow.export (PDF, JPEG sequence or AV1 video) runs in the background and returns a taskId unless wait: true; read slideshow.exportStatus before checking its output. print.exportPdf replaces an existing file at its path (never an original). Denoise runs in-process from per-user model folders (no weights are bundled); this plugin starts no denoise server, remote denoise-serve listener or live --connect session. `index`, `component` and mask `id`/`ids` parameters (history.restore, version.*, redeye.*, mask.*, spot.*) must be non-negative integers: fractional, negative or non-numeric values are refused before any change (0.11.0), and one brush stroke lays at most 2,000,000 dabs, the rest dropped silently. `crop.aspect` keeps the crop's present orientation for a named ratio and uses `[w, h]` as given (`orientation: "crop"|"given"` overrides), and with Constrain Crop on a Geometry, Upright or lens edit shrinks the stored crop about its centre, so read the crop back after such edits. In connect mode `photo.reload` replies `{background: true, count}` unless `wait: true`. Downscaling at 2:1 or more now uses Lanczos3 rather than a box filter, so downscaled export pixels differ from 0.10.0 renders.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-23 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/lightcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
