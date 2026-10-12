# Source ledger and verification scope

Review date: **2026-10-12**. The integration uses the attached project plan as its
architecture authority. Fresh public-document checks supplement its implementation
mechanics; they do not silently replace its decisions or prove native behavior.

## Supplied material, retained unchanged

| Document | SHA-256 | Use |
|---|---|---|
| [Native MCP Project Plan](sources/Claude_Code_Craft_Native_MCP_Project_Plan.md) | `fabea9691589f563c6f9f7a8df89d2d8b835ea933315ad4d6c1ad5b8dfd0cbc1` | Architecture authority: twelve direct, local headless stdio servers; one craft Skill; deterministic checks. |
| [CLI/MCP Integration Reference](sources/Crafting_Apps_CLI_MCP_Integration_Reference.md) | `3f0ec5724b801db503d10947c2e06c5a0c79e68f0996cb7684f10a77ef92f45c` | App facts and pitfalls only. Its proposed gateway/remote architecture is superseded by the Native MCP plan. |

Engineer **1.91.0 source** was inspected for AGENTS, Makefile, canonical build,
verification, cleanup and isolated-test patterns. Storytold adopts the useful
patterns, not Engineer's domain commands, server code, license or agents.

## Fresh primary-source checks

| Source | Checked topic | Important limit |
|---|---|---|
| [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference), [marketplaces](https://code.claude.com/docs/en/plugins/create-marketplace) | Plugin metadata, skill layout, marketplace identity and plugin@marketplace installation. | Claude Code 2.1.282: strict validation, local-marketplace install and `plugin details` executed in an isolated config directory. |
| [Claude MCP](https://code.claude.com/docs/en/mcp) | Direct stdio, project scope, environment expansion, approval boundaries. | Concrete paths avoid unresolved placeholders. No undocumented Claude `cwd` field is generated; test actual host working directory. |
| [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins) | Portable root `plugin.json` with OpenAI settings under `extensions.com.openai`; repo marketplace at `.agents/plugins/marketplace.json`. The `.codex-plugin/plugin.json` overlay is only a compatibility fallback, replaced by that extension, so it is not shipped. | This package distributes guidance and templates, not a remote MCP app. The ChatGPT desktop app was not tested. |
| [Codex CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) | `codex plugin add <plugin[@marketplace]>`, marketplace source commands and local plugin inspection. | Codex CLI 0.162.0-alpha.17.2: local-marketplace install and Skill discovery executed in an isolated `CODEX_HOME`. |
| [Local Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) | `[mcp_servers]` command/args/cwd TOML for local stdio. | The generator writes a new fragment; operator review/merge and runtime validation remain necessary. |
| [Portable plugin schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), [MCP schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json) | Supported portable manifest fields and stdio descriptor shape. | Static checks cover the fields this project emits, not every possible host schema or feature. |
| [MCP SDK on PyPI](https://pypi.org/project/mcp/), [Client documentation](https://py.sdk.modelcontextprotocol.io/client/), [transports](https://py.sdk.modelcontextprotocol.io/client/transports/) | Current SDK 2.3.0; `Client`, `StdioServerParameters`, typed results and client lifecycle. | Installed and exercised by `make test-sdk` against the synthetic stdio fixture only, not against Craft binaries. |
| [Pinned SDK Client source](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/src/mcp/client/client.py) | `mode="legacy"` is the SDK's name for the initialize handshake; the official SDK drives it instead of a hand-written transport. | Deliberate for the plan's native initialize negotiation. In that mode the SDK's automatic input-required and header-mismatch resends do not apply. |
| [PhotoCraft development](https://github.com/storytold/photocraft/blob/main/docs/development.md) | Native roots and discovery hints, including `doc_render_preview` in current docs. | This differs from older `render_preview` references: discover live names, never substitute a hard-coded command. |
| [VectorCraft CLI source](https://github.com/storytold/vectorcraft/blob/main/apps/vectorcraft-cli/src/main.rs) | Explicit headless launch and native mode/flag context. | Source review is not proof of no GUI attach in an installed binary. |
| [PdfCraft README](https://github.com/storytold/pdfcraft/blob/main/README.md) | Single root, compact mode and explicit save/build considerations. | Optional MCP feature and actual flags must be tested on the installed build. |
| [EffectCraft MCP](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md) | Native root restrictions, scripts and headless operation. | Actual denial behavior is an M3 test, not an assertion from a tool description. |
| [LightCraft MCP](https://github.com/storytold/lightcraft/blob/main/docs/mcp.md) | Compact discovery, library and import risks. | No persistent library, live connection or denoise service is enabled by default. |

FilmCraft, DesignCraft, GridCraft, WordCraft, DeckCraft, CADCraft and SoundCraft
cards are based on the supplied reference; a fresh complete source audit of these
seven projects was **not** performed. All app links to `main` are mutable. The
local installation lock must use full immutable revisions and trusted executable
hashes; this repository deliberately does not invent current binary pins.

## Build infrastructure

The workflow uses reviewed full-commit action references:

- [actions/checkout v7.0.1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1): `3d3c42e5aac5ba805825da76410c181273ba90b1`.
- [actions/setup-python v7.0.0](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97): `5fda3b95a4ea91299a34e894583c3862153e4b97`.

Both tags resolve to those commits and were the latest releases on the review
date, but GitHub Actions was not executed. Python 3.11/3.13 and
Linux/macOS/Windows matrix entries are **configured targets**, not a claim that
every combination was run. MCP is the only optional direct runtime dependency;
its transitive resolution was installed for the SDK test but is not locked.
Recheck releases before an intentional upgrade and run both core and SDK/native
acceptance tests.
