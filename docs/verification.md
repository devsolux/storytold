# Verification status — 1.5.1

Native application and host *acceptance* (M0–M4) remain **not run**: this
repository neither ships nor executes Craft binaries. All thirteen CLIs have
passed the native probe through operator- or runner-run `setup` (tables
below): twelve on a developer Mac and on GitHub runners, FigCraft (added in
1.4.0) on the three GitHub runners only. That is M0-level evidence, not
acceptance. This report separates the checks actually executed for each
release from documentary evidence.

## Executed for 1.5.0 and 1.5.1 — October 14, 2026

Same machine and gates as 1.4.1 (`make release`, `make test-sdk`,
`make host-validate`; the counts in the table below are from this run). The
reviewed catalog change confines WordCraft with `--automation-read-root` and
`--automation-write-root`, so the local binary acceptance that a flag change
requires ran on this Mac:

| Step | Result |
|---|---|
| `preflight --app wordcraft` | Launch resolved to the pinned `wordcraft-cli` 0.6.1 (notarized `DJ6XS33FX8`, Sigstore) with `mcp --automation-read-root ~/craft-work-storytold --automation-write-root ~/craft-work-storytold/outputs`; no `--acknowledge-unconfined` needed any more. |
| `probe --app wordcraft --confirm-execution` with the approved `inspect_document` call | The binary announced `files confined: read root …, write root …` on stderr, negotiated protocol `2025-06-18` as server `wordcraft` 0.6.1, listed 16 tools and answered `inspect_document` with `isError: false`; the evidence file was written outside the workspace and is not committed. |

The operator then ran the documented upgrade on the same Mac:

| Step | Result |
|---|---|
| `setup --app wordcraft --upgrade --replace` | Downloaded `wordcraft-cli-0.7.0-macos-universal.zip` (archive hash matched the manifest and upstream sums; notarized `DJ6XS33FX8`; Sigstore bundle verified with cosign), probed the staged candidate with the new arguments (protocol `2025-06-18`, server `wordcraft` 0.7.0, 16 tools, `inspect_document` answered), promoted it over 0.6.1, probed it again at the installed path, and in both Codex and Claude Code removed the previous user-scope entry and registered the root-flag launch; the previous entry would have been restored had the new one failed. Lock pinned to v0.7.0 (`fc419188…`); `setup --list` reports it installed, owned, pinned to the manifest commit and registered with both hosts. |

The release workflow's run 38588658915, triggered by hand after the push, then
ran `setup --all --acknowledge-unconfined` with the new WordCraft launch on
`ubuntu-latest`, `windows-latest` and `macos-latest`: WordCraft 0.7.0 was
installed, probed and pinned with the root arguments on all three, PdfCraft
0.8.0 came from its new standalone Linux CLI tarball, and the run merged pull
request #3 (`6fee7db`: DeckCraft 0.7.0, PdfCraft 0.8.0, VectorCraft 0.11.0;
cards rechecked, see the [source ledger](source-ledger.md)). Still not done:
no path outside a root was tried (denial is an M3 test), and host sessions
opened before the re-registration keep the old launch until restarted.

## Executed for 1.4.0 and 1.4.1 — October 14, 2026

macOS (Darwin 27, arm64) with Python **3.11.17** (`.venv`):

