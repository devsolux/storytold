# LightCraft

## Choose this app

RAW development and photo catalogs. Native server key: `lightcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `lightcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

The documented --compact mode keeps discovery/dispatch while reducing generated tools. Discover photo query/import, controls, develop state, preview and export schemas as needed.

## Workflow and risky operations

Default to an ephemeral headless session. Persistent --library is deliberately not configured: it needs an explicit lock/ownership decision. Never open the same library in GUI and headless processes or remove its lock. Move-import can remove originals and needs separate consent.

## Durable verification

Verify RAW/develop expectations, rendered pixels, output filename and image properties. Exports may choose a new name on collision; repeated calls are not idempotent. No denoise service or live connect is started by this plugin.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/lightcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
