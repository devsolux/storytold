# Storytold

Claude Code & Codex plugin for the open-source ArtCraft Craft App Suite: one
`craft` Skill drives 12 local, headless Craft MCP apps (photo, vector, video,
RAW, PDF, layout, sheets, docs, slides, CAD, audio, motion) with staged copies
and verified exports.

> **Thank you, ArtCraft team!** Storytold is built on the Craft App Suite, which
> the [ArtCraft](https://getartcraft.com/) team released as free, open-source
> software: twelve creative apps, each written from scratch. We're grateful for
> their generosity. None of this integration would exist without their work.
>
> ❤️ **ArtCraft team** 💚

**Local creative work. Native app engines. Verified file handoffs.**

Storytold is Devsolux's local integration kit for twelve existing Craft CLI MCP
servers. One compact `craft` Skill guides the host; the apps keep their own
schemas, editing state, rendering and save semantics. Deterministic helpers
handle installation checks, file staging, evidence-bound config generation and
limited artifact verification. **No thirteenth MCP server or second AI agent.**

```text
User + Claude Code / local Codex
           │  one craft Skill; native tool discovery and approvals
           ├── stdio ── PhotoCraft, VectorCraft, FilmCraft, LightCraft
           ├── stdio ── PdfCraft, EffectCraft, DesignCraft, GridCraft
           └── stdio ── WordCraft, DeckCraft, CADCraft, SoundCraft
                                │
                      native engines → durable files
```

**Release 1.0.1.** The offline core suite, the official MCP SDK contract test,
strict Claude manifest validation and Claude Code/Codex install with Skill
discovery have been run. Craft apps are not bundled and need your own pinned
builds; PhotoCraft 0.7.0 has passed the native discovery and smoke-call probe on
macOS, the other eleven have not been run. Read [verification](docs/verification.md).
Installing the plugin installs guidance and inactive templates, not Craft apps,
permissions, executable pins or automatically running MCP processes. Business
use requires the local acceptance gates in [acceptance](docs/acceptance.md).

## Install the Skill/plugin

Repository `devsolux/storytold` · plugin `storytold` · marketplace
`devsolux-storytold`. Both hosts take **plugin@marketplace**:

```bash
claude plugin marketplace add https://github.com/devsolux/storytold
claude plugin install storytold@devsolux-storytold

codex plugin marketplace add devsolux/storytold
codex plugin add storytold@devsolux-storytold
```

Update or remove later:

```bash
claude plugin marketplace update devsolux-storytold
claude plugin update storytold@devsolux-storytold
claude plugin uninstall storytold@devsolux-storytold

codex plugin marketplace upgrade devsolux-storytold
codex plugin remove storytold@devsolux-storytold
```

The generated `plugins/storytold/` runtime is committed, so both hosts install
straight from the public repository; nothing is built during installation. From
a source checkout, `make install-claude-local` or `make install-codex-local`
installs the local marketplace instead. These commands change host state; builds
and tests never run them, and only the explicit `make github-*` targets commit
or push.

Claude Code exposes the Skill as `/storytold:craft`; Codex lists it as
`storytold:craft` in its Skill picker. Use one native MCP registration per app.
Local Codex support is an additive packaging/configuration adaptation, **not** a
remote ChatGPT connector. Host packaging and installation sources are recorded in
[source ledger](docs/source-ledger.md).

## Craft App Suite

ArtCraft Launcher installs the **Craft App Suite**: free, open-source creative tools from the
[ArtCraft](https://getartcraft.com/) team, each written from scratch in Rust and each able to
stand on its own.

| | App | What it's for | Code | Learn more |
|:-:|---|---|---|---|
| <img src="https://raw.githubusercontent.com/storytold/photocraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.photocraft.png" alt="" width="32" height="32"> | **PhotoCraft** | Image editing: layers, masks, type and real PSD files | [GitHub](https://github.com/storytold/photocraft) | [Website](https://getartcraft.com/apps/photocraft) |
| <img src="https://raw.githubusercontent.com/storytold/vectorcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.vectorcraft.png" alt="" width="32" height="32"> | **VectorCraft** | Vector illustration | [GitHub](https://github.com/storytold/vectorcraft) | [Website](https://getartcraft.com/apps/vectorcraft) |
| <img src="https://raw.githubusercontent.com/storytold/filmcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.filmcraft.png" alt="" width="32" height="32"> | **FilmCraft** | Video editing, color and sound | [GitHub](https://github.com/storytold/filmcraft) | [Website](https://getartcraft.com/apps/filmcraft) |
| <img src="https://raw.githubusercontent.com/storytold/lightcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.lightcraft.png" alt="" width="32" height="32"> | **LightCraft** | Photo library and raw development | [GitHub](https://github.com/storytold/lightcraft) | [Website](https://getartcraft.com/apps/lightcraft) |
| <img src="https://raw.githubusercontent.com/storytold/pdfcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.pdfcraft.png" alt="" width="32" height="32"> | **PdfCraft** | Reading, organizing and protecting PDFs | [GitHub](https://github.com/storytold/pdfcraft) | [Website](https://getartcraft.com/apps/pdfcraft) |
| <img src="https://raw.githubusercontent.com/storytold/effectcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.effectcraft.png" alt="" width="32" height="32"> | **EffectCraft** | Motion graphics and visual effects | [GitHub](https://github.com/storytold/effectcraft) | [Website](https://getartcraft.com/apps/effectcraft) |
| <img src="https://raw.githubusercontent.com/storytold/designcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.designcraft.png" alt="" width="32" height="32"> | **DesignCraft** | Page layout and publishing | [GitHub](https://github.com/storytold/designcraft) | [Website](https://getartcraft.com/apps/designcraft) |
| <img src="https://raw.githubusercontent.com/storytold/gridcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.gridcraft.png" alt="" width="32" height="32"> | **GridCraft** | Spreadsheets and data | [GitHub](https://github.com/storytold/gridcraft) | [Website](https://getartcraft.com/apps/gridcraft) |
| <img src="https://raw.githubusercontent.com/storytold/wordcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.wordcraft.png" alt="" width="32" height="32"> | **WordCraft** | Word processing and documents | [GitHub](https://github.com/storytold/wordcraft) | [Website](https://getartcraft.com/apps/wordcraft) |
| <img src="https://raw.githubusercontent.com/storytold/deckcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.deckcraft.png" alt="" width="32" height="32"> | **DeckCraft** | Presentations and slide decks | [GitHub](https://github.com/storytold/deckcraft) | [Website](https://getartcraft.com/apps/deckcraft) |
| <img src="https://raw.githubusercontent.com/storytold/cadcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.cadcraft.png" alt="" width="32" height="32"> | **CADCraft** | Computer-aided design | [GitHub](https://github.com/storytold/cadcraft) | [Website](https://getartcraft.com/apps/cadcraft) |
| <img src="https://raw.githubusercontent.com/storytold/soundcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.soundcraft.png" alt="" width="32" height="32"> | **SoundCraft** | Audio recording and editing | [GitHub](https://github.com/storytold/soundcraft) | [Website](https://getartcraft.com/apps/soundcraft) |

## Develop without network access

Python **3.11+** runs the core tools and tests; GNU Make is optional convenience.
No third-party Python dependencies are needed for the default checks/build.

```bash
make help
make doctor
make check
make test
make build
make verify-build
make package
make source
make clean
```

`make setup` creates only a local virtual environment. `make setup-probe` is an
explicit network opt-in for `mcp==2.3.0`; then `make test-sdk` checks the real SDK
against a clearly synthetic stdio fixture. It does not run the twelve Craft apps.
`make release` orders checks, core tests and reproducible packaging; it does not
claim native acceptance or publish anything. [Makefile](Makefile) lists all targets.

## Configure the native apps locally

Follow [operations](docs/operations.md) in order. Keep the app binaries outside
this repository and outside the writable workspace. Obtain/build them from
reviewed immutable upstream revisions; no installer/downloader is supplied.

> **The desktop app is not an MCP server.** Each app's MCP server is its CLI,
> `<app>-cli`. On macOS the ArtCraft Launcher and the `.dmg` install only the
> `.app`; the CLI is a separate `<app>-cli-<version>-macos-universal.zip` release
> asset. Windows MSI/portable ZIP and Linux `.deb`/`.rpm` packages include it.
> Until it is installed **and** registered with your host, the Skill correctly
> reports that the app's native tools aren't connected.

1. Install each app's `<app>-cli` from its upstream release and verify the
   published checksum and signature ([operations, section 0](docs/operations.md#0-get-each-apps-cli-not-only-the-desktop-app)).
2. Create a new private workspace with `storytold.py workspace-init` and set
   `CRAFT_BIN_DIR`, `CRAFT_WORK_ROOT`, and `CRAFT_OUTPUT_ROOT` to absolute paths.
3. Use `inventory` to hash executables **without executing them**. Populate a
   private installation lock with trusted source revisions, build versions and
   verified binary hashes; the example lock intentionally fails validation.
4. Run `preflight`. Explicitly acknowledge any OS-only apps for non-sensitive
   testing, or run under a genuinely tested OS-isolated environment.
5. With the optional SDK installed, `probe` each app for initialization, paginated
   discovery and one explicitly reviewed fixture-only smoke call. Missing apps,
   hash changes, absent schemas, tool errors and timeouts are not success.
6. Generate a **new** Claude project `.mcp.json` or Codex TOML configuration from
   matching native probe evidence. Existing files are never overwritten/merged.
   Register it in the host (Codex: `~/.codex/config.toml` or a trusted project's
   `.codex/config.toml`), start a new session, then complete M0–M3 and host acceptance.

Tools still missing? `python3 storytold.py doctor` reports, without executing
anything, which apps have only the desktop app, a CLI without a host
registration, or a registration whose binary is gone. See
[troubleshooting](docs/operations.md#troubleshooting-native-tools-arent-connected).

The complete Unix launch templates are under `config/`. They are examples only,
not active host configuration. Real config generation chooses `.exe` on native
Windows and emits concrete validated paths rather than hoping env expansion
works identically across hosts. Machine-specific config stays out of packages.

## Safe creative workflow

**Inspect → staged copy → native edit → preview → save/export → reopen/verify.**

The [twelve app cards](skills/craft/SKILL.md) describe special pitfalls: VectorCraft
headless selection, LightCraft library locks, PdfCraft explicit saves, DesignCraft
UTF-8 byte offsets, GridCraft typed formulas, media timing and offline warnings.
These are source-derived hints; the connected binary supplies the operative API.

For cross-app work, pass verified files—not another server's in-memory IDs.
PhotoCraft can export a PNG for DesignCraft; DesignCraft can export a PDF for
PdfCraft. Stop at the last verified artifact if a stage fails. No universal batch
transaction, automatic write retry, or hidden fallback is promised.

Three apps have source-documented separate read/write roots; PdfCraft has one
root; eight apps must be treated as OS-user-wide. Neither the Skill, probe
receipts nor MCP config is an OS sandbox. Other host shell/file tools also need
appropriate permissions. See [security](SECURITY.md).

## Repository map

| Path | Responsibility |
|---|---|
| `skills/craft/` | One instructional Skill, twelve app cards and two workflows |
| `config/` | Reviewed launch catalog, inactive templates, example lock/env |
| `storytold_tools/`, `storytold.py` | Deterministic CLI and optional short-lived SDK probe |
| `scripts/`, `Makefile` | Offline checks, tests, guarded builds and packaging |
| `tests/` | Core regression tests, synthetic SDK fixture, native acceptance scenarios |
| `docs/` | Architecture, operations, security limits, sources and verification |
| `plugins/storytold/` | Generated shared runtime; never edit independently |

[Architecture](docs/architecture.md) records why the native plan takes precedence
over the older gateway reference and which component owns what.

Devsolux integration; no affiliation or endorsement by the upstream `storytold`
organization, Anthropic or OpenAI is asserted. Released under the
[MIT License](LICENSE). Native apps, SDKs, fonts and media are not bundled and
keep their own licenses; see the [license notice](LICENSE-NOTICE.md).
