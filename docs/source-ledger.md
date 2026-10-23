# Source ledger and verification scope

Review dates: **2026-10-12 to 2026-10-21** (each section names its own). The integration uses the attached project plan as its
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
  Superseded on 2026-10-13: card links point at `main` too, as AGENTS.md now
  requires.

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

## Release-tag recheck of the three apps moved by pull request #3 — 2026-10-14

The hand-triggered run 38588658915 (the first with WordCraft's root-flag
launch) moved DeckCraft to v0.7.0, PdfCraft to v0.8.0 and VectorCraft to
v0.11.0, signed their nine archives, verified on the three runners and merged
as `6fee7db`. Same recheck as above; no `mcp` launch flag changed:

- DeckCraft v0.7.0: a standalone `render-transition` subcommand; MCP docs and
  tools unchanged. Card unchanged.
- PdfCraft v0.8.0: a standalone `batch` subcommand and a password hint;
  `--root` and `--compact` unchanged; MCP docs unchanged. The release now
  publishes `pdfcraft-cli-0.8.0-linux-x86_64.tar.gz`, the manifest's preferred
  Linux asset name, which the Linux runner installed.
- VectorCraft v0.11.0: `command_run` and batch steps refuse unknown parameter
  keys (naming the nearest key); `command_batch` is capped at 256 steps and
  8 MiB of kept results, `atomic: true` makes a batch one undo step and a
  failing atomic batch restores documents but not files already written; one
  request line at most 16 MiB; `add_text` and the text commands report
  `overflow`; `links.list` notes images too large to decode; an older native
  file opens as `[Converted]` and a path-less save answers with a suggested
  name; `script.check` and `shortcutSet.read` read files under the read root
  without running them; new resources and 3D effect parameters. Launch flags
  unchanged (`--headless`, both roots).

## Release-tag recheck of the seven apps moved by pull request #4 — 2026-10-16

The scheduled run 38717981671 moved CADCraft to v0.7.0, EffectCraft to v0.10.0,
FilmCraft to v0.8.0, GridCraft to v0.7.0, LightCraft to v0.8.0, PhotoCraft to
v0.9.0 and SoundCraft to v0.7.0, verified on the three runners and merged as
`f49ce1e`; run 38883983466 changed only the review date (`5fc911a`). Same
recheck as above. Every catalog launch is still accepted, every smoke tool
still exists without required parameters, no tool was removed or renamed, and
every release keeps the three asset names the manifest expects:

- CADCraft v0.7.0: `mcp` adds `--lazy` and `--launch`, both only with
  `--connect` (`--launch` opens the desktop app on macOS); still no root flag.
  New `find_text` tool, `render` takes a `window`, and `inspect_drawing`
  reports `skipped` records. New AutoLISP: `(expr)` in `command_line` or
  `script`, `execute lisp` and `appload` run code whose `open`, `write-line`,
  `load` and `findfile` use the file system without a root check, so the card
  and the safety list treat it as a script.
- EffectCraft v0.10.0: CLI parser, MCP tools and `docs/mcp.md` unchanged; new
  engine commands only. Card unchanged except its recheck date.
- FilmCraft v0.8.0: CLI parser, MCP tools and `docs/agents.md` unchanged; one
  new engine command (`edit.rippleDeleteHead`). Card unchanged except its date.
- GridCraft v0.7.0: `mcp` still takes only `--connect`, `--in` and `--sample`;
  tools unchanged; `set_cell` accepts numbers and booleans and malformed
  `oneOf` arguments return -32602. Save now refuses an unknown extension,
  sheet names XLSX cannot hold, CSV/TSV over 512 MiB and HTML over 100,001
  rows. The card's "legacy .xls is refused" was wrong at both tags: BIFF8
  imports partially, and XLS, XLSB and ODS are all import-only.
- LightCraft v0.8.0: `mcp` flags and helper tools unchanged; `export` gains
  `rendereddng`, a linear 16-bit float DNG with the edit baked in.
- PhotoCraft v0.9.0: `mcp` parser and root semantics unchanged; the same 25
  tools. `doc_save`/`doc_export` take `dpxBits`, `doc_inspect` reports an
  adjustment layer's `{kind, params}`, `.kra`/`.krz` open import-only, and an
  `.ora` save that would lose content writes a copy and leaves the document
  unsaved (a path-less save refuses).
- SoundCraft v0.7.0: `mcp` adds `--automation-read-root DIR` and
  `--automation-write-root DIR` (existing folders, refused with `--connect`;
  the open session, plug-in loading and a `--connect` app are not covered).
  Other unknown `mcp` flags are still ignored, and `bounce_mix` has no
  replace guard. Tools unchanged. The catalog now launches SoundCraft with
  both roots (`read_write`), as 1.5.0 did for WordCraft, after local binary
  acceptance of the pinned 0.7.0 (see [verification](verification.md));
  because 0.6.1 ignored the root flags, `preflight` refuses a SoundCraft pin
  below 0.7.0.

Source review only; the seven new binaries ran only in the workflow's verify
jobs, not on a developer machine.

## Release-tag recheck of VectorCraft, moved by pull request #6 — 2026-10-16

The hand-triggered run 38932488545, the first with the split release workflow,
moved VectorCraft to v0.12.0 (tag commit `8bc6532`), verified it on the three
runners with the confined launch and merged #6 as `b7e243f`. Same recheck:

