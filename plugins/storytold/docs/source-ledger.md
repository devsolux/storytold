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
| [FigCraft MCP](https://github.com/storytold/figcraft/blob/main/docs/mcp.md), [CLI](https://github.com/storytold/figcraft/blob/main/docs/cli.md), [CLI source](https://github.com/storytold/figcraft/blob/main/apps/figcraft-cli/src/main.rs) | Headless `mcp` with no file-root flag (only `--attach PORT` and the global `--no-system-fonts`), 18 tools, `inspect_document` without required parameters, page-unit coordinates, `.figcraft` save and PNG/JPG/SVG/WebP/PDF/`.fig` export. | Source review on 2026-10-14; the binary was not executed. The AppImage `cli` subcommand is documented but `setup` uses the tarball. |
| [WordCraft MCP](https://github.com/storytold/wordcraft/blob/main/docs/mcp.md) | `mcp --automation-read-root` / `--automation-write-root` (since 0.6.1): separate read and write roots covering every path a command opens or writes, existing folders required, links resolved before the check, `--connect` refused with them, the desktop app unconfined, path-less commands still edit the open document. | Source review plus a local probe of the pinned 0.6.1 binary with the flags and the operator's `setup --upgrade --replace` to 0.7.0 (see [verification](verification.md)); denial of a path outside a root is an M3 test, not asserted here. |

## Release-tag review of all twelve apps — 2026-10-12

Every app card was rechecked against that app's latest release tag, not `main`:
PhotoCraft v0.7.0, VectorCraft v0.9.0, FilmCraft v0.6.0, LightCraft v0.6.0,
PdfCraft v0.6.0, EffectCraft v0.8.0, DesignCraft v0.6.0, GridCraft v0.5.0,
WordCraft v0.5.0, DeckCraft v0.5.0, CADCraft v0.5.0 and SoundCraft v0.5.0. The
review read each CLI's `mcp` argument parser, MCP/agent docs, MCP tool
definitions, Windows/Linux/macOS packaging and release assets:

- Every catalog launch flag is accepted by the released CLI. WordCraft 0.5.0
  rejects the root flags that its `main` branch added after release, and
  FilmCraft 0.6.0 rejects them by test, so both stay `os_only`.
- Only macOS separates the CLI from the desktop app (`.app` plus a
  `<app>-cli-<version>-macos-universal.zip` asset listed in `SHA256SUMS.txt`).
  Windows MSI/portable ZIP and Linux `.deb`/`.rpm` packaging install the CLI.
  The ArtCraft Launcher is not documented in these repositories; its macOS
  behavior was observed locally (installed `.app` bundles contain no CLI).
- Card links are pinned to those tags. The catalog's `documentation` links still
  point at mutable `main`; changing them would invalidate existing probe
  fingerprints, so they change only with a reviewed catalog update.

This is source review, not binary testing; only PhotoCraft 0.7.0 was executed
(see [verification](verification.md)).

## FigCraft added — 2026-10-14

FigCraft postdates both supplied documents, which enumerate twelve apps. Its
catalog entry, card, acceptance scenario and release pin were derived from the
upstream `main` branch and the v0.5.1 release (tag commit
`c5830e4683408a16f0e9b7d8b246c805190e7e6a`): the CLI parser accepts `mcp
[--attach PORT]` and the global `--no-system-fonts` only, so the app is
`os_only` like the other eight unconfined apps, and the smoke tool is
`inspect_document`, whose parameters are all optional. The three pinned
archives (`figcraft-cli-0.5.1-macos-universal.zip`,
`figcraft-0.5.1-linux-x86_64.tar.gz`, `figcraft-0.5.1-windows-x64-portable.zip`)
were downloaded, matched the release's `SHA256SUMS.txt`, and each contains
exactly one `figcraft-cli` (159 MB universal on macOS); the macOS CLI is signed
and notarized by the same Apple team `DJ6XS33FX8` as the other apps
(`codesign` and `spctl` inspection only; the binary was not run). The daily
workflow's run 38583930461 later that day moved the pin to v0.6.0 (the CLI
parser and both docs files are unchanged between the two tags), signed its
three archives and ran `setup` for it on the Linux, Windows and macOS runners;
see [verification](verification.md).

`config/releases.json` is the reviewed pin set for `storytold.py setup`: tag and
tag commit from the GitHub API, the macOS CLI zip name/size from the release
assets, its SHA-256 copied from the release's `SHA256SUMS.txt`, the smoke tool
from the tag's MCP source, and the Apple team `DJ6XS33FX8` observed on the
notarized PhotoCraft CLI and `PhotoCraft.app`. At install time `setup` re-reads
the published sums and the binary's signature, so the manifest is a consistency
gate, not the sole authenticity root. The local installation lock must use full
immutable revisions and trusted executable hashes; this repository deliberately
does not invent binary pins.

## Release-tag recheck of the eight moved apps — 2026-10-14

Pull request #2 moved eight pins. Each card was rechecked against the new tag
the same way as on 2026-10-12 (CLI `mcp` parser, MCP docs and tool
definitions, packaging and release assets), with the tool counts from that
run's macOS probe:

- No app changed its `mcp` launch flags, so every catalog entry still matches
  the released CLI, and no tool was renamed or removed. Tool counts are
  unchanged except PhotoCraft (21 to 25).
- DeckCraft v0.6.1: packaging and CI only (upstream now signs its Windows
  builds; `setup` still verifies the Sigstore bundle). Card unchanged.
- DesignCraft v0.8.0: item-creating commands take `spread` (a body spread
  index or a parent-spread object); `script --help`; atomic image writes.
- EffectCraft v0.9.2: string ids, `list_fonts {variable}`, `inDelta` and
  `outDelta`, per-comp viewer resolution saved without an undo step, Linux
  font folders.
- FilmCraft v0.7.2: export results, jobs and queue items carry `offlineMedia`;
  the standalone CLI `export` and `render` exit 1 on offline media unless
  `--allow-offline`; `durationFrames`; clips snap to the frame grid. Still no
  root flag (`mcp` takes only `--bridge`, `--project`, `--demo`, `--data-dir`).
- LightCraft v0.7.1: `export` gains `.jxl`, flat `.psd`, `addToPhotos` and
  `photosAlbum` (Apple Events into the user's Photos library after a one-time
  macOS consent); import `onDeleted` defaults to `restore` instead of `skip`;
  a new `lightcraft-cli denoise-serve` network listener (not used); headless
  sessions load the SAM 3 model folder. `mcp` flags unchanged.
- PhotoCraft v0.8.2: four new document tools (`doc_place`, `doc_export_layers`,
  `doc_export_data_sets`, `doc_import_data_sets`); `command_batch`
  `stop_on_error` default and no-rollback recovery documented; `doc_inspect`
  mask fields; `image.duplicate` and `history.newDocument` for experiments;
  `--tga-bits` and Actions sets in the standalone CLI.
- WordCraft v0.7.0: `docs/mcp.md` documents CharProps/ParaProps (unknown
  field names are ignored); `convert --format wordml2003|flatopc`. The CLI has
  accepted `mcp --automation-read-root DIR --automation-write-root DIR` since
  v0.6.1 (confining the headless server only), which the 2026-10-12 review
  found absent at v0.5.0. Storytold 1.5.0 adds the two flags to WordCraft's
  catalog launch (`read_write`, like PhotoCraft, VectorCraft and EffectCraft);
  because that changes the registration `setup` writes, existing installs
  re-register with `setup --app wordcraft --upgrade --replace`.

Source review plus the run's probes; no card claim was verified by editing a
document on a developer machine.

## Build infrastructure

The workflow uses reviewed full-commit action references:

- [actions/checkout v7.0.1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1): `3d3c42e5aac5ba805825da76410c181273ba90b1`.
- [actions/setup-python v7.0.0](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97): `5fda3b95a4ea91299a34e894583c3862153e4b97`.
- [sigstore/cosign-installer v4.1.2](https://github.com/sigstore/cosign-installer/commit/6f9f17788090df1f26f669e9d70d6ae9567deba6): `6f9f17788090df1f26f669e9d70d6ae9567deba6`, installing cosign v3.1.3 (the release workflow only).

Both tags resolve to those commits and were the latest releases on the review
date, but GitHub Actions was not executed. Python 3.11/3.13 and
Linux/macOS/Windows matrix entries are **configured targets**, not a claim that
every combination was run. MCP is the only optional direct runtime dependency;
its transitive resolution was installed for the SDK test but is not locked.
Recheck releases before an intentional upgrade and run both core and SDK/native
acceptance tests.
