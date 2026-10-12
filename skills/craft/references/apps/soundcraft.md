# SoundCraft

## Choose this app

Offline audio sessions and mix bounce. Native server key: `soundcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `soundcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover session inspection, audio import, native edit commands, save and bounce. Interpret samples, seconds and bars/beats using the actual session tempo/rate and tool schema.

## Workflow and risky operations

Headless is an offline mix engine, not a live recording/playback device session. No native file-root flag is established. Unrelated-target replacement and source-media deletion need explicit approval.

## Durable verification

Check missing media before bouncing. Verify actual audio duration, sample rate, channels and expected mix; listen when the task requires audio-quality judgment. Save the editable session separately. PCM parsing alone is not a mix or loudness approval.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