- The `mcp` parser and `crates/engine/src/file_access.rs` are unchanged:
  `--headless` and both roots keep their semantics; no new attach or listener
  flag. The same 32 tools; `doc_inspect` still needs no argument. The three
  manifest assets are published and match `SHA256SUMS.txt`.
- New: `list_commands`/`command_list` take `query`, `menu` and `brief`;
  `draw_path`/`draw_shape` take `dash`, `cap`, `join`, `opacity`, `name` and
  `effects` and may be `command_batch` steps (the reply adds `created`);
  `add_text` takes `vertical`; `export` adds `ai` (legacy per-artboard with
  `options.aiVersion: "7"`).
- Correction: the 2026-10-14 entry above and the card said a failing
  `atomic` `command_batch` restores the documents. The v0.12.0 docs describe
  the tool as an undo group only (`edit.undoGroup.begin`/`end`) whose steps
  that ran stay applied; the rollback that keeps the disk as written belongs
  to the engine command `command.batch` run through `command_run`. The card
  now says so.

## No pin moved for 1.5.3 — 2026-10-17

`config/releases.json` and `config/signatures.json` are unchanged since 1.5.2
(no release-workflow merge in between), so no card was due for a recheck and
every card is unchanged. 1.5.3 changes only Storytold's own `setup` and
`doctor` logic, which reads the host CLIs' documented `mcp add`/`get`/`remove`
behaviour already cited above.

## Release-tag recheck of all thirteen apps, moved by pull request #7 — 2026-10-18

The scheduled run 39116490412 found new releases of all thirteen apps and
failed while signing (a transient Rekor `409`, fixed in `e1e0781`); the
hand-triggered run 39167465003 signed all 39 archives, verified them on the
three runners and merged #7 as `37889e2`. Same recheck as above, between the
old and the new tag of each repository. Every catalog launch is still
accepted, every smoke tool still exists without required parameters, no tool
was removed or renamed, and every release keeps the three asset names the
manifest expects plus `SHA256SUMS.txt`:

- CADCraft v0.8.0 (`714111d`): `mcp` parser, MCP tools and `docs/mcp.md`
  unchanged (only `--connect` with `--lazy`/`--launch`, no root flag, unknown
  arguments refused; the same 12 headless tools). New
  `crates/engine/src/doc_path.rs`: a path stored in a drawing (xrefs loaded on
  `open` or reload, data links on `DATALINKUPDATE`) resolves beside it and is
  followed only on this computer or the drawing's own share, otherwise the
  xref stays Unresolved ("not opened"); paths given to `XATTACH`, `-XREF Path`
  or `DATALINK` are used as given; xref reads are capped at 1 GiB in total.
  Card adds the stored-path rule.
- DeckCraft v0.8.0 (`22db926`): `mcp` adds `--automation-read-root DIR` and
  `--automation-write-root DIR` (`apps/deckcraft-cli/src/automation_args.rs`;
  existing folders, each once, refused with `--connect`, the whole process
  confined; not covered: path-less commands, the font scan, the recovery
  folder and the desktop app). Plain `mcp` still starts unconfined and other
  unknown options are still refused. The same 25 tools; every tool refuses an
  argument outside its schema; `export` adds `gif` (`width`,
  `secondsPerSlide`, `loop`) and PDF `paper`/`orientation` for notes and
  handouts; `pointer` adds `tripleclick`/`contextclick`. Card corrected: the
  roots exist, but the catalog does not pass them.
- DesignCraft v0.9.0 (`7cb8b12`): the same two root flags with the same rules
  (`docs/mcp.md`, "Confining file access"; linked files a document names are
  checked too); plain `mcp` unchanged and unconfined. New `ime` tool (25 to
  26); an unknown tool argument or `execute`/`batch` params key is JSON-RPC
  -32602, and `batch` checks every step before the first runs; `new_document`
  adds `intent`, `units`, `startPage`, `slug` and `primaryTextFrame`; new
  engine command `file.exportPptx`. Paths stored in documents (links, data
  sources, book chapters, IDML package links) are followed only on this
  computer or the document's share, otherwise missing with the reason in
  `links.list`/Preflight; images inside SVGs are read only from `data:` URLs.
  Card corrected like DeckCraft's and adds the stored-path rule, PowerPoint
  export and the -32602 refusal.
- EffectCraft v0.11.1 (`2a01226`; there is no v0.11.0 tag): `mcp` parser and
  `crates/automation/src/confine.rs`, `tools.rs` and `backend.rs` unchanged, so
  both root flags keep their semantics (scripts, `control`, `ui_*` and
  `script_ui` still refused while confined); the same 36 tools and 382 engine
  command ids; `docs/mcp.md` unchanged. New: a footage path stored in a
  project resolves beside it and is followed only on this computer or the
  project's own share, otherwise it is marked missing unread
  (`file.findMissing`); a non-Unicode argument is a usage error; the bridge
  (not used here) no longer replays a mutation whose reply was lost. Card adds
  the stored-path rule.
