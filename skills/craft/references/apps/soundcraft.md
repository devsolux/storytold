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
Native source documents distinct read/write roots (since 0.7.0); still test the pinned binary and OS boundary.

## Discover before execution

Discover session inspection, audio import, native edit commands, save and bounce; these include inspect_session, open_session (which reports missing media), import_audio, execute, batch, save_session and bounce_mix. batch takes at most 1000 calls and refuses a longer list before any call runs (since 0.10.0; 0.8.0 ran the first 1000 and dropped the rest without a word). Since 0.12.1 mix.send refuses an unknown bus name instead of creating the bus. Since 0.13.1 edit.strip_silence takes mode strip, extract (removes the audio, keeps the silence) or separate (cuts without removing), and edit.strip_silence_preview returns the ranges Strip would keep without changing anything. Interpret samples, seconds and bars/beats using the actual session tempo/rate and tool schema.

## Workflow and risky operations

Headless is an offline mix engine, not a live recording/playback device session. The catalog launches mcp with --automation-read-root (the workspace) and --automation-write-root (outputs/): open_session, every import, track.load_preset and mix.sampler_load must read inside the read root, and every save, bounce, export, preset save and score command inside the write root, together with what a session save writes beside it (Audio Files/, Backups/, its temporary file; since 0.10.0 a backup never replaces an existing file or follows a link); a refused path is an ordinary tool error (automation path rejected), and session media outside the read root loads as missing; since 0.8.0 so does a stored source or movie path that names another computer (other than the session's own share), a device or a URL (not opened). Both folders must exist at launch, each flag may be repeated since 0.13.1 (a path inside any root of its kind passes), --connect with them is an error, and the desktop app is never confined. Not covered: path-less commands still read and change the open session (and inspect_session returns it), and plug-in discovery loads native plug-in binaries from the system folders. Before 0.7.0 the CLI ignored the root flags, so preflight refuses an older pinned SoundCraft; until 0.14.0 it also ignored other unknown mcp flags, which are now usage errors (exit 2) before anything runs, as are a stray argument, a repeated flag other than the roots and a root flag without a folder; keep the registered args exactly as generated. UI tools are listed headless but need the desktop app. Unrelated-target replacement and source-media deletion need explicit approval.

## Durable verification

Check missing media before bouncing. Verify actual audio duration, sample rate, channels and expected mix (bounce_mix renders WAV, AIFF or FLAC at the session rate and reports seconds, peak, LUFS and true peak, not rate or channels; since 0.13.1 32-bit float output keeps finite samples above full scale instead of clipping them; unlike session saves and, since 0.13.1, file.export_session_text, which need replace: true, it has no replace guard and overwrites an existing file); listen when the task requires audio-quality judgment. Save the editable session separately. PCM parsing alone is not a mix or loudness approval.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-29 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
