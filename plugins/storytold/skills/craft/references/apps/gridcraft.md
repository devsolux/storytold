# GridCraft

## Choose this app

Workbooks, typed values and formulas. Native server key: `gridcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `gridcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover workbook inspection, bounded range reads, formula evaluation, native edits and save. Preserve numbers, text, booleans, nulls and error objects as their actual types.

## Workflow and risky operations

GridCraft owns formula calculation; do not substitute another model or recompute accounting truth in this Skill. The sources establish no native root flag. Partial XLS/XLSB/ODS import is not a promise of source-format round trips.

## Durable verification

Save XLSX where supported, reopen, compare formulas and recalculated/typed values, and surface error cells. A structurally valid OOXML ZIP is not a formula/fidelity pass. Keep exported data provenance for downstream slide/document work.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/gridcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