- FigCraft v0.7.0 (`47438dd`): `mcp` adds `--automation-read-root DIR` and
  `--automation-write-root DIR` (repeatable, existing folders, refused with
  `--attach`; `crates/engine/src/file_access.rs` checks every engine file
  access, the app's own preference, recovery, plug-in and font folders
  excepted); plain `mcp` unchanged and unconfined. The same 18 tools; `batch`
  steps reference earlier results with `{"$step": n}`; `save_file` to a `.fig`
  path writes an export copy and leaves the document unsaved; `set_properties`
  returns `warnings`; `.fig` export now writes variables and shared styles,
  and the example documents were opened in other software. The release also
  ships `figcraft-server-*` tarballs, not used here. Card corrected (roots
  exist but are not passed; the `.fig` claim) and adds `$step`, the `.fig`
  copy and `warnings`. The 2026-10-14 rows above that say FigCraft has no
  file-root flag describe v0.5.1/v0.6.0.
- FilmCraft v0.9.0 (`4a69a03`): CLI parser, the 17 MCP tools
  (`crates/automation` identical) and `docs/agents.md` unchanged; `mcp` still
  takes only `--bridge`, `--project`, `--demo` and `--data-dir`. New
  (`docs/project-files.md`): media and proxy paths stored in a project,
  template or interchange file are followed only on this computer or the
  document's own share, otherwise they count as missing and render the
  offline slate; scratch folders named in a project are used only inside its
  folder or when chosen locally; Edit Original opens only media files. Card
  adds the stored-path rule.
- GridCraft v0.8.0 (`823c565`): `apps/gridcraft-cli`, `crates/mcp`,
  `docs/mcp.md` and `docs/cli.md` unchanged (`--connect`, `--in`, `--sample`;
  21 tools). Formulas over Excel's 8,192 characters or past 256 postfix
  nesting levels are now parse errors (an opened cell keeps its formula text
  and cached value); the `--connect` control channel closes on a malformed
  line. Card adds the formula limit.
- LightCraft v0.9.1 (`4f0b110`; 0.9.1 only fixes 0.9.0's web build): `mcp`
  flags unchanged (`--compact` accepted, unknown options refused; stdio now
  shuts down on an output failure); the same 17 compact tools. `export` gains
  `destinationMode` (`sameAsOriginal`) and lossy DNG; new `slideshow.*`,
  `print.*` (`print.exportPdf`) and `merge.hdrBatch` commands are reachable
  through `command_run`; merges write beside the first source photo. Card
  adds the writes into photo folders, settings-folder slideshow templates,
  the background `slideshow.export` and the overwriting `print.exportPdf`.
- PdfCraft v0.9.0 (`645016a`): `--root` (once, with a value) and `--compact`
  unchanged, `resolve_in_root` the same logic with clearer messages, unknown
  options refused, no connect flag. New `--automation-read-root` and
  `--automation-write-root` (`apps/pdfcraft-cli/src/automation_args.rs`) set
  separate read and write folders on top of `--root`; neither covers a
  `doc_print` printer job or a Keychain/Windows-store `sign_document`
  identity. Tools 163 to 170 (`text_word_count`, `page_transition_set`,
  `xfa_to_static`, four accessibility tools), nothing removed; the compact
  core and `doc_inspect` unchanged; `doc_flatten` of XFA fields removes the
  XFA. Card records the new flags (not passed), the XFA-removing edits and
  what roots do not cover.
- PhotoCraft v0.10.0 (`8407d9c`): `mcp` parser and root semantics unchanged
  (unknown flags still refused; roots apply only without `--bridge`);
  `crates/automation/src/workspace.rs` only tightens: `edit.keyboardShortcuts`
  and `brush.presets.importImage` paths are refused, stored Displace and Color
  Lookup smart-filter paths are re-checked at render time, and paths stored in
  a document are followed only locally or on its own share. The same 25 tools
  (`command_list` `filter` also matches keywords); `docs/mcp.md` unchanged.
  Card unchanged except its recheck date.
- SoundCraft v0.8.0 (`2578ea6`): no diff under `apps/`, `crates/automation/`
  or `docs/`; `crates/engine/src/file_access.rs` changed only in a test. Roots
  must exist, each flag once, refused with `--connect`; other unknown `mcp`
  flags are still ignored; still not covered: the open session, plug-in
  loading and a `--connect` app. New (`crates/engine/src/io.rs`): stored
  source and movie paths resolve through `craft-docpath`, so ones on another
  computer, a device or a URL are reported missing ("not opened"). The same
  17 tools; `bounce_mix` still has no replace guard. Card adds the stored-path
  refusal.
- VectorCraft v0.13.1 (`904f0fe`): the `mcp` parser and
  `crates/engine/src/file_access.rs` byte-identical; only unconfined headless
  sessions now keep PDF presets, ICC profiles and plug-ins beside the
  preferences. The same 32 tools; `doc_inspect`/`inspect_document` gain
  `ids`, `kind`, `limit` and `offset`; `command_batch` code and schema
  unchanged. The stdio server now honours `notifications/cancelled` (a queued
  call is dropped; a running export, flatten, bake or render stops at its
  next checkpoint and writes nothing), sends progress, and refuses other
  engine requests behind a call that has run 2 s with -32003. Card adds
  scoped inspection, the busy and cancel behaviour and that a confined server
  keeps no stores; "may not support active cancellation" is gone from the
  card and from the acceptance scenario.
- WordCraft v0.8.0 (`f2e15cf`): the `mcp` branch, `automation_args.rs` and the
  root checks unchanged (`file_access.rs` only exempts the desktop-only
  recovery store in a test); new reads go through `check_read`. The same 16
  tools; `get_text` now omits tracked deletions; new `file.rename` checks the
  file against both roots and the new name against the write root. Card adds
  both.

Four apps now ship root flags the catalog does not pass: DeckCraft 0.8.0,
DesignCraft 0.9.0 and FigCraft 0.7.0 (`--automation-read-root` and
`--automation-write-root`) and PdfCraft 0.9.0 (the same two on top of
`--root`). Their catalog launches are unchanged (plain `mcp`, `os_only`;
PdfCraft `single_root`); adopting the flags is a reviewed catalog change with
a local `preflight` and `probe`, as it was for SoundCraft and WordCraft. The
README legend, the `setup` messages and the safety list now say these apps
are launched without root flags rather than that they have none. Six releases
also follow paths stored in documents only on this computer or the
document's own share (CADCraft xrefs, DesignCraft links, EffectCraft footage,
FilmCraft media, PhotoCraft smart filters, SoundCraft sources). Source review
only; the thirteen new binaries ran only in the workflow's verify jobs, not on
a developer machine.

