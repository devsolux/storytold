# FilmCraft

## Choose this app

Video sequences, timeline and final movie assembly. Native server key: `filmcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `filmcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover project/sequence inspection, media import, frame rendering and export through actual tools. Do not translate native ticks into guessed seconds; inspect the relevant timebase.

## Workflow and risky operations

Bare mcp creates the documented headless project. No native root flags are established by the supplied sources. Use OS isolation for sensitive work. Do not start the documented unauthenticated desktop listener or use --bridge.

## Durable verification

Check duration, frame rate, timeline, audio and all media references. An export can leave a file while reporting failure because offline placeholders were rendered. Neither file existence nor a retry resolves that warning.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/filmcraft/blob/main/docs/agents.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
