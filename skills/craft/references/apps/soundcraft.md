# SoundCraft

## Choose this app

Offline audio sessions and mix bounce. Native server key: `soundcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `soundcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`soundcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/soundcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Since 0.7.0 `mcp` accepts `--automation-read-root DIR` and `--automation-write-root DIR`,
but the catalog still launches plain `mcp`, so the registered server is unconfined.
Assume OS-user-wide access.

## Discover before execution

Discover session inspection, audio import, native edit commands, save and bounce; these include inspect_session, open_session (which reports missing media), import_audio, execute, batch, save_session and bounce_mix. Interpret samples, seconds and bars/beats using the actual session tempo/rate and tool schema.

## Workflow and risky operations

Headless is an offline mix engine, not a live recording/playback device session. Plain mcp has no file-root restriction. The CLI now refuses a valueless --connect or root flag and the roots combined with --connect, but still silently ignores other unknown mcp flags (0.6.1 ignored the root flags too), so keep the registered args exactly as generated. UI tools are listed headless but need the desktop app. Unrelated-target replacement and source-media deletion need explicit approval.

## Durable verification

Check missing media before bouncing. Verify actual audio duration, sample rate, channels and expected mix (bounce_mix renders WAV, AIFF or FLAC at the session rate and reports seconds, peak, LUFS and true peak, not rate or channels; unlike session saves, which need replace: true, it has no replace guard and overwrites an existing file); listen when the task requires audio-quality judgment. Save the editable session separately. PCM parsing alone is not a mix or loudness approval.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-16 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
