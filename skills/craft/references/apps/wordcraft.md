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
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover inspect/get text, selection, formatting, tracked-change settings, save and page rendering. Read exact parameter schemas before setting review state. Tools at 0.5.0 include get_text, inspect_document, select_text, type_text, execute, batch, save_document and render_page.

## Workflow and risky operations

Preserve the agreed author and change-tracking mode; set explicit values rather than toggling an unknown state. The default config does not inject an author or start Zotero. The 0.5.0 CLI rejects --automation-read-root/--automation-write-root; upstream main adds them after that release, so using them needs a newer pinned release and a reviewed catalog change. Scripts/macros are not a workaround.

## Durable verification

Reopen DOCX and review text, tracked changes, fonts, pagination and exported PDF appearance. Legacy .doc opens but cannot be saved. Formats supported for reading are not automatically writable or semantically equivalent.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section, rechecked on 2026-10-12 against the v0.5.0 release
source (CLI parser, MCP docs, packaging). This card is source-grounded guidance,
not a runtime-tested capability contract. Upstream: [MCP documentation at v0.5.0](https://github.com/storytold/wordcraft/blob/v0.5.0/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