| Gate | Result |
|---|---|
| `make check` | Passed **71 check entries**: parsed 46 files (33 Python, 12 JSON, one TOML), checked 167 local Markdown links in source, translations and plugin, validated the thirteen-app catalog with its exact launch flags, the three-platform release manifest (now pinning FigCraft v0.5.1), the signature store, the release workflow rules and 15 native scenario definitions without executing any. |
| `make test` | **223 tests** passed in an isolated source copy, zero failures, errors or skips; the catalog, CLI, status, manifest, signature-rotation and strict-provenance tests now assert thirteen apps and 39 pinned archives. |
| `make build`, `make verify-build` | The generated plugin (51 files) matches its 91 allowlisted canonical inputs, including the new FigCraft card. |
| `make package`, `make source` | Reproducible 1.4.0 plugin and source ZIPs with SHA-256 files. |
| `make test-sdk` with `mcp==2.3.0` | Passed the same 7 checks against the synthetic stdio fixture as before; no Craft binary involved. |
| `make host-validate` (Claude Code 2.1.282) | `claude plugin validate --strict` passed for the 1.4.0 marketplace and plugin manifests. |
| `doctor`, `apps`, `setup --app figcraft --dry-run` | The read-only commands list thirteen apps; FigCraft reports `not_installed` with the `--acknowledge-unconfined` setup command, and the dry run names the macOS CLI zip, the install path and both host registrations, with `sigstore_bundle: false`. Nothing was downloaded or registered by these commands. |
| FigCraft release inspection | `figcraft-cli-0.5.1-macos-universal.zip`, `figcraft-0.5.1-linux-x86_64.tar.gz` and `figcraft-0.5.1-windows-x64-portable.zip` were downloaded into a scratch directory and matched both the manifest and the release's `SHA256SUMS.txt`; each archive lists exactly one `figcraft-cli` (`bin/figcraft-cli` in the tarball, `figcraft-cli.exe` in the portable ZIP, a 159 MB universal x86_64/arm64 binary on macOS). `codesign` and `spctl` report the macOS CLI as *Notarized Developer ID*, team `DJ6XS33FX8`. The binary was not executed; no `setup`, probe or host registration ran for FigCraft. |
| Upstream source review | FigCraft `main`: CLI parser (`mcp [--attach PORT]`, the global `--no-system-fonts`, no file-root flag), MCP documentation and tool definitions (18 tools; `inspect_document` has only optional parameters), packaging and release assets; see the [source ledger](source-ledger.md). |

Not run locally for 1.4.0 and 1.4.1: the host installs from the local marketplace and
any native `setup`, upgrade or removal on this Mac; the 1.3.2 results below
still describe the twelve binaries installed here, which 1.4.0 does not touch.

### Release workflow run after the 1.4.0 push — October 14, 2026

The daily release workflow was triggered by hand after the push (run
38583930461). Its refresh job moved eight pins to the releases upstream had
published since the last refresh (DeckCraft v0.6.1, DesignCraft v0.8.0,
EffectCraft v0.9.2, FigCraft v0.6.0, FilmCraft v0.7.2, LightCraft v0.7.1,
PhotoCraft v0.8.2, WordCraft v0.7.0), signed every archive without a bundle
keyless with cosign (39 bundles for thirteen apps), rebuilt the plugin, ran
`check` and `test`, and opened pull request #2. `scripts/check_bundles.py`
then confirmed 39 bundles on each runner, and the real
`setup --all --acknowledge-unconfined` passed on `ubuntu-latest`,
`windows-latest` and `macos-latest` with strict provenance: every archive
hash-checked against the manifest and upstream sums, cosign verification of
the bundle on all three (plus Apple notarization, team `DJ6XS33FX8`, on
macOS), staged probe (initialize, `tools/list`, read-only smoke tool), atomic
promotion and a second probe at the installed path. For FigCraft that was its
first execution anywhere: `figcraft-cli` 0.6.0 answered `inspect_document`
on all three runners (lock labels `sigstore` on Linux and Windows,
`notarized DJ6XS33FX8, sigstore` on macOS). The merge job squash-merged the
pull request into `main` as `88a97c6`; `make verify-build` and `make check`
pass on that commit. No host CLI exists on the runners, so registration is
still covered by simulated tests only, and no FigCraft binary has run on a
developer machine. The eight moved apps' smoke tools were exercised by that
run, and their cards were rechecked against the new tags on 2026-10-14 (see
the [source ledger](source-ledger.md)).

## Executed for 1.3.2 — October 12, 2026

macOS (Darwin 27, arm64) with Python **3.11.17**:

