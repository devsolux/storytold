# Storytold

**Local creative work. Native app engines. Verified file handoffs.**

A Claude Code and Codex plugin for the open-source ArtCraft **Craft App Suite**:
one `craft` Skill drives thirteen local, headless Craft MCP apps (photo, vector,
video, RAW, PDF, layout, spreadsheets, documents, slides, CAD, audio, motion and
interface design) through staged copies and verified exports.

[![CI](https://github.com/devsolux/storytold/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/devsolux/storytold/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/devsolux/storytold)](https://github.com/devsolux/storytold/releases/latest)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**English** · [Deutsch](README.DE.md) · [Türkçe](README.TR.md)

> **Thank you, ArtCraft team!** Storytold is built on the Craft App Suite, which
> the [ArtCraft](https://getartcraft.com/) team released as free, open-source
> software: thirteen creative apps, each written from scratch. We're grateful for
> their generosity. None of this integration would exist without their work.
>
> ❤️ **ArtCraft team** 💚

## Contents

- [Overview](#overview)
- [Quick start](#quick-start)
- [The Craft App Suite](#the-craft-app-suite)
- [Setting up the native apps](#setting-up-the-native-apps)
- [Updating and removing](#updating-and-removing)
- [Where things live](#where-things-live)
- [Working safely](#working-safely)
- [Development](#development)
- [Verification status](#verification-status)
- [Repository map](#repository-map)
- [License and affiliation](#license-and-affiliation)

## Overview

Storytold is Devsolux's local integration kit for the thirteen existing Craft
CLI MCP servers. One compact `craft` Skill guides the host; each app keeps its
own schemas, editing state, rendering and save semantics. Deterministic helpers
install and pin the CLIs on explicit command, stage files, generate
evidence-bound configuration and verify artifacts within stated limits.

```text
User + Claude Code / local Codex
           │  one craft Skill; native tool discovery and approvals
           ├── stdio ── PhotoCraft, VectorCraft, FilmCraft, LightCraft
           ├── stdio ── PdfCraft, EffectCraft, DesignCraft, GridCraft
           ├── stdio ── WordCraft, DeckCraft, CADCraft, SoundCraft
           └── stdio ── FigCraft
                                │
                      native engines → durable files
```

**What it is**

- One instructional Skill, thirteen on-demand app cards and two workflow guides.
- Thirteen direct, native stdio MCP registrations, one per app and host.
- A standard-library Python CLI (`storytold.py`) that installs, verifies, pins,
  probes and registers the Craft CLIs, but only when you run it.

**What it is not**

- No gateway MCP server, daemon, router or second AI agent.
- No bundled binaries: installing the plugin adds guidance, the reviewed release
  manifest and inactive templates, never executables, permissions or running
  MCP processes.
- No remote ChatGPT connector. Local Codex support is an additive
  packaging and configuration adaptation.
- No OS sandbox. See [Working safely](#working-safely) and [SECURITY.md](SECURITY.md).

## Quick start

**1. Install the plugin.** Repository `devsolux/storytold`, plugin `storytold`,
marketplace `devsolux-storytold`. Both hosts take **plugin@marketplace**:

```bash
claude plugin marketplace add https://github.com/devsolux/storytold
claude plugin install storytold@devsolux-storytold

codex plugin marketplace add devsolux/storytold
codex plugin add storytold@devsolux-storytold
```

**2. Install the native apps.** From a clone, or from the installed plugin
directory (`<home>/plugins/cache/devsolux-storytold/storytold/<version>/` under
`~/.claude` or `~/.codex`), set up one app or all thirteen:

```bash
python3 storytold.py setup --app photocraft
```

```bash
python3 storytold.py setup --all --acknowledge-unconfined
```

**3. Start a new host session** and use the Skill: `/storytold:craft` in Claude
Code, or `storytold:craft` from the Codex Skill picker.

`python3 storytold.py doctor` reports, per app, the desktop app, CLI and host
registration it finds and prints the exact `setup` command for anything missing;
the Skill offers the same command in chat when a server is not connected.

## The Craft App Suite

ArtCraft Launcher installs the **Craft App Suite**: free, open-source creative
tools from the [ArtCraft](https://getartcraft.com/) team, each written from
scratch in Rust and each able to stand on its own. The **File access** column
shows how Storytold launches each app's MCP server.

| | App | What it's for | File access | Code | Learn more |
|:-:|---|---|---|---|---|
| <img src="https://raw.githubusercontent.com/storytold/photocraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.photocraft.png" alt="" width="32" height="32"> | **PhotoCraft** | Image editing: layers, masks, type and real PSD files | Read/write roots | [GitHub](https://github.com/storytold/photocraft) | [Website](https://getartcraft.com/apps/photocraft) |
| <img src="https://raw.githubusercontent.com/storytold/vectorcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.vectorcraft.png" alt="" width="32" height="32"> | **VectorCraft** | Vector illustration | Read/write roots | [GitHub](https://github.com/storytold/vectorcraft) | [Website](https://getartcraft.com/apps/vectorcraft) |
| <img src="https://raw.githubusercontent.com/storytold/filmcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.filmcraft.png" alt="" width="32" height="32"> | **FilmCraft** | Video editing, color and sound | User-wide | [GitHub](https://github.com/storytold/filmcraft) | [Website](https://getartcraft.com/apps/filmcraft) |
| <img src="https://raw.githubusercontent.com/storytold/lightcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.lightcraft.png" alt="" width="32" height="32"> | **LightCraft** | Photo library and raw development | User-wide | [GitHub](https://github.com/storytold/lightcraft) | [Website](https://getartcraft.com/apps/lightcraft) |
| <img src="https://raw.githubusercontent.com/storytold/pdfcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.pdfcraft.png" alt="" width="32" height="32"> | **PdfCraft** | Reading, organizing and protecting PDFs | Read/write roots | [GitHub](https://github.com/storytold/pdfcraft) | [Website](https://getartcraft.com/apps/pdfcraft) |
| <img src="https://raw.githubusercontent.com/storytold/effectcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.effectcraft.png" alt="" width="32" height="32"> | **EffectCraft** | Motion graphics and visual effects | Read/write roots | [GitHub](https://github.com/storytold/effectcraft) | [Website](https://getartcraft.com/apps/effectcraft) |
| <img src="https://raw.githubusercontent.com/storytold/designcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.designcraft.png" alt="" width="32" height="32"> | **DesignCraft** | Page layout and publishing | Read/write roots | [GitHub](https://github.com/storytold/designcraft) | [Website](https://getartcraft.com/apps/designcraft) |
| <img src="https://raw.githubusercontent.com/storytold/gridcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.gridcraft.png" alt="" width="32" height="32"> | **GridCraft** | Spreadsheets and data | User-wide | [GitHub](https://github.com/storytold/gridcraft) | [Website](https://getartcraft.com/apps/gridcraft) |
| <img src="https://raw.githubusercontent.com/storytold/wordcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.wordcraft.png" alt="" width="32" height="32"> | **WordCraft** | Word processing and documents | Read/write roots | [GitHub](https://github.com/storytold/wordcraft) | [Website](https://getartcraft.com/apps/wordcraft) |
| <img src="https://raw.githubusercontent.com/storytold/deckcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.deckcraft.png" alt="" width="32" height="32"> | **DeckCraft** | Presentations and slide decks | Read/write roots | [GitHub](https://github.com/storytold/deckcraft) | [Website](https://getartcraft.com/apps/deckcraft) |
| <img src="https://raw.githubusercontent.com/storytold/cadcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.cadcraft.png" alt="" width="32" height="32"> | **CADCraft** | Computer-aided design | User-wide | [GitHub](https://github.com/storytold/cadcraft) | [Website](https://getartcraft.com/apps/cadcraft) |
| <img src="https://raw.githubusercontent.com/storytold/soundcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.soundcraft.png" alt="" width="32" height="32"> | **SoundCraft** | Audio recording and editing | Read/write roots | [GitHub](https://github.com/storytold/soundcraft) | [Website](https://getartcraft.com/apps/soundcraft) |
| <img src="https://raw.githubusercontent.com/storytold/figcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.figcraft.png" alt="" width="32" height="32"> | **FigCraft** | Interface design and prototyping | Read/write roots | [GitHub](https://github.com/storytold/figcraft) | [Website](https://getartcraft.com/apps/figcraft) |

- **Read/write roots** (nine apps): launched with native root flags that let
  them read the workspace and write only its `outputs/` directory. PdfCraft
  also keeps its single `--root` on the workspace; both apply.
- **User-wide** (four apps): launched without file-root flags, so they can
  read and write anything your OS user can. `setup` installs and registers
  them only with `--acknowledge-unconfined`; keep them for non-sensitive work
  or run them under OS isolation.

## Setting up the native apps

Each app's MCP server is its CLI, `<app>-cli`. Neither the plugin nor the
desktop app provides or registers it, so until it is set up the Skill correctly
reports that the app's native tools aren't connected. `setup` supports macOS
(universal), Linux x86_64 and Windows x64 and requires Python 3.11+.

### What `setup` does

For each selected app, `setup`:

1. Downloads the archive pinned for your platform in
   [`config/releases.json`](config/releases.json) (the macOS CLI zip, the Linux
   tarball or the Windows portable zip).
2. Checks it against that manifest **and** the release's own `SHA256SUMS.txt`,
   then extracts exactly the one `<app>-cli`.
3. Verifies provenance (see [Provenance](#provenance)).
4. Stages the candidate beside the active install and runs preflight plus the
   official MCP SDK probe against it: initialize, tools/list and one read-only
   call.
5. Promotes it only then, to `~/.local/opt/craft/bin` (or
   `%LOCALAPPDATA%\Storytold\craft\bin` on Windows), and pins the binary hash in
   a private lock.
6. Registers the server with every host CLI on PATH (`codex mcp add`,
   `claude mcp add --scope user`).

A candidate that fails any step leaves the previous binary, its pin and the
registrations untouched; an upgrade interrupted between the file replace and the
lock rewrite is reconciled by the next run. Re-running `setup` is idempotent: an
app whose installed binary matches its pin and the manifest is skipped, and a
matching registration is kept. Nothing runs unless you invoke it. Start a new
host session afterwards.

### Options

| Option | Effect |
|---|---|
| `--app <app>` / `--all` | Select one app (repeatable) or all thirteen. |
| `--acknowledge-unconfined` | Also install and register the four user-wide apps. Not evidence of isolation. |
| `--host {codex,claude}` | Register with the named host only (default: every host CLI on PATH); a named host that is not on PATH fails the run. |
| `--dry-run` | Preview what a real run would do per app (`keep`, `install`, `upgrade`, `skip` or `refuse`, a download only where one is needed, each registration) and whether it would pass (exit status 1 if not), or, with `--remove`, exactly what would be removed. Changes nothing. |
| `--list` | Show manifest, installed, pinned and registered state, and the paths in use. |
| `--upgrade` | Move an app whose pin changed to the manifest release. |
| `--replace` | Re-register a same-name server that points elsewhere; the old entry is restored if the new one cannot be added. |
| `--remove` | Unregister only the user-scope entries `setup` itself wrote (same command and arguments, app still pinned) and delete only a binary whose bytes match the lock and that no remaining registration launches, on any host; anything else is reported and left alone. |
| `--skip-probe` | Register without exercising the binary, and say so. |
| `--trust-upstream-sums` | Linux/Windows: proceed on the manifest and `SHA256SUMS.txt` when no Sigstore bundle or cosign is available; recorded in the lock. |

`python3 storytold.py setup --help` lists the remaining path and timeout
overrides. Other platforms, air-gapped machines and custom pins use the manual
chain in [operations](docs/operations.md): download, lock, `preflight`, `probe`,
`configure`, register.

### Provenance

On macOS the binary must be Apple-notarized by the ArtCraft team. Upstream does
not code-sign Linux or Windows builds, so the
[daily workflow](.github/workflows/releases.yml) signs every pinned CLI keyless
with [Sigstore cosign](https://docs.sigstore.dev/) under its own GitHub identity
and commits the bundles to [`config/signatures.json`](config/signatures.json).
On Linux and Windows, `setup` verifies that bundle with `cosign verify-blob`
(install cosign first) before installing; macOS verifies it too when cosign is
present. Until a release has a bundle, or without cosign,
`--trust-upstream-sums` proceeds on the manifest and `SHA256SUMS.txt` alone and
says so in the lock.

### Daily release refresh

The workflow checks every app's latest release each day, rewrites the manifest,
signs new CLIs, rebuilds the plugin, runs the checks and the real `setup` on
Linux, Windows and macOS runners, and opens one pull request on `bot/releases`
for review (set the repository variable `STORYTOLD_AUTO_MERGE=true` to merge
green runs automatically). Users receive the new pins with the next plugin
update.

## Updating and removing

### Update

Updating takes two steps. First, update the plugin:

```bash
claude plugin marketplace update devsolux-storytold
claude plugin update storytold@devsolux-storytold

codex plugin marketplace upgrade devsolux-storytold
codex plugin add storytold@devsolux-storytold
```

Codex has no `plugin update`: `marketplace upgrade` refreshes the Git snapshot
and running `plugin add` again installs the newer version from it. A plugin
update brings the Skill, docs and the refreshed release manifest; it never
touches installed CLIs or host registrations, and the plugin directory now
carries the new version number.

Second, move the Craft CLIs. `--list` shows which pins moved
(`manifest_commit_pinned: false`); `--all --upgrade` re-downloads only those
apps, verifies and re-probes them, and leaves registrations as they are:

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --list
```

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --all --upgrade --acknowledge-unconfined
```

When a release changes an app's launch arguments (WordCraft's root flags in
1.5.0, SoundCraft's in 1.5.2, and DeckCraft's, DesignCraft's, FigCraft's and
PdfCraft's in 1.5.4), add `--replace` so the differing registration is
re-registered; without it `setup` reports the difference and leaves it alone.
SoundCraft honours its roots only from 0.7.0, so an older installed SoundCraft
is refused until `setup --app soundcraft --upgrade --replace` moves it; the
same holds for DeckCraft before 0.8.0, DesignCraft before 0.9.0, FigCraft
before 0.7.0 and PdfCraft before 0.9.0, which refuse the flags.

### Remove

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --remove --all
claude plugin uninstall storytold@devsolux-storytold
codex plugin remove storytold@devsolux-storytold
```

`setup --remove --all` first unregisters and deletes the thirteen
Storytold-managed CLIs and their pins. The workspace and its outputs stay, and so
does anything the lock cannot prove Storytold installed. Uninstalling the plugin
alone would leave the servers registered and running.

### Install from a source checkout

The generated `plugins/storytold/` runtime is committed, so both hosts install
straight from the public repository and nothing is built during installation.
From a source checkout, `make install-claude-local` or `make install-codex-local`
installs the local marketplace instead. These targets change host state; builds
and tests never run them. Host packaging and installation sources are recorded
in the [source ledger](docs/source-ledger.md).

## Where things live

The plugin directory holds code, docs and the release manifest only. `setup`
keeps everything it installs outside it, so a plugin update or uninstall can
never delete, downgrade or swap a CLI, and one installed copy serves both hosts.
`python3 storytold.py setup --list` prints the paths in use.

| Where (macOS/Linux) | Windows | What | Written by |
|---|---|---|---|
| `~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/`, same under `~/.claude` | same under `%USERPROFILE%` | The plugin: `craft` Skill, docs, `storytold.py`, `config/releases.json`, `config/signatures.json`. No binaries. | `codex plugin add` / `claude plugin install` |
| `~/.local/opt/craft/bin/` | `%LOCALAPPDATA%\Storytold\craft\bin\` | The thirteen Craft CLIs (`photocraft-cli` … `figcraft-cli`, 16–192 MB each). Both hosts launch these, e.g. `…/cadcraft-cli mcp`. | `setup` |
| `~/.local/state/storytold/` (`$XDG_STATE_HOME/storytold` on Linux) | `%LOCALAPPDATA%\Storytold\state\` | Private state: `installations.lock.json` (pinned hashes), `evidence/` (probe receipts per app), `venv/` (official MCP SDK for the probe), `setup.json` (recorded paths). | `setup` |
| `~/craft-work-storytold/` | `%USERPROFILE%\craft-work-storytold\` | The workspace: `inputs/`, `outputs/` (exports land here), `receipts/`. | `setup` creates it; the apps fill `outputs/` |
| `~/.codex/config.toml` and `~/.claude.json` | same | One user-scope MCP registration per app and host, pointing at the absolute CLI path above. | `codex mcp add`, `claude mcp add --scope user`, run by `setup` |

The complete Unix launch templates under `config/` are examples only, not
active host configuration. Real config generation chooses `.exe` on native
Windows and emits concrete, validated paths rather than relying on environment
expansion behaving identically across hosts. Machine-specific configuration
stays out of packages.

## Working safely

Every task follows the same loop:

**Inspect → staged copy → native edit → preview → save/export → reopen/verify.**

- **App cards.** The [thirteen app cards](skills/craft/SKILL.md) describe
  app-specific pitfalls: VectorCraft headless selection, LightCraft library
  locks, PdfCraft explicit saves, DesignCraft UTF-8 byte offsets, GridCraft typed
  formulas, FigCraft page-unit coordinates, media timing and offline warnings.
  They are source-derived hints; the connected binary supplies the operative API.
- **Cross-app work.** Pass verified files, never another server's in-memory IDs.
  PhotoCraft can export a PNG for DesignCraft; DesignCraft can export a PDF for
  PdfCraft. If a stage fails, stop at the last verified artifact. No universal
  batch transaction, automatic write retry or hidden fallback is promised.
- **Confinement.** Root flags, the Skill, probe receipts and MCP configuration
  are not an OS sandbox, and other host shell and file tools need appropriate
  permissions too. Business use requires the local gates in
  [acceptance](docs/acceptance.md) and the controls in [SECURITY.md](SECURITY.md).

## Development

Python **3.11+** runs the core tools and tests; GNU Make is optional
convenience. The default checks and build need no third-party Python packages
and no network access.

```bash
make check
make test
make build
make verify-build
```

| Target | Purpose |
|---|---|
| `make help` | List every target; installs and starts nothing. |
| `make doctor` | Report installed capabilities without starting hosts or native apps. |
| `make check` | Validate source, links, identities, catalog, examples and inactive packaging. |
| `make test` | Run all core tests in an isolated source copy; no network or native binaries. |
| `make build` / `make verify-build` | Generate the shared plugin from allowlisted canonical files, then check it for drift. |
| `make package` / `make source` | Create the deterministic plugin ZIP and the complete source ZIP, each with a checksum. |
| `make release` | Ordered checks, core tests and reproducible packaging; no publishing or native acceptance claim. |
| `make setup` / `make setup-probe` | Create a local `.venv`; then, as an explicit network opt-in, install the hash-locked official MCP SDK (`mcp==2.3.0`). |
| `make test-sdk` | Exercise the real SDK against a synthetic stdio fixture, not the Craft apps. |
| `make refresh-releases` / `make sign-releases` | The network steps the daily workflow runs (signing needs cosign). |
| `make setup-confined` | Install, pin, probe and register the nine root-confined apps on this machine. |
| `make clean` | Remove only marked `.build/` and `dist/`; workspaces and `.venv` stay. |

Builds and tests never commit, push or install; only the explicitly named
`make github-*` targets commit or push. The [Makefile](Makefile) lists every
target, and [CONTRIBUTING.md](CONTRIBUTING.md) describes the contribution rules.

## Verification status

The offline core suite, the official MCP SDK contract test, strict Claude
manifest validation, and Claude Code and Codex installation with Skill
discovery have been run. `setup` has installed, probed and Sigstore-verified all
thirteen Craft CLIs on macOS, Linux and Windows runners, and twelve of them on a
developer Mac as well. That is protocol-level evidence, not native acceptance:
the gates in [acceptance](docs/acceptance.md) remain the operator's to run. The
[verification report](docs/verification.md) separates what was executed for
each release from documentary evidence.

## Repository map

| Path | Responsibility |
|---|---|
| `skills/craft/` | One instructional Skill, thirteen app cards and two workflows |
| `config/` | Reviewed launch catalog, release manifest and Sigstore bundle store, inactive templates, example lock and env |
| `storytold_tools/`, `storytold.py` | Deterministic CLI and optional short-lived SDK probe |
| `scripts/`, `Makefile` | Offline checks, tests, guarded builds and packaging |
| `tests/` | Core regression tests, synthetic SDK fixture, native acceptance scenarios |
| `docs/` | Architecture, operations, acceptance, sources and verification |
| `plugins/storytold/` | Generated shared runtime; never edit it directly |
| `.github/workflows/` | Offline CI matrix and the daily release refresh, signing and three-OS verification |

[Architecture](docs/architecture.md) records why the native plan takes
precedence over the older gateway reference and which component owns what.

## License and affiliation

Released under the [MIT License](LICENSE). Native apps, SDKs, fonts and media are
not bundled and keep their own licenses; see the
[license notice](LICENSE-NOTICE.md).

Storytold is a Devsolux integration. No affiliation with or endorsement by the
upstream `storytold` organization, Anthropic or OpenAI is asserted.
