# FilmCraft

## Choose this app

Video sequences, timeline and final movie assembly. Native server key: `filmcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `filmcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`filmcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/filmcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover project/sequence inspection, media import, frame rendering and export through actual tools. Ticks are 254,016,000,000 per second and commands also accept seconds, frames or timecode; frame conversion needs the sequence rate, so inspect it; sequence inspection reports durationFrames (a sequence ending partway through a frame counts that frame) and placed clips snap to the frame grid. Export runs through command_run (file.exportMedia) unless the running tool list has a dedicated export tool.

## Workflow and risky operations

Bare mcp creates the documented headless project; its only options are --bridge, --project, --demo and --data-dir. No native file-root flag is established: the CLI rejects root flags such as --automation-read-root. Use OS isolation for sensitive work. Do not start the documented unauthenticated desktop listener or use --bridge.

## Durable verification

Check duration, frame rate, timeline, audio and all media references. An offline clip (missing, made offline or unreadable) renders as a MEDIA NOT FOUND slate and the MCP export still succeeds: the result of file.exportMedia with wait: true, the job in jobs.list and each export.queue.list item carry offlineMedia, the items drawn as placeholders ([] when none). Treat a non-empty list as a failed deliverable, check with media.status or media.findMissing before exporting and inspect frames afterwards; only the standalone CLI export and render exit 1 on offline media unless --allow-offline. Neither file existence nor a retry proves the media was present. Since 0.9.0 a media or proxy path stored in a project, template or interchange file resolves beside it and is followed only on this computer or the document's own share; any other (a device too) counts as missing and renders the slate.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-18 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [agent and MCP guide](https://github.com/storytold/filmcraft/blob/main/docs/agents.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
