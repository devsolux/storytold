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
install and pin the twelve CLIs on explicit command, stage files, generate
evidence-bound config and verify artifacts within stated limits. **No
thirteenth MCP server or second AI agent.**

```text
User + Claude Code / local Codex
           │  one craft Skill; native tool discovery and approvals
           ├── stdio ── PhotoCraft, VectorCraft, FilmCraft, LightCraft
           ├── stdio ── PdfCraft, EffectCraft, DesignCraft, GridCraft
           └── stdio ── WordCraft, DeckCraft, CADCraft, SoundCraft
                                │
                      native engines → durable files
```

**Release 1.2.1.** The offline core suite, the official MCP SDK contract test,
strict Claude manifest validation and Claude Code/Codex install with Skill
discovery have been run, and `setup` has installed, probed and
Sigstore-verified all twelve Craft CLIs on macOS, Linux and Windows runners as
well as a developer Mac; read [verification](docs/verification.md). Craft apps
are not bundled: installing the plugin installs guidance, the reviewed release
manifest and inactive templates, never binaries, permissions or running MCP
processes. Only the explicit `setup` command below installs and registers the
CLIs. Business use requires the local acceptance gates in
[acceptance](docs/acceptance.md).

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

A plugin update brings the Skill, docs and the refreshed release manifest; it
never touches installed CLIs or host registrations. Afterwards
`python3 storytold.py setup --list` shows which pins moved
(`manifest_commit_pinned: false`), and `setup --all --upgrade
--acknowledge-unconfined` re-downloads only those apps, re-probes them and
leaves registrations as they are. Before `plugin uninstall`,
`setup --remove --all` unregisters and deletes all twelve CLIs and their pins;
the workspace and its outputs stay.

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
claim native acceptance or publish anything. `make refresh-releases` and
`make sign-releases` are the network steps the daily workflow runs (the second
needs cosign); `make setup-confined` installs the four root-confined apps on
this machine. [Makefile](Makefile) lists all targets.

## Set up the native apps (one command)

Each app's MCP server is its CLI, `<app>-cli`. Installing the plugin or the
desktop app never provides or registers it, so until then the Skill correctly
reports that the app's native tools aren't connected. One explicit command fixes
that per app, or for all twelve, on macOS (universal), Linux x86_64 and Windows
x64:

```bash
python3 storytold.py setup --app photocraft
```

```bash
python3 storytold.py setup --all --acknowledge-unconfined
```

Run it from a clone or from the installed plugin directory (Codex:
`~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/`; Claude Code:
the plugin cache under `~/.claude/plugins/cache/`); `python3 storytold.py doctor`
prints the exact command, with the right path, for each app that is missing. For each app, `setup`
downloads the archive pinned for your platform in
[`config/releases.json`](config/releases.json) (the macOS CLI zip, the Linux
tarball or the Windows portable zip), checks it against that manifest **and**
the release's own `SHA256SUMS.txt`, takes exactly the one `<app>-cli` out of
it, checks provenance, installs it (`~/.local/opt/craft/bin`, or
`%LOCALAPPDATA%\Storytold\craft\bin` on Windows), pins the binary hash in a
private lock, probes initialize, tools/list and one read-only call through the
official MCP SDK, and registers the server with every host CLI on PATH
(`codex mcp add`, `claude mcp add --scope user`). Then start a new session.
Re-running `setup` is idempotent: an app whose installed binary matches its
pin and the manifest is skipped, a registration that already matches is kept.
`--dry-run` previews; `--list` shows manifest, installed, pinned and registered
state; `--upgrade` moves an app whose pin changed to the manifest release;
`--replace` re-registers a same-name server that points elsewhere;
`--skip-probe` registers without exercising the binary and says so;
`--remove` unregisters, deletes the binary and drops the pin. Nothing runs
unless you invoke it; Python 3.11+ is required.

**Provenance.** On macOS the binary must be Apple-notarized by the ArtCraft
team. Upstream does not code-sign Linux or Windows builds, so the
[daily workflow](.github/workflows/releases.yml) signs every pinned CLI keyless
with [Sigstore cosign](https://docs.sigstore.dev/) under its own GitHub
identity and commits the bundles to
[`config/signatures.json`](config/signatures.json); on Linux and Windows,
`setup` verifies that bundle with `cosign verify-blob` (install cosign first)
before installing, and macOS verifies it too when cosign is present. Until a
release has a bundle, or without cosign, `--trust-upstream-sums` proceeds on the
manifest and `SHA256SUMS.txt` alone and says so in the lock.

**Daily refresh.** The workflow checks every app's latest release each day,
rewrites the manifest, signs new CLIs, rebuilds the plugin, runs the checks and
the real `setup` on Linux, Windows and macOS runners, and opens one pull request
on `bot/releases` for review (set the repository variable
`STORYTOLD_AUTO_MERGE=true` to merge green runs automatically). Users get the
new pins with the next plugin update.

PhotoCraft, VectorCraft, EffectCraft and PdfCraft are confined to the workspace
by native root flags and register by default. The other eight can read and
write anything your user can, so they register only with
`--acknowledge-unconfined`: keep them for non-sensitive work or run them under
OS isolation. Other platforms, air-gapped machines and custom pins use the
manual chain in [operations](docs/operations.md): download, lock, `preflight`,
`probe`, `configure`, register.

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
| `config/` | Reviewed launch catalog, release manifest and Sigstore bundle store, inactive templates, example lock/env |
| `storytold_tools/`, `storytold.py` | Deterministic CLI and optional short-lived SDK probe |
| `scripts/`, `Makefile` | Offline checks, tests, guarded builds and packaging |
| `tests/` | Core regression tests, synthetic SDK fixture, native acceptance scenarios |
| `docs/` | Architecture, operations, security limits, sources and verification |
| `plugins/storytold/` | Generated shared runtime; never edit independently |
| `.github/workflows/` | Offline CI matrix and the daily release refresh, signing and three-OS verify |

[Architecture](docs/architecture.md) records why the native plan takes precedence
over the older gateway reference and which component owns what.

Devsolux integration; no affiliation or endorsement by the upstream `storytold`
organization, Anthropic or OpenAI is asserted. Released under the
[MIT License](LICENSE). Native apps, SDKs, fonts and media are not bundled and
keep their own licenses; see the [license notice](LICENSE-NOTICE.md).
