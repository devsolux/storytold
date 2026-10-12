# EffectCraft

## Choose this app

Motion graphics, compositions and keyframes. Native server key: `effectcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `effectcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents distinct read/write roots; still test the pinned binary and OS boundary.

## Discover before execution

Discover compositions, layer/property schemas, keyframe operations, native batches and frame/export jobs. Use the native progress/status APIs where present rather than adding a queue.

## Workflow and risky operations

The source-documented read/write roots enable restricted mode that refuses scripting. Do not bypass it. Keyframe-setting time may be layer time while sampling/render time is composition time; use the tool-specific timeBase when required.

## Durable verification

Check composition dimensions, timing, layer offset/stretch, expected frames and media. Preserve native warnings. Native batch rollback semantics are engine-specific; they do not promise cross-file or cross-app atomicity. Autosave is not enabled implicitly.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
