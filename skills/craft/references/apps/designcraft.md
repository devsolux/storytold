# DesignCraft

## Choose this app

Page layout, stories and publishing. Native server key: `designcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `designcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover document structure, story reading/editing, image placement, page rendering, save and export. Native tools and supported PDF/IDML routes evolve; inspect the running schema.

## Workflow and risky operations

Text positions are UTF-8 byte offsets, not character counts or JavaScript string lengths. Compute a boundary with len(prefix.encode("utf-8")) only when the native schema requires it. Coordinates use points and spread space; page indices can be zero-based. No native file-root flag is established.

## Durable verification

Inspect overset text, fonts, linked images, pages and exported layout. Validate the actual saved/exported file and render relevant pages. CLI export options may apply only to following exports; do not use shell fallback without an explicit unique need.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/designcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
