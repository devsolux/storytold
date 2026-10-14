# WordCraft

## Choose this app

Rich text, tracked changes and documents. Native server key: `wordcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `wordcraft-cli` (`.exe` on native Windows). On macOS the `.app` (from
the `.dmg` or the ArtCraft Launcher) holds only the desktop app: install the separate
`wordcraft-cli-<version>-macos-universal.zip` release asset. Windows MSI/portable ZIP and
Linux `.deb`/`.rpm` packages install the CLI next to the app (Linux: `/usr/bin/wordcraft-cli`).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
The released CLI accepts --automation-read-root DIR and --automation-write-root DIR for mcp (they confine
the headless server only; a connected running app is not confined), but the reviewed catalog still launches
WordCraft without them: assume OS-user-wide access until a reviewed catalog change adds them.

## Discover before execution

Discover inspect/get text, selection, formatting, tracked-change settings, save and page rendering. Read exact parameter schemas before setting review state. Tools include get_text, inspect_document, select_text, type_text, execute, batch, save_document and render_page. format.set, para.set, styles.modify and the table style commands take CharProps/ParaProps objects: every field is optional, lengths are points, colours are hex or [r, g, b], a Border needs a width above 0 to show, and an unknown field name is ignored rather than refused, so inspect the result after setting.

## Workflow and risky operations

Preserve the agreed author and change-tracking mode; set explicit values rather than toggling an unknown state. The default config does not inject an author or start Zotero. The installed CLI's help lists --automation-read-root/--automation-write-root, but adding them to the launch is a reviewed catalog change that also re-registers the server; do not add them by hand. Scripts/macros are not a workaround.

## Durable verification

Reopen DOCX and review text, tracked changes, fonts, pagination and exported PDF appearance. Legacy .doc opens but cannot be saved. Formats supported for reading are not automatically writable or semantically equivalent. An .xml save is Word XML (Flat OPC) or, with format wordml2003, a Word 2003 XML document.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-14 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/wordcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
