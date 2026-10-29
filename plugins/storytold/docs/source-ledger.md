# Source ledger and verification scope

Review dates: **2026-10-12 to 2026-10-23** (each section names its own). The integration uses the attached project plan as its
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

## Release-tag recheck of the eight apps moved by pull request #9 — 2026-10-23

Upstream published new releases of eight apps between 2026-10-21 18:12 and
19:57 UTC, after that day's scheduled run. The scheduled run 39762354104 on
`44fea38` pinned, signed (24 archives, no retry) and verified them on the three
runners and merged #9 as `9e54271`; 1.5.5 shipped them with this recheck still
pending. Same recheck as above, between the old and the new tag of each
repository, by `git diff` and `git show` on blob-less clones; nothing from
upstream was built or run. Every catalog launch is still accepted with
unchanged meaning, every smoke tool still exists without a required parameter,
no tool was removed or renamed, no root flag appeared for GridCraft or
LightCraft, no range spans an untagged version, and every release keeps the
three asset names the manifest expects, at the manifest's byte sizes, plus
`SHA256SUMS.txt`. EffectCraft, GridCraft and SoundCraft are version-only
releases (the version bump, a `.coderabbit.yaml`, CI moved to shared
`craft-common-actions` workflows); DesignCraft and PdfCraft carry one engine
change each; FigCraft, LightCraft and PhotoCraft several. Several release
notes record that `freebsd-aarch64.tar.gz` was dropped (the emulated build ran
past the shared workflow's 5-hour limit, craft-common-actions#39); nothing
here uses it. All eight repositories have since tagged newer versions
(DesignCraft v0.12.0, EffectCraft v0.15.0 and v0.16.0, FigCraft v0.10.0,
GridCraft v0.11.1, LightCraft v0.12.0 and v0.13.0, PdfCraft v0.12.0 and
v0.13.0, PhotoCraft v0.13.0 and v0.14.0, SoundCraft v0.12.1), which the next
daily run pins; each will need this recheck again.

- DesignCraft v0.11.0 (`4d62a50`): the `mcp` branch of `main.rs`,
  `automation_args.rs`, `crates/engine/src/file_access.rs`, `io.rs`,
  `crates/mcp`, `docs/mcp.md`, `docs/agents.md`, `release.yml` and
  `packaging/` byte-identical to v0.10.0 (`--connect PORT`, `--sample`, both
  root flags; unknown options refused; the same 26 tools, `inspect_document`
  without parameters). Twelve commits, almost all CI (SonarCloud, CodeRabbit,
  `cargo xtask ci`, the shared nix workflow) and licence notices for the PDF
  reader. The one engine change (#876) moves placed-PDF reading from the
  pdfcraft-vendored hayro crates to craft-libs `craft-pdf`
  (`89dcbb3`), with a 512 MiB input bound (`docs/pdf-backend.md`):
  `file.place` (`cmd/file.rs`) and `links.relink`, `links.relinkFolder` and
  `links.update` (`cmd/links.rs`, `reload`) refuse a larger PDF before
  parsing it, as an ordinary error naming the command or the path.
  `file.exportPdf` (`cmd/export.rs`, `rasterize_layered`) now fails, naming
  the placed file and the reason (`PdfRasterError` in `crates/render`:
  missing page, layers not hidden, image decode, unsupported font, truncated
  content), when a placed PDF with hidden layers cannot be rasterized, where
  0.10.0 skipped the item and exported the page as stored; the "exported as
  images" warning is unchanged, and `book.exportPdf` and `file.print` do not
  take that path. No new command (`pdf_page_box` is test-only). No untagged
  version in the range; a v0.12.0 tag already exists upstream. The release
  drops `freebsd-aarch64.tar.gz` (5-hour CI limit, craft-common-actions#39)
  and keeps the three manifest assets plus `SHA256SUMS.txt`. Card adds the
  512 MiB PDF bound on `file.place`/`links.*` and the `file.exportPdf`
  failure on unrasterizable layered PDFs.
- EffectCraft v0.14.0 (`26b4019`; no v0.13.x tag between): ten commits, six
  files, none under `apps/`, `crates/`, `docs/` or `.github/` (all four
  subtrees identical to v0.13.0). The `mcp` branch of
  `apps/effectcraft-cli/src/main.rs` is byte-identical (`--autosave | --bridge
  PORT`, both root flags repeatable, unknown options refused before anything
  runs, `--autosave` with `--bridge` refused); `crates/automation` unchanged
  (`tools.rs`, `confine.rs`, `backend.rs`): the same 36 tools, `doc_inspect`
  with an empty schema, the same 382 engine command ids, scripts, `control`,
  `ui_*` and `script_ui` still refused while confined; `docs/mcp.md` and
  `docs/agents.md` byte-identical. The diff is the version bump (36 workspace
  crates in `Cargo.lock`, no dependency moved), a README that drops its After
  Effects/Adobe comparisons and trademark footnote (306 "built-in" effects;
  parity figures now cite `docs/target-app-parity.md`), a `.coderabbit.yaml`
  that skips Dependabot PRs, a `sonar-project.properties` (its projectKey
  still names craft-launcher) and `packaging/freebsd/package.sh` building
  aarch64 with 16 codegen units and no LTO after the emulated VM ran past its
  5-hour limit; the release nevertheless carries `freebsd-x86_64.tar.gz`
  only. `release.yml` still delegates to `craft-common-actions` at `@main`.
  Card unchanged except its recheck date.
- FigCraft v0.9.0 (`28de91d`): `apps/figcraft-cli` byte-identical (`args.rs`,
  `main.rs`, `files.rs`); the `mcp` branch keeps `[--attach PORT]` and the two
  repeatable root flags, refuses positionals, unknown options and `--attach`
  with roots, and builds the same `file_access::Roots`;
  `crates/engine/src/file_access.rs`, `crates/mcp` (the same 18 tools, the
  32 MiB line limit, -32600, `$step`), `docs/mcp.md`, `docs/cli.md` and
  `.github/workflows/release.yml` are identical too. No version in the range
  went untagged (0.8.0 → 0.9.0 in the release commit). Engine changes behind
  `run_command`: `component.combineVariants` dedupes its ids and refuses,
  naming the reason, variants already in a set (it used to nest a set in a
  set), library copies, components inside an instance and a component with
  one inside it, names the set from the first variant's path before its last
  `/` (else "Component N") and renames bare variants "Property 1=Default",
  "Property 1=VariantN"; `component.addVariant` on a lone main component
  makes it a set of itself and adds the variant in one undo step (#903).
  `file.save`/`file.saveAs` to a new path give an untitled document, or one
  still titled as its old file stem, the new file's stem before writing, and
  `file.open` replaces a stored "Untitled" with the stem (#935).
  `Color::parse_css` refuses `rgb()`/`hsl()` forms with a malformed alpha or
  more than four arguments (#911); `trim_num` prints huge whole numbers
  exactly; SVG export keeps Title Case across styled runs; `ellipse` rings
  keep open subpaths open. Linux window decorations move to the shared
  `craft-window` crate (desktop app only). The release drops
  `freebsd-aarch64` and keeps the three catalog assets plus `SHA256SUMS.txt`.
  Card adds the `combineVariants` refusals and naming, `addVariant` on a lone
  component, the CSS-colour refusal and the save-adopts-filename rule.
- GridCraft v0.10.0 (`2ebdf16`): a CI-only release. Between v0.9.0 and
  v0.10.0 the diff is four files: `.coderabbit.yaml` (new; skips CodeRabbit
  on Dependabot pull requests), `.github/workflows/nix.yml` (the flake check
  now comes from `storytold/craft-common-actions/.github/workflows/nix.yml@main`)
  and the 0.9.0 → 0.10.0 bump in `Cargo.toml` and `Cargo.lock`, made in the
  release commit itself (no untagged version in the range). `apps/gridcraft-cli`,
  `crates/*`, `docs/`, `packaging/` and `.github/workflows/release.yml` are
  byte-identical: `mcp` still takes only `--connect`, `--in` and `--sample`,
  each with a value, no switches, unknown options and extra positionals
  refused (`main.rs:497-499`, `:126`); plain `mcp` opens a blank headless
  session (`main.rs:516`); no root flag. The same 21 tools in the same
  `tools/list` order, `inspect_workbook` with an empty schema
  (`tools.rs:137-143`); nothing added, removed or renamed, no schema change,
  no new command, no new disk write. `file.save`/`file.saveAs` with a `.pdf`
  path is still a print of the active sheet (`cmd/file.rs:107-109`), the
  unknown-extension error still names only .xlsx/.csv/.tsv/.json/.html
  (`io.rs:199`), HTML export still stops at 100,001 rows (`io.rs:409`) and
  CSV/TSV at 512 MiB. Release v0.10.0 (2026-10-21) carries
  `gridcraft-0.10.0-linux-x86_64.tar.gz`, `gridcraft-cli-0.10.0-macos-universal.zip`,
  `gridcraft-0.10.0-windows-x64-portable.zip` and `SHA256SUMS.txt`; its notes
  drop the FreeBSD aarch64 build, which Storytold does not pin. Card
  unchanged but for the date.
- LightCraft v0.11.0 (`ec0cda9`): the `mcp` parser in `apps/lightcraft-cli/src/
  main.rs` is outside every hunk (`mcp [--connect [ADDR]] [--demo] [--library
  DIR] [--compact] [--headless] [FILES…]`, other options refused; no root
  flag); the same 17 compact tools, `doc_inspect` still without a required
  parameter, no property changes. `crates/mcp/src/tools.rs` marks `export`,
  `render_photo` and the bridged `screenshot` `destructiveHint: true` and says
  that `path` replaces an existing file while a catalogued original or its XMP
  sidecar is refused with nothing written (#2152); `docs/mcp.md` calls the
  annotations client hints, not a sandbox. Headless `export` still writes PNG
  for a `path` naming no format, but `bitDepth` is checked against the format
  written (#1966), and `app.export` refuses a depth its format lacks (#1952).
  Engine: `photo.reload` is split into plan/probe/apply (`cmd/reload.rs`; in
  the app `{background: true, count}` unless `wait: true`);
  `metadata.reverseGeocode` takes `maxDistance` and reports `nearestCity`
  (#2242); `crop.aspect` keeps the crop's orientation and takes `orientation`
  (#2253); Constrain Crop tightens the stored crop (#1927); `index`,
  `component` and mask `id`/`ids` must be non-negative integers, refused
  before any change (#2100, #2101); a brush stroke lays at most 2,000,000 dabs
  (#1520); Lightroom import reads `.lrcat` pages on demand up to 16 GiB and
  skips images with missing records under `skipped` (#842, #2230); an
  arriving JPEG/TIFF never reads its raw's shared stem sidecar (#1905);
  downscaling at 2:1 or more uses Lanczos3 (#2012). No new disk write. The
  macOS bundle drops the `.pcraft`/PSB/QOI types (#1951); the same 28 asset
  names. Card adds the destructive annotations, the path replace/refusal,
  the `bitDepth` refusal, `photo.reload`, the Lightroom limits, `maxDistance`,
  the stem-sidecar rule, the index refusals, the dab cap, `crop.aspect`,
  Constrain Crop and the Lanczos change.
- PdfCraft v0.11.0 (`3e30645`; six commits, Cargo.toml 0.10.1 to 0.11.0 in
  the release commit alone, no untagged version; v0.12.0 and v0.13.0 already
  exist upstream): `apps/pdfcraft-cli` byte-identical (`main.rs`
  `MCP_OPTIONS`, `mcp`, `automation_roots` and `validate_options`: both root
  flags taken out first, `--root` once with a value, `--compact`, unknown
  options refused, `--root` on top of both roots), as are `crates/automation`
  (`mcp.rs` compact core of fifteen plus `tool_search` and `tool_call`,
  `tools.rs` 171 tools, `doc_inspect` without a required parameter,
  `file_access.rs`), `crates/platform/src/staging.rs`, `crates/engine`,
  `docs/mcp.md`, `crates/automation/README.md`, `release.yml` and
  `packaging/`; nothing added, removed or renamed, no schema, write or
  confinement change. The one behaviour change is #3522 (fixes #3499) in
  `crates/redact/src/{interp.rs,sanitize.rs}`: sanitizing `hidden-layers`
  (`doc_remove_hidden`, `doc_optimize` `discard`) evaluates an OCMD's `/P`
  policy (AnyOn, AllOn, AnyOff, AllOff, indirect names resolved, an invalid
  one hidden when any group is off) and bounded `/VE` expression (depth 64,
  4096 nodes) against the default configuration, so AllOff and Not content
  goes with every group on, an unevaluable expression counts as hidden unless
  it names only on groups, and off groups that surviving content refers to
  stay in `/OCProperties`; the pass always runs and `doc_hidden_info` counts
  hidden image and form XObjects, undecodable forms and forms at `MAX_DEPTH`
  12. The rest is a raster watchdog test, `xtask` moving the workspace
  crates' pins with the version, the shared nix workflow and
  `.coderabbit.yaml`. Release 2026-10-21 19:57 UTC with the three assets and
  `SHA256SUMS.txt`. Card adds the 0.11.0 sanitizing sentence to "Durable
  verification" and moves the date.
- PhotoCraft v0.12.0 (`6a2d027`; one version commit, "Release: version
  0.12.0", no untagged version): `apps/photocraft-cli/src/lib.rs` changes
  only `convert`, `run` and `batch` (DDS flags; `batch` drops recorded Save
  and view steps from played action sets, #6860); the `mcp` entry is
  identical (`--bridge`, `--control-token`, `--control-token-file` and the
  two root flags, any other flag `unknown flag` with exit 2);
  `workspace.rs`, `files.rs` and `docs/mcp.md` unchanged. `server.rs`: the
  same 25 tools, `doc_inspect` still `{index?}`; `doc_save`/`doc_export`
  take `ddsCompression` and `ddsMipmaps`, forwarded to `app.save` over the
  bridge, and refuse a `quality` outside 1..100 instead of clamping it
  (#7023); `headless.rs` `on_doc`: an `index` on `doc_place`,
  `doc_export_layers`, `doc_export_data_sets` or `doc_import_data_sets`
  leaves the active document alone, on error too (#7025). Engine, through
  `command_run`: 668 to 674 ids, nothing removed or renamed; new
  `history.stepForward`, `history.stepBackward`, `history.clear` (undoable,
  refused while a job runs), `history.setSource` (`state` row or
  `snapshot`), `brush.mixer.load` and `brush.mixer.clean`; `doc_inspect`
  adds `historySource`; `edit.fill` contents=history takes a panel row or
  `snapshot`, default the brush source; DDS is writable wherever a save
  takes `dpxBits` (BC1–BC3 lossy); `image.trim` and `image.duplicate
  {mergedOnly}` refuse over 2^30 px (#7223); batch Format "same" saves raws
  and import-only inputs as PSD (#5799); a GIF opens in Indexed Color
  (#7886). The three catalog assets and SHA256SUMS.txt are in the release.
  Card adds the DDS options and quality refusal, the index rule,
  `historySource`, the six commands, the `edit.fill` change, the flatten
  limit, the batch "same" rule and the GIF mode.
- SoundCraft v0.11.0 (`b74fca0`; two commits above v0.10.0, `7b339fe` "Skip
  CodeRabbit reviews on Dependabot PRs (#821)" and the release bump, no
  untagged version inside the range): the whole diff is a new six-line
  `.coderabbit.yaml` (no reviews on `dependabot[bot]`), `Cargo.toml` and the
  18 workspace-crate version lines of `Cargo.lock`; no dependency moved.
  `apps/soundcraft-cli` (`main.rs` `parse_mcp_args`: `--connect`, `--demo`,
  both roots once through `automation_args.rs`, a misspelled
  `--automation-…` flag is `unknown mcp option`, any other unknown flag still
  falls through `_ => {}` and is ignored, roots with `--connect` refused),
  `crates/engine/src/file_access.rs`, `io.rs`, `crates/automation/src/mcp.rs`,
  `docs/mcp.md`, the packaging scripts and `release.yml` (reusable
  `craft-common-actions` workflow at `@main`) byte-identical. The same 17
  tools (`tool_definitions`): `inspect_session` with optional `detail`
  (`summary`|`full`) and no required parameter, `batch` `calls` `maxItems`
  `MAX_BATCH_CALLS = 1000` refused before any call runs, seven APP_ONLY
  tools; no new command, no new write, the 0.10.0 backup rule and the 0.8.0
  stored-path rule unchanged, `bounce_mix` still without a replace guard.
  The release (2026-10-21 18:12 UTC) carries the three expected assets at the
  manifest's byte sizes plus `SHA256SUMS.txt`; its note drops
  `freebsd-aarch64` (CI time limit, craft-common-actions#39), never used here.
  Card unchanged but for the date.

## Release-tag recheck of all thirteen apps, moved by pull requests #10, #11 and #12 — 2026-10-29

Pull request #10 (run 39937835313, `8678dea`, release 1.5.6) moved all
thirteen pins on 2026-10-23, #11 (run 40082757472, `d376480`, release 1.5.7)
PhotoCraft from 0.14.0 to 0.15.1 on 2026-10-24, and #12 (run 40945242370,
`bb3fe62`, release 1.5.8) all thirteen again on 2026-10-29, after the signing
fix `6b61878`. None of those moves was rechecked when it merged, so each
repository is reviewed here from the tag last rechecked above (the pull
request #8 or #9 section) to its 1.5.8 pin, by `git log`, `git diff` and
`git show` on blob-less clones; nothing from upstream was built or run and no
asset was downloaded. The release workflow had already checked every archive
against the manifest and the release's `SHA256SUMS.txt` when it pinned and
signed it; here GitHub's release metadata confirmed that each release still
carries the three manifest assets at the manifest's byte sizes plus
`SHA256SUMS.txt`. Every catalog launch is still accepted with unchanged
meaning, every smoke tool still exists without a required parameter
(GridCraft's `inspect_workbook` and FigCraft's and WordCraft's
`inspect_document` gained optional ones), and no tool was removed or renamed;
GridCraft (`list_windows`), PdfCraft (eight), PhotoCraft
(`doc_replace_smart_object`), VectorCraft (the desktop-only `answer_dialog`)
and WordCraft (`list_documents`) added tools. CADCraft 0.14.0, PhotoCraft
0.16.0 and SoundCraft 0.14.0 parse with clap, so an unknown option or a stray
argument is a usage error (exit 2): SoundCraft no longer ignores unknown `mcp`
flags as the pull request #8 entry says, and since PhotoCraft 0.16.0 a
non-empty `PHOTOCRAFT_CONTROL_PORT` in the environment the host gives the
server stops its confined launch (exit 2). DesignCraft 0.13.0, SoundCraft
0.13.1 and VectorCraft 0.15.0 let each root flag repeat (one use of each, as
the catalog gives, means what it did); no root flag appeared for CADCraft,
FilmCraft, GridCraft or LightCraft. Several version bumps were never tagged
or released (DeckCraft 0.11.0; FigCraft 0.11.0, 0.11.1 and 0.12.0; GridCraft
0.11.0 and 0.12.0; PhotoCraft 0.15.0; SoundCraft 0.12.0 and 0.13.0), each
followed by a release that mainly fixes release packaging, as each bullet
details. The October 28 releases share a per-user Windows MSI default (the CLI
still beside the app), a desktop-only self-updater (`craft-update`) that no
CLI links, hash-pinned AppImage tooling and macOS stapling retries; the
CADCraft, PhotoCraft and SoundCraft tarballs add shell completions, one named
like the CLI (handled since `6b61878`). CADCraft, FilmCraft and GridCraft now
authenticate their desktop control connection with a token; Storytold uses
none of those bridges. Every card's recheck date is now 2026-10-29.

- CADCraft v0.14.0 (`fbd97d4`; 311 commits over four tags, v0.11.0, v0.12.0,
  v0.13.0 and v0.14.0, each version bump made in its own release commit, so
  none went untagged): `mcp` moved from `parse_mcp_args` in `main.rs` to clap
  (#2268, RFC-0012; `apps/cadcraft-cli/src/args.rs` `McpArgs`, `mcp.rs`,
  `lib.rs` `run`). It still takes `--connect HOST:PORT` (once, trimmed, a host
  and a `u16` port, `[::1]:7979` accepted) with `--lazy`/`--launch` that
  require it, plus the flattened `Settings` flags `--config-dir DIR`,
  `--fontalt FONT` and `--fontfallback FONTS` with the fallbacks
  `CADCRAFT_CONFIG_DIR` (empty means no settings folder; its `plotters` folder
  holds plotter configurations), `CADCRAFT_FONTALT` and
  `CADCRAFT_FONTFALLBACK`, variables the engine already read at v0.10.0;
  unknown, repeated or positional arguments are clap usage errors with exit 2
  (1 before); plain `mcp` is still the headless session with no root or
  confinement flag, so the catalog launch keeps its meaning.
  `crates/mcp/src/server.rs` unchanged; `tools.rs` changes only `open`'s
  description to "Open a DXF or DWG file." (#1887): the same 12 headless tools
  (15 with the bridged `screenshot`, `ui_inspect`, `ui_click`),
  `inspect_drawing` `{entities?, limit?}` with no required parameter, 200
  entities by default. `backend.rs` changes only `Remote`, the `--connect`
  bridge: it sends the per-session token the app writes to an owner-only
  `cadcraft-control-<port>.token` (#1844, `control_token.rs`) and resends once
  on an `unauthorized` not-run reply (#2098); `Headless` unchanged.
  `docs/mcp.md` adds the `usage` and `loops` rows and `shapes`' `selfCheck`;
  `docs/cli.md` is new (exit codes, the variable table, deliberately no
  variable for `--connect`); `docs/control-protocol.md` documents the token;
  there is no `docs/agents.md`. Engine through `execute`: 13 new command ids,
  none removed or renamed (`attdisp.normal|on|off`, `blockreplace`,
  `blocks.description`, `compareexport`, which opens the comparison as a new
  untitled drawing, `cutbase`, `layout.saveas`, `loops`, `thickness`, `usage`,
  read-only with a 5,000,000-object scan cap, `volume.measure`,
  `vports.named`); `appload {path}` refuses a non-`.lsp` path and returns
  `commands` (#1903). One new disk write: `layout.saveas {name?, path}`
  (#2177, `cmd/layout/saveas.rs`) writes a `.dwt`, `.dwg` or `.dxf` template
  (no extension adds `.dwt`, another is refused), replacing the target. The
  0.12.0 security batch (#1840 to #1852): save, export, plot, autosave and the
  `.adt` log go through `atomic_write.rs` (an exclusive
  `.cadcraft-tmp-<pid>-…` beside the target, then rename); `capped_read.rs`
  makes open (512 MiB), `script` and LISP `open`/`load`/`appload` (64 MiB)
  take regular files only; LISP callbacks, `wcmatch`/`equal` and `setvar`
  conversion get step and size budgets; import, render, document-model,
  constraint and geometry work is budgeted; a DXF over 1 GiB is not converted
  to DWG. Stored xref and data-link paths now go through craft-docpath
  `resolve_absolute` (#1750; craft-docpath `82a24b0` to `92d392c` changes
  nothing under `crates/docpath/src`), so the 0.8.0 rule holds. No network or
  process reach: the `craft-update` self-updater (#2141) links only into the
  desktop app (`apps/cadcraft`, `crates/ui-egui`), and `cadcraft-cli` depends
  on engine, io, mcp, render, clap, same-file, serde_json and thiserror.
  Packaging: the Linux packages and tarball now ship `cadcraft-cli` man pages
  and bash/zsh/fish completions (the bash one is named `cadcraft-cli`, which
  Storytold's `6b61878` already handles); the MSI installs per-user by default
  under `Programs\ArtCraft\CADCraft`, `cadcraft-cli.exe` still beside the app;
  `release.yml` adds a git-sources job and defaults to `contents: read`, still
  delegating to `craft-common-actions` at `@main`; macOS stapling retries.
  Release v0.14.0 (2026-10-28 16:34 UTC) carries the three manifest assets at
  the pinned byte sizes plus `SHA256SUMS.txt` (no `freebsd-aarch64`). Card
  corrects `mcp`'s argument list and `open`'s description and adds the
  settings flags, `usage`, `loops`, `selfCheck`, `compareexport`, `appload`'s
  refusal and `commands`, `layout.saveas` and the read limits.
- DeckCraft v0.12.0 (`29f0f77`; from v0.9.0 through v0.10.0 `b47195f` and
  v0.11.1 `9ec3926`, 564 commits, 522 files): 0.11.0 was bumped in `1330ce4`
  and never tagged or released, and v0.11.1 adds only a macOS signing fix
  (`79bf9a6`) ten minutes later, so no untagged version ships alone. The `mcp`
  branch of `apps/deckcraft-cli/src/main.rs` (`:606-654`),
  `automation_args.rs`, `help.rs`, `crates/mcp/src/server.rs`, `headless.rs`
  and `backend.rs` are unchanged (`--connect`, `--sample`, both root flags
  once, existing folders, refused with `--connect`, the whole process
  confined; other options `unknown mcp option`);
  `crates/engine/src/file_access.rs` changes only its test scan.
  `crates/mcp/src/tools.rs` keeps the same 25 tools, `list_commands` still
  `{filter?}` with no required parameter (`:67-73`); its one change adds `rtf`
  to `export`'s `format` enum (`:122`). `docs/mcp.md` adds only `chart.options
  {textColor}`; there is no `docs/agents.md` at either tag. Engine: nine new
  command ids, none removed or renamed (321 → 330 by source count):
  `slide.reuseList` (reads a path or data, lists the slides), `review.reject`,
  `format.languageAll`, `shape.openPath`, `closePath`, `deleteSegment` and
  `segmentType` (0.11.1), `slide.selectRange` and `text.deleteSurrounding`
  (0.12.0). Since 0.11.1 `file.export` and `file.save` write an RTF outline
  for `rtf` or a `.rtf` path and `file.open` reads RTF (by content) as an
  outline deck (`cmd/file.rs`, `crates/format/src/rtf.rs`); `io::read_file`
  refuses a non-regular file or one over 2 GiB and `write_file` keeps an
  existing file's permissions and writes through a link to its root-checked
  target (`io.rs:9-20`, `:33-67`); `design.browseTheme` with a `.pptx` or
  `.potx` replaces the current master and its layouts and moves slides to
  matching layouts; PDF slide rasters are capped at 64M pixels (dpi lowered).
  An `ids` entry or a slide, table row/column, animation or layout index that
  is negative or fractional is refused instead of acting on the selection
  (slide commands 0.10.0 and 0.11.1, the rest 0.12.0; `cmd.rs:357-372`). Since
  0.12.0 PDF export writes only http, https and mailto links besides slide
  links (`crates/pdf/src/lib.rs:623`). Also `chart.options {textColor}`, fill
  and line on a group reach its members, `arrange.group` nests at most 32
  deep, `.potx`/`.ppsx` keep their content types, and pptx import gains
  resource budgets. The startup self-update (`craft-update`) is in the desktop
  app only, not the CLI. Not new but missing from the card:
  `review.addToDictionary` appends to a user dictionary file and
  `review.spelling` reads system Hunspell folders outside the roots
  (`spell.rs`, allowed by the `file_access` scan). Packaging: the macOS `.app`
  still holds only the desktop app beside the separate CLI zip, Linux installs
  `/usr/bin/deckcraft-cli`, the Windows MSI now defaults to a per-user
  `Programs\ArtCraft\DeckCraft` folder with the CLI still beside the app,
  appimagetool and its runtime are pinned by hash; `release.yml` still calls
  `craft-common-actions` at `@main` (craft-fonts pin moved). Release v0.12.0
  carries the three manifest assets at the manifest's byte sizes, with GitHub
  digests equal to the pinned sha256, plus `SHA256SUMS.txt`; no
  `freebsd-aarch64`. Card adds the RTF outline route, the 2 GiB regular-file
  read rule, the `ids` and index refusals, `design.browseTheme`'s master
  replacement, the PDF link rule and the dictionary paths the roots do not
  cover.
- DesignCraft v0.14.0 (`7da69c1`; v0.12.0 `5e8ef67` and v0.13.0 `dcce40f`
  between, each version bumped in its release commit alone, no untagged
  version, no newer tag yet): 685 commits (464 non-merge), 561 files. The
  `mcp` branch of `apps/designcraft-cli/src/main.rs` keeps `--connect PORT`,
  `--sample` and both root flags, unknown options refused, roots with
  `--connect` an error; since 0.13.0 (#1552, `automation_args.rs`,
  `crates/engine/src/file_access.rs`) each root flag may be repeated, every
  use adding a folder of its kind (one given twice counts once; a path must
  lie inside one of them, never their common parent; read and write stay
  separate). One use of each, as the catalog gives, keeps its meaning and its
  error text (`outside the read root X`; several give `outside the read roots
  A, B`). `crates/mcp/src/tools.rs`, `headless.rs` and `backend.rs`
  byte-identical: the same 26 tools, `inspect_document` with an empty schema;
  `server.rs` (#1803, 0.14.0) answers a non-UTF-8 line with -32700 instead of
  ending the stream. `docs/mcp.md` documents the repeated roots, the per-user
  MSI path and table-cell find matches; `docs/agents.md` adds the CLI-only
  `validate-pdf` checks (`--standard x4|x1a` in 0.14.0). Engine: 521 to 542
  command ids, 21 added, none removed or renamed. Since 0.13.0
  `find.find`/`find.change` reach table cells in document scope (`cell`,
  cell-relative offsets); `links.update`, `links.relink` and
  `links.relinkFolder` read a linked file under a 256 MiB cap and refuse a
  larger one by name (#1751, `cmd/links.rs` `reload_capped`; the 512 MiB PDF
  bound on `file.place` is unchanged), and `links.relinkFolder` takes only a
  file directly in the chosen folder (#1399); a type size outside 0.1 to 1296
  pt and an Insert Pages count outside 1 to 9999 are refused; `file.exportPdf`
  keeps Object Layer Options choices as vector optional content (#1241,
  `crates/pdf/src/optional_content.rs`), failing with a file-named error when
  a choice cannot be preserved or names a layer the file lacks, and only `a2b`
  still rasterizes them (`rasterize_layered`, same error path);
  `object.layerOptions` takes `useDefaults` and checks every selected PDF
  before changing any; `file.exportIdml` with `embedImages: false` refuses a
  layer choice; native files holding one are format 4. Since 0.14.0
  `file.exportPdf` takes `standard: x1a` (craft-prepress flattening),
  `file.print` spools exactly the `file.exportPdf` PDF and returns its
  warnings, and `ink.separations` (query) and `file.info` are new; the startup
  self-updater (`craft-update`) is linked into the desktop app only, not
  `designcraft-cli` or `crates/mcp`. A scan of added `std::fs` calls and of
  the engine's file-I/O call sites found no new write path (sites only moved
  in the `cmd/export/` and `cmd/file/` splits). `release.yml` adds a
  `git-sources` job (git dependencies only from github.com/storytold,
  `Cargo.lock` current, no cargo source replacement), moves `contents: write`
  to the release job and still delegates to `craft-common-actions` at `@main`;
  packaging ships `NOTICE`, the MSI installs per user or per machine under
  `ArtCraft\DesignCraft` with the CLI beside the app, and macOS stapling
  retries. Release v0.14.0 (28 assets, FreeBSD x86_64 only) keeps the three
  manifest assets at the manifest's byte sizes plus `SHA256SUMS.txt`. Card
  adds the repeatable root flags (dropping "each flag is given once"),
  table-cell find, the type-size and page-count refusals, the 256 MiB link cap
  and the folder-relink rule, vector layer export with its failures and the
  a2b-only rasterization, the `file.exportIdml` refusal, `x1a`, `file.print`
  printing the `file.exportPdf` PDF and `ink.separations`.
- EffectCraft v0.18.0 (`c3600f9`; v0.15.0, v0.16.0 and v0.17.0 between, each
  bump in its own tagged release commit, no untagged version; 351 non-merge
  commits, 870 files): the `mcp` branch of `apps/effectcraft-cli/src/main.rs`
  is unchanged (`--autosave | --bridge PORT`, both root flags repeatable,
  unknown options refused before anything runs, `--autosave` with `--bridge`
  refused); the one parser change is `run --args-file F` (one argument per
  line, for Windows' command-line limit), a valued option `mcp` accepts and
  ignores. `crates/automation/src` (`tools.rs`, `confine.rs`, `backend.rs`)
  and `docs/mcp.md` are byte-identical: the same 36 tools, `doc_inspect` with
  an empty schema, the same refused/read/write tables (scripts, `control`,
  `ui_*` and `script_ui` still refused while confined), and `engine.batch`
  still takes steps as `command|id` plus `params`, so the per-step check
  holds. Engine command ids 669 to 673 counted by `cmd!`/`query!` literal (669
  at v0.13.0 too; the 382 of earlier entries is not that count), none removed
  or renamed, none of the four new ones taking a path: `layer.replaceSource`,
  `effect.pickCryptomatte`, `effect.cryptomatteAt`, `text.deleteSurrounding`;
  `file.projectSettings` adds `frameStart`, `layer.revealSource` takes
  `layers`. `docs/agents.md` adds the per-user Windows MSI path, a Cryptomatte
  recipe and `text.deleteSurrounding`. Engine, all 0.17.0: `prop_ref` resolves
  `effects/<match name>[#n]/<property>`, so `prop.get`, `prop.set` and
  `prop.addKey` take it (#2064); deleting a layer clears the layer-reference
  properties and keys that named it in the same undo step (#2153);
  `general.createSplitLayersAbove` defaults on (#2083); a key on the out point
  no longer warns (#2084); Reload Footage reads a numbered still as its own
  file (#2074); stored paths go through craft-docpath `resolve_absolute`, so
  an imported 3D model's side files are read only locally or from its own
  share (the probe used to join any URI) and a `C:\` path is invalid off
  Windows (#1975); input bounds for SVG CSS and raster surfaces (512 MiB), PDF
  images (64 Mi pixels) and craft-pdf, text layout (over 1 MiB lays out
  empty), roto mattes, expressions (4 MiB rewrite) and segmentation
  checkpoints (1 GiB); eleven colour and key effects recalibrated to After
  Effects (#1872), so older projects can render differently. 0.18.0 is egui
  0.37, craft-ui docking, a desktop-only `craft-update` self-update
  (`ui-egui`'s frame loop, not reached by `mcp`), the `commands/` to `cmd/`
  split, Clippy refactors and movie encoding beside rendering (bytes pinned).
  No new MCP-reachable disk write found. Packaging: a per-user Windows MSI
  default with an install-policy check, `NOTICE` shipped, appimagetool and
  AppImage runtime hash-pinned, a macOS `stapler` retry; the CLI still sits
  next to the app, at `/usr/bin/effectcraft-cli` and in the separate macOS
  zip; `release.yml` moves `contents: write` to the job, still
  `craft-common-actions` at `@main`. Release 2026-10-28 17:38 UTC: the same 28
  asset names as v0.14.0 (no `freebsd-aarch64`), the three manifest assets at
  the manifest's byte sizes and SHA-256 (API digests), plus `SHA256SUMS.txt`.
  Card adds the 0.17.0 path form for the prop.* tools, the delete and split
  rules, `layer.replaceSource`, the Cryptomatte pick and the model side-file
  rule.
- FigCraft v0.12.1 (`ef9721c`; 886 commits above v0.9.0, tagged v0.10.0,
  v0.11.2 and v0.12.1; the release commits of 0.11.0 (`32b836f`), 0.11.1
  (`22c15e3`) and 0.12.0 (`08204fd`) were never tagged or released: their
  release runs were cancelled or failed, and the follow-ups fix macOS signing
  and the web build's wasm size gate, 0.12.1 also carrying the strict-clippy
  refactor #1403 (225 files changed since 0.12.0; its refactor commits were
  not read line by line) and the Flatpak network grant #1471; v0.10.0 is CI,
  SonarCloud, a README icon and chrono dates only): the `mcp` branch of
  `apps/figcraft-cli/src/main.rs` (`:189`) keeps `[--attach PORT]` and the two
  repeatable root flags (`ROOT_FLAGS`, `roots_of`, the same
  `file_access::Roots::new`), refuses positionals, unknown options (exit 2)
  and `--attach` with roots, and `fn mcp` (`:271`) is unchanged. Since 0.11.2
  (#1161) `--help` or `-h` anywhere but as a value prints the usage and exits
  0, ahead of a bad option (`args.rs:40`); since 0.12.1 (#954) `--` ends the
  options (`args.rs:23`; positionals stay refused for `mcp`) and
  `--no-system-fonts` is a parsed flag instead of being stripped anywhere in
  argv. `crates/mcp/src/tools.rs`: the same 18 tools, nothing added, removed
  or renamed; `inspect_document` still has no required parameter (`:174-185`)
  and since 0.11.2 takes `maxBytes` (#915: default 8 MiB of the whole JSON-RPC
  message, below 1024 refused; a larger tree is bisected to a shallower depth
  with a `truncated` object, `:592`, `:641`), `get_node` `offset` and
  `maxBytes` (a window of children with `children.nextOffset`; an error when
  the layer alone passes the limit); since 0.12.1 `batch` steps take `as` and
  `{"$ref": name, field}` with slash paths (#1003, `$ref` reserved like
  `$step`, duplicate names refused before any step), `export` takes `xml`
  (Android Vector Drawable, #840) with `vdCompat`, and `open_file` reads
  `.sketch` (Sketch 48 and newer, #1021). `server.rs` changes one clippy line
  (32 MiB line limit, -32600 kept); `headless.rs`, `resources.rs`,
  `prompts.rs` and `backend.rs` are identical. `docs/mcp.md` and `docs/cli.md`
  (+402/-69) add the headless-only scope of the roots (#905), `$ref`, xml,
  boards, `data.fill`, `--help` and `--`, but document neither `maxBytes` nor
  `offset`, and the batch row still says the clipboard is not rolled back
  although `session/exec.rs:49,82` restores it after any failed command since
  0.11.2 (#1167), a failed batch included. Confinement: `file_access.rs` moved
  to `crates/engine/src/automation/` (98% similar, adds `same_file`),
  `crates/engine/clippy.toml` and its four `disallowed_methods` exceptions
  unchanged; new writes go through it (`data.fill {dir}` via `file.export`, up
  to 500 rows; `variable.export` dart and tailwind with `path`), `file.saveAs
  {data: true}` and `file.exportLayers {zip}` return base64 instead, and a
  plugin's API 4 `saveFile` only queues a UI request headless sessions drop.
  On macOS the system font scan, unconfined as before, also reads fonts that
  font managers (#1309) or Adobe Fonts (#661) activate outside the font
  folders. Engine, through `run_command`: 569 to 615 command ids, none removed
  or renamed (boards, `data.fill`, `text.fit`, Dev Mode measurements,
  Selection colors variables, board templates, tables, timer and vote, widget
  fields, paint copy and paste, `file.markSaved`). Since 0.12.1 `file.save`
  without a path refuses when the file changed on disk since it was opened or
  saved unless `overwrite: true` (#1374, `cmd/file/save.rs:98`), and a save
  over a native file opened without the images past the 4 GiB or 20,000-image
  budget is refused (#1314, `:87`; auto-save skips it, `convert` and `run --in
  X --out X` refuse); since 0.11.2 style links in a call apply after its
  values (#1042), `node.reparent` `index` is the final position (#1005),
  `node.set {path}` replaces a vector's geometry (#1004) and fills and strokes
  take `"none"`; images over 16384 px a side draw scaled down (#1337) and PDF
  is written with craft-libs' krilla (#1240). The desktop app's new update
  check and self-update (craft-update, #1328) do not reach `figcraft-cli`,
  whose dependencies are unchanged. `release.yml` only re-pins craft-fonts;
  appimagetool and the AppImage runtime are pinned by hash (#950), Windows
  gains an MSI install policy (#1399), and the tarball (`bin/figcraft-cli`),
  the portable ZIP (`figcraft-cli.exe`) and AppRun's `cli` are unchanged.
  Release v0.12.1 (2026-10-28 17:58 UTC, 30 assets, still no
  `freebsd-aarch64`) holds the three manifest assets at the manifest's byte
  sizes plus `SHA256SUMS.txt`. Card adds `mcp --help`, the clipboard restore,
  `$ref`, `.sketch`, the font-manager fonts, the style-link, `node.reparent`,
  board and `data.fill` rules, xml export, the two save refusals and the
  `maxBytes` truncation.
- FilmCraft v0.14.0 (`a2d8e9c`; v0.11.0, v0.12.0 and v0.13.0 between, 458
  commits, each bump in its own "Release" commit, no untagged version): the
  `mcp` branch of `apps/filmcraft-cli/src/main.rs` moved into `cli_mcp`
  (Clippy refactor) with the same logic; `unknown_opt` (`args.rs`, unchanged)
  still refuses every option but `--bridge`, `--project`, `--demo` and
  `--data-dir` (exit 2), so a root flag is still rejected and no native root
  or confinement flag appeared. The CLI's own `exec`/`run` now make
  `file.exportMedia` wait unless `"wait": false` (#2342; not MCP).
  `crates/automation`: the same 17 tools, `doc_inspect` and `document()`
  untouched, still without parameters; only bridge code changed: it sends
  `FILMCRAFT_CONTROL_TOKEN` on every request (#2764), reads screenshots from
  an owner-only temp dir (#2919) and documents `ui_click` `count` 0-10 and
  `ui_drag` `steps` 0-1024. Since 0.13.0 the desktop `--control` listener
  stays closed without a 64-hex-digit token (`control_server.rs`), as
  `docs/agents.md` and `docs/control-protocol.md` now say ("The port has no
  authentication" is gone); `docs/agents.md` also documents the
  `effects.setParam` reply and the per-user Windows MSI folder
  (`%LOCALAPPDATA%\Programs\ArtCraft\FilmCraft`). Engine, through
  `command_run`, by a source extraction of the registry (the 0.10.0 total of
  413 not recounted): nine new ids, none removed or renamed (`history.clear`,
  `history.deleteRedoable`, `sequence.workAreaBar`, `sequence.setWorkArea`,
  `.setWorkAreaIn`, `.setWorkAreaOut`, `sequence.showDuplicateFrameMarkers`,
  `sequence.duplicateFrames`, `captions.duplicate`). `effects.setParam`
  refuses a float outside its range (0.13.0, #2679) and returns `{keyframes,
  param, value}` (0.14.0, #3281); `effects.apply` returns `{applied: [{clip,
  index, effect}]}` (#1545); `file.exportMedia` takes `maxThreads` (#1216); a
  parameterless `sequence.closeGap` with no gap selected closes every gap
  between In and Out instead of failing (#1986); Lift and Extract fill the
  clipboard. Disk and paths: `media.status`, `media.makeOffline {deleteFiles}`
  and `file.projectManager` (which now fails) act only on paths the
  stored-path rule follows (#2869, #2609 with `resolve_absolute`); relink
  skips symlinked folders; an ingest destination stored in a project is used
  only once `project.ingestSettings` chose it or it lies in the project folder
  (#3083); AAF/OMF embedded audio goes to a numbered name instead of over an
  existing file (0.11.0, #2023) in a one-component `<name> Media` folder
  (#2956); project-derived export names stay one component (#2903); proxy
  outputs are reserved atomically (#2922); saving creates the previews folder
  only when there are previews (#2343). New bounds: AAF/OMF export decodes at
  most 64 Mi samples per media range, Remix at most 10 minutes, `lut.import` 8
  MiB, audio 384 kHz and 64 channels, generator frames 2^25 pixels, and
  imported sequence settings are validated. Desktop only: self-update prompt
  (#3298), egui 0.37, craft-ui docking, auto-save names with Unix seconds
  (`docs/project-files.md`, the stored-path rule unchanged). The model
  downloads (`transcript.downloadModel`, `tts.downloadVoices`) stay off: every
  packaging script builds `-p filmcraft -p filmcraft-cli` without features
  (the shared workflow itself not read). `release.yml` still calls
  `craft-common-actions` at `@main` (only `craft-fonts-ref` moved); Linux
  packaging pins appimagetool 1.9.1 and its runtime by SHA-256, macOS retries
  the stapler. The release (2026-10-28 16:40 UTC, lightweight tag on
  `a2d8e9c`) carries the three manifest assets at the manifest's byte sizes
  plus `SHA256SUMS.txt`; no `freebsd-aarch64`. Card adds the token-gated
  listener (replacing "unauthenticated"), the `effects.setParam` and
  `effects.apply` results, `makeOffline` file deletion, the history commands,
  the parameterless `closeGap`, the AAF/OMF audio write, and the stored-path
  rule's reach to `media.status`, `makeOffline` and Project Manager plus the
  ingest destination.
- GridCraft v0.13.0 (`4328437`; 582 commits without merges, 612 files over
  v0.10.0; v0.11.1 and v0.12.1 tagged between, while the 0.11.0 (`73af8c6`)
  and 0.12.0 (`4995ecc`) bumps were never tagged or released: within the
  hour a macOS packaging fix, stapler retry `10fb7d5` and keychain lifetime
  `bca6794`, made each a `.1`): the `mcp` function of
  `apps/gridcraft-cli/src/main.rs` (`:527-555`) and `Args::parse` are
  outside every hunk (`--connect`, `--in` and `--sample`, each with a value,
  unknown options refused at `:128`, extra positionals at `:530`, plain
  `mcp` a blank headless session at `:547`; no root flag). Elsewhere in the
  CLI `convert` writes `.pdf`, `run --script` refuses a JSON line with an
  unknown key (#2256) and `check` fails an incomplete or empty scan.
  `crates/mcp/src/tools.rs` goes from 21 to 22 tools, nothing removed or
  renamed: 0.13.0 adds `list_windows` (`window.list`) second, and every
  tool but `list_commands`, `list_functions`, `list_windows`,
  `new_workbook`, `open_workbook` and `screenshot` gains optional integer
  `window` and `doc` ids (`:110-125`, routed through `engine.execute`; an
  unknown id is "no open window has id N"), so `inspect_workbook` has those
  two and still no required parameter; `server.rs` is byte-identical.
  `--connect` and `send` now authenticate to the app's control port with
  `GRIDCRAFT_CONTROL_TOKEN` or the app's token file (`control_auth.rs`,
  #777, 0.13.0); headless is untouched. `docs/mcp.md` adds the
  `list_windows` row, the `window`/`doc` rule and the token; no
  `docs/agents.md` exists at either tag. File access stays unconfined;
  since 0.12.1 `read_file` refuses anything but a regular file and stops
  reading at 2 GB, and `write_file` creates `<path>.sctmp` exclusively with
  the target's permissions before the rename (`io.rs:613-673`, #2418). The
  `cmd!` registry grows from 340 to 354 ids, none removed:
  `automate.trustScripts`, `formulas.convertToNumber`,
  `formulas.selectPrecedents`/`selectDependents` and `view.showObjects`
  (0.11.1); `automate.stopAction`, `data.outlineSettings`,
  `formulas.pasteName`, `pivot.options`, `pivot.showDetails` (source
  records onto a new sheet), `view.showOutlineSymbols` and `view.statusBar`
  (0.12.1); `window.list` and `window.close` (0.13.0).
  `automate.runScript` refuses a file's stored scripts until trusted and
  any `file.*`, `link.*` or `path` step, inside an `io.rs` `ScriptSandbox`
  (#2178, 0.11.1), and from 0.12.1 window steps too, with
  `document.inspect` reporting `trust` (`cmd/extra/scripts.rs`).
  `formulas.evaluate` refuses what cell entry refuses (0.11.1);
  `range.setValues` takes `parse: false` (#2267, 0.12.1); HTML export also
  stops at 4,000,000 cells (`io.rs:454`, #2416) beside the 100,001-row cap
  (`:449`); the unknown-extension error (`io.rs:230`) and `.pdf` as a print
  (`cmd/file.rs:117-121`) are unchanged. `DocState::from_saved` (#2512) is
  added but never called, so opening still recalculates. `release.yml` only
  moves `craft-fonts-ref`; packages add `NOTICE` and `ATTRIBUTION.md`, the
  MSI installs per user by default with the CLI still beside the app, and
  the desktop app's new self-updater (`craft-update`, #2566) is not a
  dependency of `gridcraft-cli`. Release v0.13.0 (2026-10-28 16:10 UTC)
  carries the three manifest assets at its byte sizes, GitHub digests equal
  to the pinned SHA-256, plus `SHA256SUMS.txt`; `freebsd-aarch64` is still
  absent. Card adds `list_windows` and the `window`/`doc` ids, the
  `parse: false` route, the `evaluate_formula` refusal, the script trust
  gate and `trust`, the regular-file rule and the 4,000,000-cell HTML cap.
- LightCraft v0.15.0 (`e381c1a`; v0.12.0, v0.13.0 and v0.14.0 between, each
  workspace version bump made in its tagged release commit, no untagged
  version; 943 commits, 800 files, v0.13.0 a single dev-tool path-validation
  PR): the `mcp` branch of `apps/lightcraft-cli/src/main.rs` (`fn mcp`,
  `:298-370`) is outside both hunks (`snapshot` gains `write_new`, `commands`
  sorts by id): `--connect [ADDR]`, `--headless`, `--demo`, `--compact`,
  `--library DIR` and FILES, any other `--` option refused, `--compact` still
  `with_command_tools(!compact)` (`:368`); no root flag. `crates/mcp`: the
  same 17 compact tools, `doc_inspect` with an empty schema
  (`tools.rs:108-114`), annotations unchanged; the one schema change is
  `export` `fit: dimensions|widthHeight` (#1861, `tools.rs:248`, `:734`, and
  `app.export`'s doc in `headless.rs`); `backend.rs` and `headless.rs` add
  tests only (one for the `--connect` client reconnecting after the app's new
  five-minute idle close, #2027). `docs/mcp.md` changes the MSI path, `fit`, a
  `%B` organize template and test paths; there is no `docs/agents.md`, and
  `AGENTS.md`/`CLAUDE.md` change contributor rules only. The engine `cmd!`
  registry goes from 370 to 375 ids, none removed or renamed:
  `keyword.nextSet`, `keyword.previousSet`, `library.toggleFilters`,
  `print.template.export` (a `.lcprint` file through `check_write_target`,
  replacing an ordinary file) and `print.template.import` (at most 256 KB,
  into the library's prefs) (#2778). New refusals: a photo `id`/`ids` that is
  not a whole number no longer falls back to the selection, nor mask-effect
  ids, spot `index` or colour-range `component` (#2456), as is `photo.label`
  without a label; a fractional `photo.rate` (#2755); a `crop.set` rect under
  2 % of the short side (#1968); `keyword.export` over an original or into a
  missing folder (#2015); an original export with `removeLocation` of a
  PSD/PSB with GPS or malformed metadata (#2546). Colour-range samples are
  capped at 64 (#2670) and hostile files meet allocation bounds (#2769, #2770,
  #2780). A rating, flag or label without `ids` makes the next photo active
  when the photo leaves a filtered view (#2327); merge warps sample Lanczos-3
  and a photo named twice merges once (#2481, #1959); faster 8-bit export
  encoding is byte-identical (#3168). On Windows `same_file` compares the file
  index, so a hard link to an original counts as it (#3020); create-new
  pinning of screenshot targets is app-side only, and the self-update prompt
  (#2933) lives in the desktop app, not in `mcp`. `release.yml` adds a
  git-sources job before the shared `craft-common-actions` release at `@main`;
  AppImage tools are hash-pinned; the MSI installs per user into
  `%LOCALAPPDATA%\Programs\ArtCraft\LightCraft` by default (#3104). Release
  v0.15.0 (2026-10-28 17:36 UTC) keeps v0.11.0's 28 asset names and carries
  the three manifest assets at the manifest's byte sizes (GitHub's asset
  digests equal the pinned SHA-256) plus `SHA256SUMS.txt`. Card adds the MSI
  path, `fit`, the PSD/PSB `removeLocation` refusal, `print.template.export`
  and `keyword.export`, the photo id, label and rating refusals, the
  colour-range cap, the active photo moving on, the crop minimum and the merge
  changes.
- PdfCraft v0.15.0 (`75360d1`; from v0.11.0 through v0.12.0, v0.13.0 and
  v0.14.0, 1,891 commits, 215 first-parent, 922 files; each version moves in
  Cargo.toml and Cargo.lock only in its own "Release 0.x.0" commit, so no
  version went untagged; v0.13.0 is one macOS file-association fix):
  `apps/pdfcraft-cli/src/main.rs` is split into `options.rs`, `run.rs`,
  `commands.rs`, `check.rs` and `ui.rs` (0.15.0), but `MCP_OPTIONS` (`--root`
  with a value, `--compact`), `automation_roots` (both root flags taken out
  first; `automation_args.rs` byte-identical), the `mcp` body and its usage
  text are unchanged, and `validate_options` still refuses unknown options and
  a second or valueless `--root`; since 0.14.0 it also refuses any path option
  whose value starts with `--` (photocraft#7071), and a non-UTF-8 argument is
  a usage error instead of a panic. `crates/automation/src/mcp.rs` keeps
  `COMPACT_CORE_TOOLS` (fifteen plus `tool_search` and `tool_call`) and the
  protocol versions; since 0.14.0 (#3924) a request line over 16 MiB gets
  -32600 and the server reads on, a non-UTF-8 line -32700, and a panic outside
  `tools/call` -32603. `tools.rs` goes from 171 to 179 tools, none removed or
  renamed: 0.12.0 adds `form_add_field_table`, `form_calculation_order`,
  `layer_set` (a view setting `page_render` follows) and
  `standards_remove_id`, 0.14.0 `attachment_add`, `attachment_delete`
  (destructive), `bookmark_set_style` and `content_copy`. `doc_inspect` is
  byte-identical (`{doc?}`, read-only, same handler). Schema changes add
  optional properties only (`bookmark_add` top/left, `stamp_custom` rect with
  `at` no longer required, `measure_scale` page_distance/page_unit,
  `doc_print` duplex `printer`, `char_spacing`, `content_update` crop to 0.95,
  `comment_edit` points, `doc_header_footer` font/shrink, accessibility
  summary/scope, `image_edit` rotate_by, `doc_optimize`
  compatibility/object_streams/lzw_to_flate); `redact_mark` takes page or
  pages, not both, and a comment id several comments share is refused.
  `docs/mcp.md` changes only its Windows paragraph and
  `crates/automation/README.md` adds the same, a `content_update.rotate` note
  and the per-user MSI path. Confinement: `file_access.rs` refuses a path on
  another share or device namespace than the root's by name before resolving
  it (#4003, 0.14.0); `resolve_in_root`, `resolve_for` and `check_roots` move
  to `paths.rs` unchanged; every tool read goes through `read_input`, capped
  at 512 MiB (0.14.0); `attachment_add` reads through the read root and embeds
  the file; no new write path. `crates/platform/src/staging.rs` keeps a
  replaced file's Unix group (0.12.0), its macOS extended attributes (#2658,
  0.12.0; bounded, and a failed copy refuses the save and keeps the file) and
  its Windows hidden and system attributes (#4647, 0.15.0). Engine changes an
  agent sees: Password-field values are never written by save, extract, split
  or combine (#3926, 0.14.0); removing an XFA form forces a full save (#4568,
  0.14.0); a copy-restricted document's text is kept from `text_lines`
  (0.12.0), `ocr_recognize` results, `content_copy`, `doc_compare` and the
  audit's covered text, and `pdfa_convert` needs the owner's permission
  (#3921); `redact_apply` refuses a mark with no readable area (#3728) and
  hidden-information removal strips metadata, private data, `/AF` files and
  actions from every owning object and decodes content strictly, refusing what
  it cannot read (0.12.0); since 0.15.0 a vector path a mark overlaps is
  removed whole instead of clipped (F-008, #4577) and unused Type 3 glyph
  programs and fonts are unlinked, failing closed on a Type 3 font it cannot
  clean (F-011). The desktop self-updater (#4654) and Windows install policy
  touch the app only; `pdfcraft-cli` does not depend on `ui-egui`.
  `release.yml` still delegates to `craft-common-actions` at `@main` (only
  `craft-fonts-ref` moved); packaging pins appimagetool and its runtime by
  hash, retries stapling and keeps the CLI artifact names. Release v0.15.0
  (2026-10-28 17:38 UTC, target `75360d1`) carries the three manifest assets
  at the manifest's byte sizes and SHA-256 digests plus `SHA256SUMS.txt`;
  FreeBSD aarch64 is still absent. Card adds the 179-tool count and the eight
  new tools, the 16 MiB line limit, the 512 MiB input cap and share refusal,
  `attachment_add` embedding read-root files, the XFA full save, the kept
  group, extended and Windows attributes, the Password-field rule, the
  copy-permission refusals, and the 0.12.0 and 0.15.0 redaction and sanitizing
  changes, and moves the date.
- PhotoCraft v0.17.0 (`b8c3f3a`; 3,567 commits from v0.12.0 over v0.13.0,
  v0.14.0, v0.15.1 and v0.16.0; "Release 0.15.0" (`e6d6fb4`, 2026-10-23) was
  never tagged or released, and its 51 commits to 0.15.1 that day leave
  `apps/photocraft-cli`, `crates/automation`, `docs/mcp.md` and `release.yml`
  alone): since 0.16.0 `photocraft-cli` parses with clap derive (#7071,
  `src/args.rs`); `mcp` takes `--bridge`, one token flag and both root flags,
  the roots still opened by `AuthorizedWorkspace::new` with unchanged meaning
  and no environment fallback (`crates/automation/src/args.rs:32-43`). Unknown
  flags, stray positionals (once ignored) and a repeated option (once
  last-wins) are usage errors, exit 2; roots with `--bridge` and token flags
  without it are refused (#8035); `PHOTOCRAFT_CONTROL_PORT` now stands in for
  `--bridge`, so set non-empty beside a root flag it stops the catalog launch,
  exit 2 (`args.rs:394-400`, `tests/it/cli.rs:1355-1362`; empty counts as
  unset). `server.rs` has 26 tools: new `doc_replace_smart_object` (0.16.0,
  #8150; `{path, index?, layer?}`, reads through the read root, destructive
  hint, `index` refused over the bridge), `doc_export_layers` also returns
  `skipped` (#8713); nothing removed or renamed, `doc_inspect` still
  `{index?}`, instructions and annotations unchanged; since 0.13.0 a non-UTF-8
  stdio line gets -32700 instead of ending the session. `docs/mcp.md` adds the
  root-rights, replace and launch-option rules. `workspace.rs`: since 0.17.0
  `write` (`doc_save`/`doc_export`) refuses to replace a non-regular file or
  one PhotoCraft does not write by extension or image header (#9439), and
  request paths refuse COM0/LPT0 and superscript ports (#9424); the
  ambient-path gate adds `file.new` `profile` paths and working aliases, the
  `fileHandling.lutFolder` preference and
  `layer.layerStyle.contours.load/save` with a `path` (0.13.0) and
  `style.presets.importAsl/exportAsl` (0.16.0); since 0.14.0 (#8680) confined
  PSD/PSB/layered TIFF saves and layer exports write Linked smart objects as
  pixels and a linked source outside the gate counts as missing. Engine: 21
  command ids added, none removed or renamed (796 to 817 by a source count of
  the specs `build()` merges; the 0.12.0 bullet's 674 counted otherwise): the
  five `layer.layerStyle.contours.*`, `layer.xmpMetadata`, `layerComp.reorder`
  and four `tools.*Brush` (0.13.0), `style.presets.importAsl/exportAsl`,
  `type.fillPath`, `help.checkForUpdates` and `updates.status` (0.16.0;
  headless has no checker, so the check is disabled and nothing reaches the
  network), `history.options`, `paint.artHistoryBrush`, `brush.mixer.sample`
  and `type.font.favorite/library` (0.17.0). XCF and IFF open since 0.13.0,
  12-bit and arithmetic JPEG since 0.16.0; Cineon writes since 0.13.0, Amiga
  IFF since 0.17.0; batch "same" adds .xcf, .psdt and writer-less codecs to
  its PSD list; the 2^30 px flatten limit stands. The notes' optional local
  models (#1199) were reverted before the tag (`bb39b4a`). `release.yml` only
  moves `craft-fonts-ref`; since 0.16.0 the Linux packages, tarball included,
  carry man pages and shell completions, among them
  `share/bash-completion/completions/photocraft-cli`, which Storytold ignores
  since `6b61878`; the MSI installs per user by default. The release
  (2026-10-28 17:39 UTC) carries the three manifest assets at the manifest's
  byte sizes, GitHub's sha256 digests matching the pins, plus
  `SHA256SUMS.txt`. Card adds the 0.16.0 launch-option rules and the
  `PHOTOCRAFT_CONTROL_PORT` hazard, `doc_replace_smart_object`, `skipped`, the
  replace refusal, the confined `path`/`profile` refusals, linked smart
  objects as pixels, and `history.options`, and corrects a claim older than
  this range: `command_run` refuses `file.saveACopy`, `file.automate.batch`
  and every other `file.*` command outside a short in-document list as
  ambient-path commands (`crates/automation/src/workspace.rs`
  `authorize_engine_command`, already so at v0.12.0), so the card now points
  to `doc_open`, `doc_save` and `doc_export` instead.
- SoundCraft v0.14.0 (`c6befe5`; from v0.11.0 over v0.12.1 and v0.13.1, 231
  commits plus 117 merges; 0.12.0 (`2cfc56d`) and 0.13.0 (`1066784`) were
  bumped in `Cargo.toml` but never tagged or released, each followed within
  the hour by a patch release whose only addition is a release fix, macOS
  stapler retries (`239c78e`) and `contents: write` on the release job
  (`b48df2a`); Storytold pinned v0.12.1 in pull request #10 without this
  recheck and never pinned v0.13.1): `apps/soundcraft-cli` is now a library
  plus a thin binary parsed by clap (#1136; `args.rs`, `mcp.rs`), so
  `parse_mcp_args` and `automation_args.rs` are gone and the root flags live
  in `crates/automation/src/args.rs` (`AutomationArgs`, flags only, no
  environment variable). `mcp` takes `--connect`, `--demo` and both root flags
  with unchanged meaning, so the catalog launch parses as before; since 0.13.1
  (#979, `d01abd0`) each root flag may repeat, a path inside any root of its
  kind passing (`file_access.rs` holds a `Vec<Root>` per kind, a folder given
  twice counts once, a refusal with several names them all); since 0.14.0 an
  unknown flag, a stray argument, a repeated `--connect` or `--demo`,
  `--demo=1` and a root flag without a folder are clap usage errors (exit 2)
  before any root is opened, where v0.13.1 still ignored unknown flags through
  `_ => {}`, and `--connect` with a root or `--demo` is a conflict (exit 2).
  `crates/automation/src/mcp.rs`: the same 17 tools, seven APP_ONLY,
  `inspect_session` with optional `detail` and no required parameter, `batch`
  still `maxItems` 1000 refused before any call runs; the one schema change is
  the `bounce_mix` `format` enum, now `FileFormat::writable_extensions()`
  (wav, wave, bwf, aif, aiff, flac, which the engine already accepted).
  `docs/mcp.md` documents the repeatable roots and links the new `docs/cli.md`
  (exit codes; `SOUNDCRAFT_CONTROL_PORT` only for `app --port` and the desktop
  `--control`; no variable grants file access). `file_access.rs` is otherwise
  unchanged (absolute, links followed, whole components); `io.rs` is split
  into `io/` (`6401809`) with the same `check_read`/`check_write` call sites
  plus one in `file.import_audio` for audio the app decoded off the UI thread;
  the session save, backup and bounce writers are unchanged except that
  `file.export_session_text` needs `replace: true` over an existing file
  (#980), a bare save name is checked as the working directory against the
  write root (#947), and stored paths go through craft-docpath
  `resolve_absolute` (#826; same refusals, `crates/docpath` identical between
  the two craft-libs revisions). `bounce_mix` still has no replace guard.
  Engine: 479 to 481 command ids, nothing removed or renamed: new
  `clip.auto_rename` and the query `edit.strip_silence_preview`;
  `edit.strip_silence` takes `mode` strip|extract|separate and naming
  parameters, `clip.loop` `fill`, `audiosuite.process` `speed_ramp`,
  `file.bounce_stems` `dither`; `mix.send` refuses an unknown bus instead of
  creating one (#829, 0.12.1); track lists are deduped and `signal_generator`
  is capped by one sample budget across tracks (#996); 32-bit float WAV and
  AIFF keep finite samples above full scale (#792); a session with duplicate
  ids is refused on load (#586); new built-in plugins `auto_pan`, `ring_mod`
  and `subharmonic`; the bounce hot paths are faster without changing output
  (#1144). The desktop app gains a self-updater (`craft-update`), which the
  CLI does not link. `release.yml` only moves `contents: write` to the job
  (still `craft-common-actions` at `@main`); the Linux packages and tarballs
  now carry clap-generated man pages and bash, zsh and fish completions, so
  per `packaging/linux/package.sh` `soundcraft-0.14.0-linux-x86_64.tar.gz`
  holds `share/bash-completion/completions/soundcraft-cli` beside
  `bin/soundcraft-cli`, which the release workflow ignores since Storytold
  `6b61878`; the MSI defaults to a per-user `ArtCraft\SoundCraft` folder with
  the CLI still next to the app; appimagetool and the Windows signing client
  are pinned by hash. Release v0.14.0 (2026-10-28 16:08 UTC) carries the three
  manifest assets at the pinned byte sizes and SHA-256 digests plus
  `SHA256SUMS.txt`, and still no `freebsd-aarch64`. Card adds the repeatable
  roots, the 0.14.0 usage errors, the `mix.send` refusal, the Strip Silence
  modes and preview, the `file.export_session_text` guard and the float
  headroom.
- VectorCraft v0.18.0 (`68b68a3`; v0.15.0, v0.16.0 and v0.17.0 between, each
  bump in its own release commit, no untagged version; 1,685 commits): the
  `mcp` branch of `apps/vectorcraft-cli/src/main.rs` still takes `--connect
  ADDR`, `--headless` and both root flags (also `--flag=DIR`), refuses other
  options (`unknown mcp option`), `--connect` with `--headless` and roots
  with `--connect`, and roots still pick the confined headless backend
  (`confine_process`); since 0.15.0 each root flag may be repeated (#3546:
  the "given twice" refusal is gone, a path inside any root of its kind
  passes) and since 0.18.0 `-h`/`--help` outside a flag's value prints the
  usage instead of serving (#4063). `crates/mcp/src/server.rs`, `intake.rs`,
  `backend.rs` and `logging.rs` byte-identical (-32003 after 2 s,
  cancellation, the 256-step, 8 MiB and 16 MiB limits). `tools.rs` is split
  into `tools/{definitions,dispatch,handlers}.rs`: 33 tools, the 32 of
  0.14.0 in order plus the desktop-only `answer_dialog` (#4057), nothing
  removed or renamed; `doc_inspect` keeps `inspect_props()` with no required
  key and reports `opacityPct` beside the 0–1 `opacity` (#4149);
  `render_preview` and `screenshot` take `traceViews`, `save_file` takes
  `compress`, `version`, `preview` and `options` (#3955), `set_paint` answers
  `objects` (#4069), and `draw_path`/`draw_shape` run as one
  `command.batch`, one undo step a refused paint rolls back (#3545).
  `crates/engine/src/file_access.rs` keeps several roots per kind and names
  them all in its refusal; the 0.17.0 audits (#3897, #3933) bring the Place
  queue, clipboard files, placed-document workers, folder searches, the
  recovery folder (read and write) and stored link paths under the roots,
  refuse a non-UTF-8 path while confined and a device or pipe as a read,
  and make an atomic save owner-only when it cannot keep the replaced file's
  group or ACL; `headless.rs` renders previews as a PNG export on white
  (#3981). `docs/mcp.md` (4,453 to 5,341 lines; no `docs/agents.md`) adds
  `run --commands` (#3630), nearest-id answers for unknown command ids
  (#4060), atomic batches that also group documents a step opens or creates
  (#4016), heavy plug-in filters installed only with `allowHeavy: true`
  (#3721), EPS artboard exports that write a central `{stem}.eps` first
  (#3958), links on a drive mapped to another share counted as missing
  (#3321) and images past the 2 GiB decode allowance drawn at reduced size
  (#4269). `convert` to PDF drops the native attachment unless
  `--preserve-editing` (#4147, CLI only); the desktop self-updater
  (`craft-update`, #4138) is not linked into `vectorcraft-cli`.
  `release.yml` adds a `git-sources` job (git dependencies from storytold
  only) and job-level `contents: write`, still on `craft-common-actions@main`;
  AppImage tooling is hash-pinned and the MSI installs per user by default.
  Release v0.18.0 (2026-10-28 17:38 UTC, 28 assets, no FreeBSD aarch64)
  holds the three manifest assets at their byte sizes and SHA-256 digests
  plus `SHA256SUMS.txt`. Card adds repeatable roots, `answer_dialog`, the
  nearest command id, one-step `draw_*`, `opacityPct`, `set_paint` `objects`,
  the `save_file` options, the EPS central file, the batch scope, the
  mapped-drive refinement, the heavy plug-in rule, preview rendering and
  `traceViews`, and corrects the oversized-image sentence.
- WordCraft v0.12.0 (`3de6ff9`; v0.10.0 `9130181` and v0.11.0 `e31f2f0`
  between, 1,351 commits; the workspace version moves only in the three
  release commits, so no version went untagged): the `mcp` branch of
  `apps/wordcraft-cli/src/main.rs` keeps `MCP_OPTIONS` (`--connect`,
  `--author`), and `validate_options` (unknown options refused),
  `automation_roots` and `automation_args.rs` are byte-identical, so both root
  flags keep their meaning and roots or `--author` with `--connect` are still
  refused. Only `--connect` changed: a malformed `HOST:PORT` fails at startup,
  an unreachable app no longer stops the server (a lazy `Remote` retries on
  each call, #4078, 0.11.0), and the control key goes only to 127.0.0.1
  (#3699). `crates/mcp/src/tools.rs` lists 17 tools: `list_documents` is new
  (0.12.0), none removed or renamed; `execute`, `batch`, `type_text`,
  `select_text`, `get_text`, `inspect_document`, `render_page` and
  `save_document` gain an optional `doc` (`with_doc`), so the smoke tool
  `inspect_document` still has no required parameter. Several documents can
  now be open (`crates/engine/src/session/documents.rs`): `file.new`,
  `file.open`, `file.newFromTemplate`, mail merge without a path, labels and
  envelopes open beside the others and make theirs active, where 0.9.0
  replaced the session's document (`set_document`); `file.open` replaces only
  an untouched blank document and reactivates an open file without rereading
  it (`alreadyOpen`); `new_document` and `open_document` reply with its `id`;
  `file.closeDocument` (`id`, `force`) and `view.switchWindows` are new.
  `type_text` with `paragraphs` is one `text.insert` and undo step (#3973,
  0.11.0), each break an Enter, at most 10,000 lines (`MAX_TYPED_PARAGRAPHS`,
  0.12.0); `server.rs` answers a request line over 1 MiB with -32600
  (`MAX_REQUEST_LINE`, #3950); protocol versions unchanged. `docs/mcp.md` adds
  "Several documents", the lazy bridge and the root additions below; there is
  no `docs/agents.md` at either tag. `crates/engine/src/file_access.rs` now
  also checks, for a write, the directory entry a save replaces, so a link
  outside the write root that points into it is refused (#3735); an HTML
  file's pictures (#3736), the `file.options`
  `dictionariesFolder`/`userTemplatesFolder` and `file.listTemplates` folders
  (#3737) are held to the read root, and `font.add`/`font.remove` to the write
  root when a user font folder is set (#3692; the headless CLI sets none, so a
  font lasts for the session); `io/safe_save.rs` goes on when a GVFS share
  refuses a mode change (#3003, 0.10.0). Engine: 15 new command ids, none
  removed; an encrypted DOCX without `dataIntegrity` is refused (#4223) and
  `file.exportPng` refuses a path not ending in `.png` (#3837), both 0.11.0;
  `edit.replace`/`replaceAll` without text or an earlier search are errors
  (#3271); a protected document now checks `file.properties`,
  `file.privacyOptions` and inspector removals, and a formatting restriction
  refuses Copy Styles; `review.accept`/`reject` take `next`; `mailings.finish`
  takes `records`/`from`/`to`; label and envelope text is capped at 2,000
  characters, groups at 1,000 children, `review.compare` at 50 million LCS
  cells (the rest marked deleted and inserted); many parser, layout and font
  budgets. `release.yml` still delegates to `craft-common-actions` at `@main`
  (new `craft-fonts-ref`, `web-craft-fonts`); the MSI moves from `perMachine`
  to `perUserOrMachine` (#2560) and still installs `wordcraft-cli.exe` beside
  the app, Linux keeps `/usr/bin/wordcraft-cli`, macOS the separate CLI zip.
  The release keeps the three manifest assets at the manifest's byte sizes
  (GitHub's digests equal the pinned SHA-256) plus `SHA256SUMS.txt`, without
  `freebsd-aarch64`. Card adds `list_documents`, `doc` and the
  several-document rules, the `type_text` paragraph cap, the 1 MiB request
  line, the new read-root folders and the link-into-write-root refusal, the
  integrity-check refusal and the `.png`-only `file.exportPng`.

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