## DeckCraft, DesignCraft, FigCraft and PdfCraft launched with their root flags — 2026-10-18

A reviewed catalog change after the recheck above. Source, at the pinned tags:

- DeckCraft v0.8.0 and DesignCraft v0.9.0 add
  `apps/<app>-cli/src/automation_args.rs` in that tag (no earlier tag has
  it). Each flag is given once (`--flag DIR` or `--flag=DIR`), the folders
  must exist, `--connect` with them is an error and the whole server process
  is confined. Their `docs/mcp.md` ("Confining file access") lists every
  read and write command; DesignCraft also checks the files a document
  names. Not covered: path-less commands, the system font scan, the recovery
  folder and, for DesignCraft, `file.print` to the system spooler.
- FigCraft v0.7.0 adds the flags (commit `ac4b98d`, first in that tag): each
  repeatable, existing folders, refused with `--attach`. Every engine file
  access goes through `crates/engine/src/file_access.rs` (enforced for the
  engine by `clippy.toml`); the app's own preference, recovery, plug-in and
  font folders are excepted.
- PdfCraft v0.9.0 takes the root flags out of the `mcp` arguments before
  `validate_options` sees the rest (`apps/pdfcraft-cli/src/main.rs`,
  `automation_roots`), so their order next to `--root` and `--compact` does
  not matter. With `--root` both apply: a path must be inside `--root` and
  inside the matching automation root (`docs/mcp.md`). Without `directories`,
  `text_font_files` then searches the read root instead of the installed
  fonts.
- Older releases of all four refuse unknown `mcp` options (DeckCraft v0.7.0
  `unknown mcp option`, FigCraft v0.6.0 `unknown option`, and the same for
  DesignCraft v0.8.0 and PdfCraft v0.8.0), so an older pin would fail to start
  rather than run unconfined.

Decision: DeckCraft, DesignCraft and FigCraft move from `os_only` to
`read_write` with the same two flags as WordCraft and SoundCraft. PdfCraft
moves from `single_root` to `read_write`: it keeps `--root {work}` as an
extra fence and adds `--automation-read-root {work}` and
`--automation-write-root {outputs}`, so it reads the workspace and writes
only `outputs/`, no longer `inputs/` or `receipts/`. `single_root` is gone
from the catalog. `ROOTS_SINCE` in `storytold_tools/catalog.py` now names
DeckCraft 0.8.0, DesignCraft 0.9.0, FigCraft 0.7.0 and PdfCraft 0.9.0, so
`preflight` refuses an older pin before anything starts and `setup`
upgrades it. Local acceptance, including a denial outside the read root for
all four and outside the write root for PdfCraft, is in
[verification](verification.md). Nine apps now run with roots; FilmCraft,
LightCraft, GridCraft and CADCraft remain user-wide.

## Release-tag recheck of all thirteen apps, moved by pull request #8 — 2026-10-21

Upstream published new releases of all thirteen apps between 2026-10-20 14:34
and 2026-10-21 07:46 UTC. The hand-triggered run 39574679446 on `656515b` (the
first with the refresh retries and the run summaries) pinned, signed and
verified them on the three runners and merged #8 as `658e26f`. Same
recheck as above, between the old and the new tag of each repository, by `git
diff` and `git show` on blob-less clones; nothing from upstream was built or
run. Every catalog launch is still accepted with unchanged meaning, every smoke
tool still exists without a required parameter, no tool was removed or
renamed, and every release keeps the three asset names the manifest expects
plus `SHA256SUMS.txt`. Five ranges span a version that was never tagged or
released (CADCraft 0.9.0, EffectCraft 0.12.x, PdfCraft 0.10.0, PhotoCraft
0.11.0, SoundCraft 0.9.x), so each is one move. The releases also ship Arch
`linux-{x86_64,aarch64}.pkg.tar.zst` packages and, for DesignCraft, FigCraft,
GridCraft, PhotoCraft and SoundCraft, a new `freebsd-aarch64.tar.gz`; none is
used here.