| Gate | Result |
|---|---|
| `make check` | Passed **71 check entries**: parsed 46 files (33 Python, 12 JSON, one TOML), checked 153 local Markdown links in source, translations and plugin, validated the three-platform release manifest, the signature store, the release workflow rules (including that the verify matrix checks bundle completeness before a strict `setup` without `--trust-upstream-sums`) and 14 native scenario definitions without executing any. |
| `make test` | **223 tests** passed in an isolated source copy, including the staged `setup`/upgrade flow, fault-injected promotion recovery (failure before promotion, during the file replace, while writing the lock, while clearing the marker; `completable`, `reverted`, `ambiguous` and `corrupt` reconciliation), whole-registration ownership on removal, recoverable `--replace` with restore and restore-failure, candidate-versus-active evidence identity, and the ownership-checked removal on simulated macOS, Linux and Windows with injected network, notarization, cosign and host CLIs, signature-store rotation with a fake signer, manifest rules and `doctor` scopes; zero failures, errors or skips. |
| `make build`, `make verify-build` | The generated plugin (50 files) matches its 90 allowlisted canonical inputs. |
| `make package`, `make source` | Reproducible plugin and source ZIPs with SHA-256 files. |
| `make test-sdk` with `mcp==2.3.0` | Passed 7 checks against the synthetic stdio fixture: initialize, two-page `tools/list`, wire aliases, typed structured content, `isError`, SDK context exit, and a native tool error not reported as success. |
| `claude plugin validate --strict` (Claude Code 2.1.282) | 1.3.2 marketplace and plugin manifests: no errors or warnings. |
| Claude Code install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `claude plugin details` lists one Skill (`craft`) and zero MCP servers. |
| Codex CLI 0.162.0-alpha.17.2 install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `codex debug prompt-input` lists the `storytold:craft` Skill. |
| Portable manifests | `plugin.json` and `config/portable.mcp.example.json` validate against the published Agent Plugins 1.0.0 schemas. |
| External links | Every README, app catalog and source ledger URL resolved, except the repository itself before publication. The 15 release-pinned upstream links in the app cards exist at their tags. |
| Upstream release review | All twelve cards and catalog launch flags rechecked against each app's latest release tag; see the [source ledger](source-ledger.md). Source review only, not binary execution. |

Host installs used throwaway `CLAUDE_CONFIG_DIR` and `CODEX_HOME` directories, so
no real host configuration was changed. The two install rows ran for 1.0.0;
1.0.1 through 1.2.0 change Skill text, docs and helper commands, not manifest structure. Installation from GitHub reads the same
committed marketplace files and `plugins/storytold/` runtime.

## 1.3.0 and 1.3.1 behavior changes: offline evidence only

The staged upgrade (probe before promotion), the recovery marker outside
staging and its five reconciliation states, the whole-registration ownership
checks in `setup --remove`, the read-only `--remove --dry-run`, the
restore-on-failure `--replace`, the separate candidate and active probe
evidence, the Claude registration parsing and the signature-store rotation
were verified by the offline suite above with injected network, signing and
host CLIs and with fault injection at the binary replace, lock write, marker
cleanup and host add/remove boundaries. The strict verify matrix (bundle
completeness, then `setup` without `--trust-upstream-sums`) is enforced by
`make check` and a test on the workflow text; it has not yet run on GitHub
for 1.3.1. No live `setup`, upgrade, removal, signing run or
host-configuration change was executed for 1.3.0, 1.3.1 or 1.3.2; the native
evidence below predates them and still describes the installed binaries,
which none of these releases touches. The 1.3.1 lifecycle suite failed on
the Windows CI runners only (evidence archive name collision, fixed in
1.3.2); the macOS and Linux runners passed.

## Native app evidence — the first twelve apps via `setup`

Operator-run on macOS (Darwin 27, arm64) with the one-command path:
`python3 storytold.py setup --all --acknowledge-unconfined`, resumed twice after
fixes found during the run (the probe did not forward the acknowledgement for
unconfined apps; DeckCraft's headless session has no presentation open, so its
smoke tool became `list_commands`). Final state, confirmed by `codex mcp list`,
`claude mcp list` (every server health-checked as connected), `doctor` and
`setup --list`:

