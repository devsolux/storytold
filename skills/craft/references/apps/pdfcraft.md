# PdfCraft

## Choose this app

PDF inspection, operations and validation. Native server key: `pdfcraft`. Plugin-provided or
host-specific namespacing may change the callable tool prefix; discover it.

## Launch and scope

Native executable: `pdfcraft-cli` (`.exe` on native Windows).
The source-derived launch arguments live in the single reviewed
[app catalog](../../../../config/apps.json), not in a copied engine registry.
Native source documents one root; it does not separate read and write authority.

## Discover before execution

Discover actual PDF tools; compact mode may expose tool_search/tool_call rather than every operation. The pinned build must include MCP support. Inspect document and page structure before choosing edits.

## Workflow and risky operations

--root confines one tree, not a separate read-only input directory. Edits can remain in memory until explicit doc_save. Work on a new output. Destructive page/security/redaction changes require explicit permission; do not drive the separate desktop ui channel.

## Durable verification

Reopen the saved PDF and check page count, text and rendering. For redactions, use a genuine content-removal audit and inspect sanitized output; visual rectangles are not enough. The helper only checks PDF markers, not validity or confidentiality.

## Evidence and maintenance

Basis: supplied Native MCP Project Plan, section 4, and CLI/MCP Integration
Reference, app-specific section. This card is source-grounded guidance, not a
runtime-tested capability contract. [Upstream source/documentation](https://github.com/storytold/pdfcraft/blob/main/README.md).
Pin the source revision and executable hash, verify help/flags and current
`tools/list`, then run the app's non-sensitive acceptance fixture before real work.