- CADCraft v0.10.0 (`e86eacf`; no v0.9.0 tag or release, `b23d362` "Release
  0.9.0" only bumps the version inside the range): `mcp` parser unchanged
  (`parse_mcp_args`: only `--connect HOST:PORT`, once, with `--lazy`/`--launch`
  that need it; anything else `mcp: unknown argument`; plain `mcp` headless,
  no root flag); `crates/engine/src/doc_path.rs`, the AutoLISP file
  functions, `crates/mcp/src/server.rs` and `backend.rs` unchanged. The same
  12 headless tools (15 definitions with the bridged `screenshot`,
  `ui_inspect`, `ui_click`); the one schema change is `query_entities`
  `selected?: boolean` (the current selection in the active space, combined
  with `type`/`layer`/`window` before paging; an empty selection returns no
  entities; `"true"` or `1` is -32602). New engine commands through
  `execute`: `shapes` (closed polylines, circles, full ellipses and closed
  splines: perimeter, area, centroid, winding, first self-intersection,
  `tolerance?`), BURST, TXT2MTXT, BREAKLINE, MOCORO, ALIASEDIT (reads a
  `.pgp`), HATCHEDIT add/remove; `dist`/`id`/`list` report Z. `docs/mcp.md`
  adds the `shapes` and `selected` rows, `docs/customization.md` is new. New
  write: system variable `AUDITCTL` (default 0) at 1 makes `audit` and
  `recover` write `<drawing>.adt` beside a drawing that has a path (an
  unsaved drawing writes nothing). `open` is described as DXF, but at both
  tags the reader takes DXF (ASCII or binary) and DWG by content and
  SVG/SVGZ by name; an imported SVG leaves the drawing without a file name,
  and the result's `warnings` now name what the import left out. Card
  corrects `open`'s formats and adds `selected`, `shapes` and the `.adt` log.
- DeckCraft v0.9.0 (`fe510bd`): the `mcp` branch of
  `apps/deckcraft-cli/src/main.rs`, `automation_args.rs` and
  `crates/engine/src/file_access.rs` unchanged (`--connect`, `--sample`, both
  root flags once, existing folders, refused with `--connect`, the whole
  process confined; other options `unknown mcp option`); `crates/mcp`
  byte-identical, so the same 25 tools and schemas; `docs/mcp.md` unchanged.
  Engine: `file.open`/`file.openBytes`, and so `open_presentation`, return
  `lostSlides` next to `damagedMedia` (an unreadable `.pptx` slide is left out
  and the title gets "(Repaired)"); `file.export` and `file.render` take
  `transparentBackground` (PNG only), which the MCP `export` and
  `render_slide` schemas do not, so a transparent PNG goes through
  `run_command file.export`; `shape.move`, `shape.resize` and
  `shape.setBounds` clamp sizes to 0..15,840 pt and positions to ±100,000 pt;
  `comment.delete` refuses an `index` that is not a non-negative integer
  (0.8.0 cleared the slide's comments instead); `shape.editPoints` is
  undoable; native saves keep imported chart parts. Card adds `lostSlides`,
  the transparent-PNG route, `comment.delete` and the geometry limits.
- DesignCraft v0.10.0 (`15a2f3c`): the `mcp` branch of `main.rs`,
  `automation_args.rs`, `crates/engine/src/file_access.rs` and `io.rs`
  unchanged (`--connect PORT`, `--sample`, both root flags; unknown options
  refused); `crates/mcp` byte-identical, the same 26 tools. `docs/mcp.md`
  adds that `story.replaceRange` refuses an offset inside a character, an
  `end` past the story or `start` after `end`, with the story length in bytes
  and the story unchanged (0.9.0 snapped and clamped; `cmd/text.rs`);
  `docs/agents.md` adds `\u000b` as a forced line break in text parameters
  and a "Parent pages" section. New commands `layout.parents.delete {id}`
  (the parent's shared artwork and its assignments go in one undo step, local
  overrides stay as ordinary items) and `font.reload {}` (rescans the
  installed font folders, fixed paths the roots do not check, without an
  undo step). `file.package` writes the packaged `.designcraft` and IDML
  links relative to the package (`Links/<name>`), resolved beside the
  document on open through the same `io` checks; `links.copyTo` keeps full
  paths. `links.list` lists anchored and inline images; `object.stroke`
  refuses malformed `type` objects; the IDML, DOCX, RTF, Tagged Text and ASE
  importers clamp non-finite values. Card adds the `replaceRange` refusal,
  `\u000b`, the relative package links, `layout.parents.delete` and
  `font.reload`.
- EffectCraft v0.13.0 (`de3fec2`; no v0.12.x tag): the `mcp` branch of
  `apps/effectcraft-cli/src/main.rs` unchanged (`--autosave | --bridge PORT`,
  both root flags repeatable, unknown options refused); the only parser
  change is the render-only `--progress` flag, which `mcp` accepts and
  ignores like `--gpu`. `crates/automation` tree-identical (`tools.rs`,
  `confine.rs`, `backend.rs`): the same 36 tools and 382 engine command ids,
  scripts, `control`, `ui_*` and `script_ui` still refused while confined;
  `docs/mcp.md` unchanged. `docs/agents.md` adds variable-font named
  instances and `render --template --values` filling a Media Replacement
  control. Behaviour: a saved project records each comp's current time
  (`compTimes`, editor state older versions ignore) and reopens there;
  `anim.applyPreset` and the property and link paste commands resolve
  `effects/<match name>[#n]/<property>` paths; `keys.delete` returns the
  number of keys removed; a pasted mask or shape path on Position becomes a
  2 s motion path; the Linux/BSD font scan honours `FONTCONFIG_PATH`, still
  outside the roots. Card adds the saved comp times, the `keys.delete` count
  and the match-name effect paths.
- FigCraft v0.8.0 (`594dc8c`): `apps/figcraft-cli/src/args.rs`
  byte-identical; the `mcp` branch keeps `[--attach PORT]` and the two
  repeatable root flags, refuses positionals and `--attach` with roots, and
  builds the same `file_access::Roots`. New: `info`, `export`, `convert`,
  `render` and `run` take the same two flags (`docs/cli.md`, "Confining a
  run"; not used by the catalog). `crates/engine/src/file_access.rs` changes
  only a refusal's wording: a path whose existing prefix resolves into a
  root gets the OS reason (`automation path rejected: <path>: <why>`) and a
  link leading out of a root is outside; the roots' meaning and the
  uncovered folders are unchanged. `crates/mcp` identical except one
  `create_node` description: the same 18 tools, the 32 MiB line limit and
  -32600. New engine commands behind `run_command`: `text.missingFonts`,
  `text.rescanFonts`, `text.loadFont {path | data}` (read through
  `file_access::read_capped`, so confined), `text.refit`, `pref.uiScale`,
  `pref.startOnHome`. Behaviour: an effect object with a key the effect does
  not read is refused naming the keys it takes (#851); an explicit edit of a
  variable-bound field detaches that field's variable; `get_node` and
  `inspect_document` carry `pluginData`; `vector.create` and `create_node
  {type: vector}` scale the path to `width`/`height` and refuse an empty path
  or a size of 0; `variable.import` also reads top-level `variables` and
  `variableCollections`. The release ships the `figcraft-server-*` tarballs
  again. Card adds the CLI-subcommand roots, the font commands, the
  effect-key refusal, the variable detaching, `pluginData` and the vector
  sizing rule.
- FilmCraft v0.10.0 (`cdf43fd`): the `mcp` branch of
  `apps/filmcraft-cli/src/main.rs` unchanged, still refusing every option but
  `--bridge`, `--project`, `--demo` and `--data-dir` (exit 2), so a root flag
  is still rejected; the CLI's `exec` refuses dotted params past 64 nesting
  levels and `render` a non-finite `--seconds`/`--scale`. `crates/automation`:
  the same 17 tools; the one code change is `doc_inspect`, which now inspects
  the sequence `project.activeSequence` names, so its pair is consistent in
  bridge mode too (#1477). The same 413 engine command ids. `file.exportMedia`
  without `wait` returns `{job, path, poll: "jobs.list", cancel:
  "jobs.cancel"}` (`docs/agents.md`: `export.queue.list` lists the Export
  Queue only); `timeline.setTrack` takes `label` and `sequence.inspect` tracks
  report it; `effects.toggleAnimation` creates a missing parameter from its
  default; a `.3dl` LUT with an input mesh outside 2-256 values is refused.
  `docs/project-files.md` unchanged, so the stored-path rule stands. Card
  adds the export-without-wait result and the consistent `doc_inspect` pair.
- GridCraft v0.9.0 (`a2cc4b4`): `apps/gridcraft-cli`, `crates/mcp`,
  `docs/mcp.md` and `docs/cli.md` byte-identical (`--connect`, `--in`,
  `--sample`, each with a value; no root flag; the same 21 tools,
  `inspect_workbook` with an empty schema). Engine: `execute_command
  file.open {csvAsText: true}` keeps every CSV/TSV/TXT field as text
  (`open_workbook` has no such parameter); signed and doubly-`$`
  whole-row/column ranges (`+1:+3`, `$$A:$$C`) are refused; defined and table
  names are at most 255 characters; `insert.pivotTable` refuses an unknown
  value-field `func`; custom numeric filters match numbers only, hiding
  blank and text rows; `range.fill` gives each cell the number format typing
  there would; `.xls` import skips dialog sheets and reads WINDOW2.
  Pre-existing and missing from the card: `save_workbook`/`file.save` with a
  `.pdf` path is a print of the active sheet (Page Setup applies) that
  leaves the workbook's own file and unsaved state untouched, while the
  unknown-extension error names only .xlsx/.csv/.tsv/.json/.html. Card
  corrects the save sentence and adds the CSV-as-text open, the new refusals
  and the filter rule.
- LightCraft v0.10.0 (`a2a4138`): `apps/lightcraft-cli`, `crates/mcp` and
  `docs/mcp.md` byte-identical (`mcp [--connect [ADDR]] [--demo] [--library
  DIR] [--compact] [--headless] [FILES…]`, other options refused; no root
  flag); the same 17 compact tools. Behaviour: opaque 8-bit PNG, TIFF and
  WebP exports are written without an alpha channel, real transparency is
  kept (#1670); `photo.rename` refuses a `start` out of range; `print.set
  page` gains `pageNumbers`, `pageInfo` and `cropMarks`; slideshow and print
  colour strings must be six hex digits; model downloads honour the connect
  timeout and Cancel; the denoise cap rises to 110 MP; a catalog snapshot
  with an out-of-range `seq` is refused as corrupt; the new "last merge
  settings" in prefs.json are written only by the desktop merge dialog. Card
  adds the alpha-free exports; otherwise unchanged except its recheck date.
- PdfCraft v0.10.1 (`b77d570`; no v0.10.0 tag): `automation_args.rs`,
  `crates/automation/src/file_access.rs` and `mcp.rs` byte-identical; in
  `main.rs` the `mcp` function, `automation_roots`, `validate_options` and
  `MCP_OPTIONS` are untouched (`--root` once with a value, `--compact`, both
  root flags, unknown options refused before any file is read; `--root`
  applies on top of both roots), and `resolve`, `resolve_in_root` and
  `check_roots` in `crates/automation/src/lib.rs` are outside every hunk.
  Tools 170 to 171: `page_reverse`, nothing removed or renamed;
  `page_duplicate` takes `at`; `doc_set_info` also sets custom properties,
  listed by `doc_info` under `custom`; `form_fields` and `form_set_props`
  handle push-button captions; `doc_export_office` reports `truncated`. The
  compact core is the same fifteen tools plus `tool_search` and `tool_call`;
  `doc_inspect` still has no required parameter. Saving
  (`crates/platform/src/staging.rs`, every tool write): a read-only target is
  refused before anything is written, a replaced file keeps its Unix mode
  and macOS/Windows creation date; a file whose cross-reference index had to
  be rebuilt on open is written in full even without edits (#1937);
  `doc_close` refuses a new or recovered document with unsaved state even
  after undo unless `discard_changes` (#2346). Redaction: `redact_apply`
  removes the replies of the annotations it removes (#2659), clears image
  pixels under the marks (#3368), walks the structure tree from the parent
  and ID trees too and refuses, with the document unchanged, a tagged PDF
  whose tree it cannot clean (#2447, #3302); `text_edit` refuses a rewrite
  that would remove text drawn as a clipping path (#3447); in AES-256 files
  `/Perms` limits an edited `/P`. `docs/mcp.md` adds "Install and register".
  Card completes the compact-core list, corrects the save sentence (full
  rewrites, read-only refusal, `doc_close`) and adds the redaction and
  `text_edit` refusals.
- PhotoCraft v0.11.1 (`46e538b`; no v0.11.0 tag, `cd79a5a` "Release 0.11.0"
  is only a commit, and 0.11.1 adds the FreeBSD build fix):
  `apps/photocraft-cli` byte-identical (`mcp` takes `--bridge`,
  `--control-token`, `--control-token-file` and the two root flags, any other
  flag `unknown flag` with exit 2; roots apply only without `--bridge`);
  `crates/automation/src/server.rs` identical, the same 25 tools;
  `workspace.rs` changes only how a file inside the write root is replaced
  (the old file's extended attributes are copied through the two open
  descriptors, nothing reaches outside the root); `files.rs` reports open
  warnings for a `.pcraft` as for imports; `docs/mcp.md` adds "Install and
  register", its tool and cancellation sections unchanged. Engine, through
  `command_run`: `file.saveACopy` whose `path` is the document's own file is
  refused unless `overwrite: true` (#7437); a `.pcraft` with out-of-range
  numbers is refused on open (#6862); `edit.presets.exportImportPresets`
  moves tool presets as in-memory `data`, no path; `filter.cameraRaw`
  exposure is clamped to -5..5. Card adds the `file.saveACopy` guard.
- SoundCraft v0.10.0 (`e894076`; no v0.9.x tag or release):
  `apps/soundcraft-cli` (`main.rs`, `automation_args.rs`),
  `crates/engine/src/file_access.rs` and the confinement section of
  `docs/mcp.md` unchanged (`--connect`, `--demo`, both roots once, existing
  folders, refused with `--connect`; other unknown `mcp` flags still ignored).
  The same 17 tools; `batch` takes at most 1000 `calls` (`maxItems`) and
  refuses a longer list as `isError` before any call runs (0.8.0 ran the
  first 1000 and dropped the rest silently). `crates/engine/src/io.rs`: a
  session backup (`Backups/<name> backup <n>`) is checked against the write
  root and never replaces an existing entry or follows a link
  (`create_new`); a `.scraftz` bundle whose sources share one file loads them
  all; `automation.clear` with an unknown `param` is refused instead of
  clearing every lane. The 0.8.0 stored-path rule is unchanged; `bounce_mix`
  still has no replace guard. Card adds the batch limit and the backup rule.
- VectorCraft v0.14.0 (`ad05669`): the `mcp` parser,
  `crates/engine/src/file_access.rs` and `crates/mcp/src/server.rs` (the
  -32003 busy refusal after 2 s, `notifications/cancelled`, the 256-step,
  8 MiB and 16 MiB limits) byte-identical; a confined server still keeps no
  preset, profile or plug-in store. The same 32 tools; `export` passes
  `scale` to `document.export` only for a raster format
  (`named_export_params`), so it no longer resizes a DXF; `open_file` also
  reads Targa. `crates/mcp/src/intake.rs`: a parse error or overlong line now
  waits for room in the 64-line queue instead of being answered at once.
  `docs/mcp.md` (+352 lines): `document.export`, `serialize`,
  `exportSelection` and `exportForScreens` refuse a `.ait` path or `format:
  "ait"` naming `file.saveAsTemplate` (which refuses `aiVersion: "7"`);
  `edit.clearHistory` removes every undo and redo step; `SOURCE_DATE_EPOCH`
  pins the time PNG, PDF, EPS, `.ai`, zip and `.vectorcraft` output records,
  an encrypted PDF still differs (`crates/doc/src/metadata.rs`); a PDF
  export, `.ai` save or `file.print` leaves out an undecodable image and
  warns once; a document on a Windows mapped drive finds its links on the
  share behind it (`document_path_with`/`share_path`); numbers given as text
  are refused by the Object-menu, blend, envelope, mesh and `path.*`
  commands; `object.objectsOnPath.*`, `object.path.simplify`, library groups
  and exporter plug-ins (`format: "plugin.<id>"`, unreachable confined) are
  new. Card adds the raster-only `scale`, the `.ait` refusal, Targa,
  `SOURCE_DATE_EPOCH`, `edit.clearHistory`, the undecodable-image warning and
  the stored-link rule.
- WordCraft v0.9.0 (`2e6db0b`): the `mcp` branch of
  `apps/wordcraft-cli/src/main.rs` (`--connect`, `--author`, both roots
  through `automation_args.rs`; roots or `--author` with `--connect` refused;
  other options refused by `validate_options`), `automation_args.rs`,
  `crates/engine/src/file_access.rs` and `crates/mcp/src/server.rs`
  unchanged. The other CLI subcommands gain `--password`, `--password-file`,
  `WORDCRAFT_PASSWORD` and `run --script FILE|-` (a JSON job file, at most
  4 MiB; `docs/mcp.md` "Scripts from the command line"); neither reaches
  `mcp`. The same 16 tools; `open_document` gains an optional `password`
  forwarded to `file.open` and says a protected file without it fails asking
  for one; `file.open`, `file.save`, `file.saveAs` and `file.encrypt` take
  `password` at this tag, and a document opened with one is saved with it
  again (`file.encrypt` with null or "" saves it plain).
  `crates/engine/src/io/safe_save.rs`: where the folder refuses the temporary
  file a safe save needs (macOS privacy-protected or read-only folders), a
  new file is written directly (removed again on failure) and an existing
  file is left unchanged with an error saying so; the write-root check
  happens before either. Card adds the password and the save fallback.

No catalog launch, smoke tool or `ROOTS_SINCE` minimum changes: DeckCraft
0.9.0, DesignCraft 0.10.0, FigCraft 0.8.0 and PdfCraft 0.10.1 are above their
root-flag minimums, SoundCraft still ignores unknown `mcp` flags, and
FilmCraft, LightCraft, GridCraft and CADCraft still ship no root flag. Neither
`skills/craft/SKILL.md`, the workflow references nor
`tests/native/acceptance.json` names a tool these releases changed.
Release-note claims that were not confirmed in source stayed out of the
cards. Source review only; the thirteen new binaries ran only in the
workflow's verify jobs, not on a developer machine.

## Pull request #9 moved eight apps — 2026-10-22, recheck pending

The scheduled run 39762354104 pinned DesignCraft 0.11.0, EffectCraft 0.14.0,
FigCraft 0.9.0, GridCraft 0.10.0, LightCraft 0.11.0, PdfCraft 0.11.0,
PhotoCraft 0.12.0 and SoundCraft 0.11.0, verified them with each app's smoke
tool on the three runners and merged them as `9e54271`. No card has been
rechecked at those tags: the eight cards still carry their 2026-10-21 recheck
dates, and 1.5.5 ships the pins as the workflow verified them. The recheck of
the CLI's `mcp` parser, MCP docs, tool definitions, smoke tool, packaging and
release assets at each new tag is still due.

## Build infrastructure

The workflow uses reviewed full-commit action references:

- [actions/checkout v7.0.1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1): `3d3c42e5aac5ba805825da76410c181273ba90b1`.
- [actions/setup-python v7.0.0](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97): `5fda3b95a4ea91299a34e894583c3862153e4b97`.
- [sigstore/cosign-installer v4.1.2](https://github.com/sigstore/cosign-installer/commit/6f9f17788090df1f26f669e9d70d6ae9567deba6): `6f9f17788090df1f26f669e9d70d6ae9567deba6`, installing cosign v3.1.3 (the release workflow only).
- [actions/upload-artifact v7.0.2](https://github.com/actions/upload-artifact/commit/cf430e030ddbb5b0abf93d22962f4752f3646cd9): `cf430e030ddbb5b0abf93d22962f4752f3646cd9` and [actions/download-artifact v8.0.2](https://github.com/actions/download-artifact/commit/9000827ccba6bdab643e8b6fd33ac0654aef8333): `9000827ccba6bdab643e8b6fd33ac0654aef8333`, carrying the refreshed files from the token-less refresh job to the publish job (release workflow only; reviewed 2026-10-18). Both 2026-10-07 patch releases only retry HTTP 429 responses (honouring `Retry-After`) through `@actions/artifact` 6.3.1; taken after the 2026-10-18 run failed on a transient Sigstore error, so the workflow's other network hand-over is hardened as well. v7.0.1/v8.0.1 (`043fb46d…`/`3e5f45b2…`) were the previous pins.

Each tag resolved to the listed commit when it was reviewed. The CI matrix
(Python 3.11/3.13 on Linux, macOS and Windows, plus the SDK contract job) ran
in full on the 2026-10-16 push of `main` (run 38927511616), and the release
workflow runs daily; none of this was executed locally. The artifact actions
first run with the release workflow after this change. MCP is the only optional direct runtime dependency;
since 2026-10-16 its transitive graph is locked with hashes in
`requirements-probe.lock` (uv 0.13.1, universal resolution, 28 packages; a
strict `--require-hashes --only-binary=:all:` install and `make test-sdk`
passed on macOS arm64; Linux and Windows wheels are hashed but install there
only in CI and on users' machines).
Recheck releases before an intentional upgrade and run both core and SDK/native
acceptance tests.
