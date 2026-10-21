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
Native source documents distinct read/write roots; still test the pinned binary and OS boundary.

## Discover before execution

Discover inspect/get text, selection, formatting, tracked-change settings, save and page rendering. Read exact parameter schemas before setting review state. Tools include get_text, inspect_document, select_text, type_text, execute, batch, save_document and render_page. open_document takes an optional password for a protected Word file (since 0.9.0; without it the call fails asking for one), and a document opened with a password is saved with it again (file.save and file.saveAs take password; file.encrypt with null or "" saves it plain). format.set, para.set, styles.modify and the table style commands take CharProps/ParaProps objects: every field is optional, lengths are points, colours are hex or [r, g, b], a Border needs a width above 0 to show, and an unknown field name is ignored rather than refused, so inspect the result after setting.

## Workflow and risky operations

Preserve the agreed author and change-tracking mode; set explicit values rather than toggling an unknown state. The default config does not inject an author or start Zotero. The catalog launches mcp with --automation-read-root (the workspace) and --automation-write-root (outputs/): every path a command opens, inserts, compares or reads a template from must lie inside the read root, every save, export, print, rename or template write inside the write root, and a refused path is an ordinary tool error (automation path rejected). file.rename renames the open document's file on disk (the old name is gone), so that file must lie inside both roots. Both folders must exist at launch, each flag is given once, --connect with them is an error, and the desktop app is never confined. Commands that take no path still read and change the open document, and the Zotero commands use a socket, not files. Scripts/macros are not a workaround.

## Durable verification

Reopen DOCX and review text, tracked changes, fonts, pagination and exported PDF appearance. get_text omits tracked deletions, while inspect_document's paragraph text still includes them. Legacy .doc opens but cannot be saved. A save into a folder that refuses the temporary file a safe save needs (macOS privacy-protected folders, a read-only folder) writes a new file directly but leaves an existing file unchanged and fails with an error saying so (0.9.0); retry into another folder inside the write root. Formats supported for reading are not automatically writable or semantically equivalent. An .xml save is Word XML (Flat OPC) or, with format wordml2003, a Word 2003 XML document.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-21 against the upstream
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation](https://github.com/storytold/wordcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
