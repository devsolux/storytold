# WordCraft

## Choose this app

Rich text, tracked changes and documents. Native server key: `wordcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `wordcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
No native MCP root restriction is established here. Assume OS-user-wide access.

## Discover before execution

Discover inspect/get text, selection, formatting, tracked-change settings, save and page rendering. Read exact parameter schemas before setting review state.

## Workflow and risky operations

Preserve the agreed author and change-tracking mode; set explicit values rather than toggling an unknown state. The default config does not inject an author or start Zotero. No native file-root flag is established. Scripts/macros are not a workaround.

## Durable verification

Reopen DOCX and review text, tracked changes, fonts, pagination and exported PDF appearance. Legacy DOC may be read-only. Formats supported for reading are not automatically writable or semantically equivalent.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/wordcraft/blob/main/docs/mcp.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