| App | Release | Probe (initialize, tools/list, read-only call) | Tools | Registered |
|---|---|---|---|---|
| PhotoCraft | v0.7.0 | passed (`doc_inspect`) | 21 | codex, claude |
| VectorCraft | v0.9.0 | passed (`doc_inspect`) | 32 | codex, claude |
| FilmCraft | v0.6.0 | passed (`doc_inspect`) | 17 | codex, claude |
| LightCraft | v0.6.0 | passed (`doc_inspect`) | 17 | codex, claude |
| PdfCraft | v0.6.0 | passed (`doc_inspect`) | 17 | codex, claude |
| EffectCraft | v0.8.0 | passed (`doc_inspect`) | 27 | codex, claude |
| DesignCraft | v0.6.0 | passed (`inspect_document`) | 25 | codex, claude |
| GridCraft | v0.5.0 | passed (`inspect_workbook`) | 21 | codex, claude |
| WordCraft | v0.5.0 | passed (`inspect_document`) | 16 | codex, claude |
| DeckCraft | v0.5.0 | passed (`list_commands`) | 25 | codex, claude |
| CADCraft | v0.5.0 | passed (`inspect_drawing`) | 11 | codex, claude |
| SoundCraft | v0.5.0 | passed (`inspect_session`) | 17 | codex, claude |

Every archive matched both `config/releases.json` and the release's
`SHA256SUMS.txt`; every binary was accepted by `spctl` as *Notarized Developer
ID* with team `DJ6XS33FX8`; the probe SDK was installed into
`~/.local/state/storytold/venv` from PyPI by `setup` itself. Re-running `setup`
afterwards reports every app as already installed and already registered.

Upgrade path (1.2.0): after the manifest refresh moved VectorCraft to v0.10.0,
PdfCraft to v0.7.1 and SoundCraft to v0.6.1, `setup --app … --upgrade` replaced
the three binaries (notarization verified; no Sigstore bundle exists before the
workflow's first run), re-probed them (32, 17 and 17 tools, servers reporting
0.10.0, 0.7.1 and 0.6.1) and left both hosts' registrations unchanged;
`setup --list` reports all twelve pins equal to the manifest commits.

Fresh-user simulation: in a throwaway `CODEX_HOME`, `codex plugin marketplace
add <this checkout>` and `codex plugin add storytold@devsolux-storytold`, then
`python3 <plugin cache>/storytold.py setup --app gridcraft --host codex
--acknowledge-unconfined` registered GridCraft only in that throwaway home; the
real `~/.codex/config.toml` hash was unchanged.

Real work: during this session a host chat on this Mac exported
`outputs/our-world.png` (1920×1200 RGB) together with the editable
`our-world.pcraft` through the registered PhotoCraft server; `verify-artifact`
accepted the PNG signature and dimensions, and the image was reviewed visually.
This is an M0/M1-level result for PhotoCraft only; edit, export, root-denial,
isolation and fidelity tests (M1–M3) have not run for the other eleven apps, and
no Windows or Linux machine was used.

### Earlier manual PhotoCraft run (1.0.1)

Operator-run on macOS (Darwin 27, arm64), following [operations](operations.md):

| Step | Result |
|---|---|
| Obtain the CLI | `photocraft-cli-0.7.0-macos-universal.zip` from the v0.7.0 release matched `SHA256SUMS.txt`; `spctl` reported *Notarized Developer ID*, team `DJ6XS33FX8`, the same team as the installed `PhotoCraft.app` 0.7.0, which contains no CLI. |
| Pin | Revision `79261615956ab21334e49ca1d384390272e647da` (tag v0.7.0); binary SHA-256 `31ce1ee0…c2e42f7f2d`; `preflight` passed. |
| `probe` discovery | Official SDK 2.3.0 negotiated protocol `2025-11-25` with server `photocraft` 0.7.0 and listed 21 tools, including `doc_inspect`, `command_list`, `command_run`, `doc_render_preview`, `doc_save` and `doc_export`. |
| `probe` smoke call | `doc_inspect` with `{}` (annotated read-only) returned `isError: false` and an empty session (`document: null`). |
| `configure --host codex` | Generated `[mcp_servers.photocraft]` with absolute command, root flags and workspace `cwd`; after registration, `codex mcp get photocraft` (Codex CLI 0.162.0-alpha.17.2) lists it as enabled stdio. |

