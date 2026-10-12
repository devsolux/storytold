# Verification status — 1.2.1

Native application and host *acceptance* (M0–M4) remain **not run**: this
repository neither ships nor executes Craft binaries. One operator-installed
binary, PhotoCraft 0.7.0, has passed the native probe (below). This report
separates the checks actually executed for the release from documentary evidence.

## Executed for this release — October 12, 2026

macOS (Darwin 27, arm64) with Python **3.11.17**:

| Gate | Result |
|---|---|
| `make check` | Passed **68 check entries**: parsed 43 files (30 Python, 12 JSON, one TOML), checked 119 local Markdown links in source and plugin, validated the three-platform release manifest, the signature store, the release workflow rules and 14 native scenario definitions without executing any. |
| `make test` | **169 tests** passed in an isolated source copy, including the `setup` flow on simulated macOS, Linux and Windows with injected network, notarization, cosign and host CLIs, manifest and signature-store rules and `doctor` connection cases; zero failures, errors or skips. |
| `make build`, `make verify-build` | The committed plugin (50 files) matches its 85 allowlisted canonical inputs. |
| `make package`, `make source` | Reproducible plugin and source ZIPs with SHA-256 files. |
| `make test-sdk` with `mcp==2.3.0` | Passed 7 checks against the synthetic stdio fixture: initialize, two-page `tools/list`, wire aliases, typed structured content, `isError`, SDK context exit, and a native tool error not reported as success. |
| `claude plugin validate --strict` (Claude Code 2.1.282) | 1.2.1 marketplace and plugin manifests: no errors or warnings. |
| Claude Code install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `claude plugin details` lists one Skill (`craft`) and zero MCP servers. |
| Codex CLI 0.162.0-alpha.17.2 install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `codex debug prompt-input` lists the `storytold:craft` Skill. |
| Portable manifests | `plugin.json` and `config/portable.mcp.example.json` validate against the published Agent Plugins 1.0.0 schemas. |
| External links | Every README, app catalog and source ledger URL resolved, except the repository itself before publication. The 15 release-pinned upstream links in the app cards exist at their tags. |
| Upstream release review | All twelve cards and catalog launch flags rechecked against each app's latest release tag; see the [source ledger](source-ledger.md). Source review only, not binary execution. |

Host installs used throwaway `CLAUDE_CONFIG_DIR` and `CODEX_HOME` directories, so
no real host configuration was changed. The two install rows ran for 1.0.0;
1.0.1 through 1.2.0 change Skill text, docs and helper commands, not manifest structure. Installation from GitHub reads the same
committed marketplace files and `plugins/storytold/` runtime.

## Native app evidence — all twelve apps via `setup`

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

- **Craft apps.** All twelve CLIs passed discovery and one read-only call on one
  macOS machine; only PhotoCraft has produced a real export. Native edit,
  export, root-denial, isolation and fidelity tests (M1–M3) have not run for the
  other eleven apps.
- **Linux and Windows.** Real runs exist only on GitHub-hosted runners: the
  release workflow's verify matrix (run 38278727530, 2026-10-12) installed,
  probed and Sigstore-verified all twelve apps on `ubuntu-latest`,
  `windows-latest` and `macos-latest`. No host CLI was present there, so
  registration on Linux/Windows is covered by simulated tests only, and no
  Linux or Windows desktop machine has been used.
- **Sigstore signing.** Keyless signing and `cosign verify-blob` ran in that
  workflow, not on this Mac (cosign is not installed here). Until the bot's
  pull request is merged, `config/signatures.json` on `main` is empty and
  Linux/Windows users need `--trust-upstream-sums`.
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
