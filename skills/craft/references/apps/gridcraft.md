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

Discover workbook inspection, bounded range reads, formula evaluation, native edits and save. Preserve numbers, text, booleans, nulls and error objects (for example {"error":"#DIV/0!"}) as their actual types. Tools include inspect_workbook, read_range, get_cell, set_cell, write_range, evaluate_formula, execute_command and save_workbook. Since 0.13.0 list_windows gives each open window's `window` and `doc` ids, and every tool that acts on a workbook takes an optional `window` or `doc`; without one it acts in the active window, which new_workbook and open_workbook move to the new book. set_cell input takes a string, number or boolean; write_range parses strings like typed input by en-US rules ("05.04.2026" becomes a date), while execute_command range.setValues {range, values, parse: false} keeps them as text (0.12.1). evaluate_formula takes English function names with `,` separators and, since 0.11.1, fails with the reason on a formula a cell would refuse (an unknown function is still #NAME?). A malformed format_range borders or sort_range keys argument is refused as invalid params (-32602). execute_command file.open {path, csvAsText: true} keeps every CSV/TSV/TXT field as text (0.9.0; open_workbook has no such parameter). A signed or doubly-$ whole-row or whole-column range (+1:+3, $$A:$$C) is an invalid range, defined names and table names are at most 255 characters, and insert.pivotTable refuses an unknown value-field func.

## Workflow and risky operations

GridCraft owns formula calculation; do not substitute another model or recompute accounting truth in this Skill. mcp takes only --connect, --in and --sample, so no native root flag exists; never use --connect. Since 0.11.1 automate.runScript refuses the stored scripts of a workbook opened from a file until it is trusted (automate.trustScripts, or trusted: true for one run) and any step that reaches outside the workbook (file.*, link.*, a `path` parameter, since 0.12.1 window commands); inspect_workbook reports `trust` (local or fromFile, 0.12.1). Trust a file's scripts only on the user's word. Open reads only regular files up to 2 GB (0.12.1). XLSB and ODS import values only and legacy .xls (BIFF8) imports partially (formulas with cached results, no styles, charts or comments; encrypted and BIFF5 files refused); none of the three can be saved, so none round-trips. Save refuses an unknown extension (write .xlsx, .csv, .tsv, .json or .html), sheet names XLSX cannot hold, CSV/TSV over 512 MiB and HTML over 100,001 rows or (0.12.1) 4,000,000 cells; a .pdf path is not a save but a print of the active sheet (Page Setup applies) that leaves the workbook's own file and unsaved state untouched.

## Durable verification

Save XLSX where supported, reopen, compare formulas and recalculated/typed values, and surface error cells. Custom numeric filters (<, <=, >, >=) match numbers only, so blank and text rows are hidden (0.9.0). A formula longer than Excel's 8,192 characters is a parse error; in an opened file such a cell keeps its formula text and cached value. A structurally valid OOXML ZIP is not a formula/fidelity pass. Keep exported data provenance for downstream slide/document work.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-29 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/gridcraft/blob/main/docs/mcp.md) and [format limits](https://github.com/storytold/gridcraft/blob/main/docs/file-format-parity.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
