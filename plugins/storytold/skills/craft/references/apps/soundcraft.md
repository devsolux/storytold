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
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover session inspection, audio import, native edit commands, save and bounce; these include inspect_session, open_session (which reports missing media), import_audio, execute, batch, save_session and bounce_mix. Interpret samples, seconds and bars/beats using the actual session tempo/rate and tool schema.

## Workflow and risky operations

Headless is an offline mix engine, not a live recording/playback device session. No native file-root flag is established. The CLI silently ignores unknown or incomplete mcp flags, so keep the registered args exactly as generated. UI tools are listed headless but need the desktop app. Unrelated-target replacement and source-media deletion need explicit approval.

## Durable verification

Check missing media before bouncing. Verify actual audio duration, sample rate, channels and expected mix (bounce_mix reports seconds, peak, LUFS and true peak, not rate or channels); listen when the task requires audio-quality judgment. Save the editable session separately. PCM parsing alone is not a mix or loudness approval.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-12 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
