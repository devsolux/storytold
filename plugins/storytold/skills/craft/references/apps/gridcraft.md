# GridCraft

## Choose this app

Workbooks, typed values and formulas. Native server key: `gridcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `gridcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`gridcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/gridcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover workbook inspection, bounded range reads, formula evaluation, native edits and save. Preserve numbers, text, booleans, nulls and error objects (for example {"error":"#DIV/0!"}) as their actual types. Tools include inspect_workbook, read_range, get_cell, set_cell, write_range, evaluate_formula, execute_command and save_workbook.

## Workflow and risky operations

GridCraft owns formula calculation; do not substitute another model or recompute accounting truth in this Skill. The sources establish no native root flag. XLSB and ODS import values only, XLSB cannot be written and legacy .xls is refused; none of these round-trips.

## Durable verification

Save XLSX where supported, reopen, compare formulas and recalculated/typed values, and surface error cells. A structurally valid OOXML ZIP is not a formula/fidelity pass. Keep exported data provenance for downstream slide/document work.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-12 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/gridcraft/blob/main/docs/mcp.md) and [format limits](https://github.com/storytold/gridcraft/blob/main/docs/file-format-parity.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