That manual run is M0-level evidence only; the `setup` run above supersedes it.

## What the offline checks exercise

The standard-library core suite uses temporary isolated source/workspace copies.
Synthetic non-executable app fixtures test binary equality and config boundaries;
SDK-shaped stubs test discovery, error, timeout and evidence logic without starting
any Craft binary. Tests cover staging, preservation, limited artifact parsing,
explicit execution approval, generated-file ownership, cleanup, reproducible
packaging, install-command identity and offline release targets. These do **not**
constitute a native handshake; `make test-sdk` covers the real SDK transport.

`make check` parses Python AST, JSON and TOML; checks local Markdown links in both
canonical source and generated plugin; checks identities, README install commands,
Makefile script references, app topology, inactive templates, source hashes, Skill
policy and acceptance definitions. CI YAML is checked for the specific
privilege/action-pinning rules used here, not full GitHub server-side validation.
Host manifest schemas remain authoritative.

## Not verified

- **Craft apps.** Twelve CLIs passed discovery and one read-only call on one
  macOS machine; only PhotoCraft has produced a real export. Native edit,
  export, root-denial, isolation and fidelity tests (M1–M3) have not run for the
  other eleven apps.
- **FigCraft.** Executed only on the three GitHub runners (run 38583930461:
  download, provenance, discovery and the `inspect_document` smoke call at
  v0.6.0); its card and scenario rest on source review. No developer machine
  has run it, no host has registered it, and every acceptance gate (M1–M3)
  is still open.
- **Linux and Windows.** Real runs exist only on GitHub-hosted runners: the
  release workflow's verify matrix (run 38278727530 on 2026-10-12 with twelve
  apps, runs 38583930461 and 38588658915 on 2026-10-14 with all thirteen, the
  latter with WordCraft's confined launch) installed, probed and
  Sigstore-verified every pinned app on `ubuntu-latest`,
  `windows-latest` and `macos-latest`. No host CLI was present there, so
  registration on Linux/Windows is covered by simulated tests only, and no
  Linux or Windows desktop machine has been used.
- **Sigstore signing.** Keyless signing ran only in that workflow. Its first
  pull request merged on 2026-10-12 and its second and third (#2 and #3, thirteen apps) on
  2026-10-14, so `config/signatures.json` on `main` holds 39 bundles, and `cosign verify-blob` (cosign v3.1.3 via Homebrew) has
  since verified three of them on this Mac during `setup --upgrade` of
  GridCraft 0.6.1, WordCraft 0.6.1 and CADCraft 0.6.2 (lock labels
  `notarized DJ6XS33FX8, sigstore`). Apps installed before cosign was present
  carry notarization-only labels until they are next upgraded.
- **CI matrix.** GitHub Actions for Linux/macOS/Windows × Python 3.11/3.13 is
  configured but was not executed here. Windows-specific branches (binary-mode
  reads, read-only publication order) are covered by simulations on macOS.
- **Out of scope.** Remote ChatGPT connectors, cloud execution, live GUI control
  and real customer documents.

App cards remain source-derived guidance, not a tested registry.

## Reproduce and extend

```bash
make check
make test
make build
make verify-build
make package
make source
make setup-probe
make test-sdk
make host-validate
```

`make setup-probe` is the only network step; it installs the pinned SDK into a
local `.venv`. `make test-sdk` launches only the synthetic stdio fixture. After
that, follow [operations](operations.md) and [acceptance](acceptance.md) against
your pinned native apps and target hosts. Keep synthetic SDK results separate
from real app evidence.

Source and plugin ZIPs use sorted entries, fixed timestamps and file modes.
Byte-identical archive tests apply to repeated builds using the same Python/zlib
toolchain; cross-zlib byte identity is not promised. File hashes attest bytes,
not business correctness, safe execution, provenance or legal authorization.
