# Verification status — 1.0.0

Native application and host *acceptance* (M0–M4) remain **not run**: this
repository neither ships nor executes Craft binaries. This report separates the
checks actually executed for the release from documentary evidence.

## Executed for this release — October 12, 2026

macOS (Darwin 27, arm64) with Python **3.11.17**:

| Gate | Result |
|---|---|
| `make check` | Passed **55 check entries**: parsed 33 files (22 Python, 10 JSON, one TOML), checked 110 local Markdown links in source and plugin, and validated 14 native scenario definitions without executing any. |
| `make test` | **122 tests** passed in an isolated source copy; zero failures, errors or skips. |
| `make build`, `make verify-build` | The committed plugin (45 files) matches its 74 allowlisted canonical inputs. |
| `make package`, `make source` | Reproducible plugin and source ZIPs with SHA-256 files. |
| `make test-sdk` with `mcp==2.3.0` | Passed 7 checks against the synthetic stdio fixture: initialize, two-page `tools/list`, wire aliases, typed structured content, `isError`, SDK context exit, and a native tool error not reported as success. |
| `claude plugin validate --strict` (Claude Code 2.1.282) | Marketplace and plugin manifests: no errors or warnings. |
| Claude Code install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `claude plugin details` lists one Skill (`craft`) and zero MCP servers. |
| Codex CLI 0.162.0-alpha.17.2 install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `codex debug prompt-input` lists the `storytold:craft` Skill. |
| Portable manifests | `plugin.json` and `config/portable.mcp.example.json` validate against the published Agent Plugins 1.0.0 schemas. |
| External links | Every README, app catalog and source ledger URL resolved, except the repository itself before publication. |

Host installs used throwaway `CLAUDE_CONFIG_DIR` and `CODEX_HOME` directories, so
no real host configuration was changed. Installation from GitHub reads the same
committed marketplace files and `plugins/storytold/` runtime.

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

- **Craft apps.** None of the twelve CLI binaries was installed. No native
  handshake, edit, export, isolation or fidelity test (M0–M3) has run.
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
