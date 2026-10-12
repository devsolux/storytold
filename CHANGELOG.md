# Changelog

## 1.2.1 — 2026-10-12

Fixes the first run of the daily release workflow, which failed in its test
step, and the main CI matrix on Linux and Windows.

- The archive member `setup` extracts is now named for the archive's platform
  (`<app>-cli.exe` only inside Windows zips) while the installed file is named
  for the running OS; the tests that simulate other platforms relied on that
  distinction and failed on Windows runners. No change for real installs.
- Tests: the CLI dry-run test accepted only macOS; doctor and setup tests
  created `<app>-cli` without `.exe`, compared paths without it and read
  recorded state from `~/.local` on Windows.
- Documented the three repository settings the daily workflow needs to run
  hands-off (Actions may open pull requests, approval policy for new-to-GitHub
  accounts only, `STORYTOLD_AUTO_MERGE`); PR creation is now non-fatal.
- The workflow's first run had already refreshed the manifest (WordCraft
  0.6.1) and signed all 36 archives keyless before the test step stopped it,
  so extraction against the real macOS, Linux and Windows archives is
  confirmed; that run's signatures were discarded with the runner and are
  regenerated on the next run.

## 1.2.0 — 2026-10-12

`setup` now covers Linux x86_64 and Windows x64, and the release pins refresh
themselves daily.

- Platform support: the manifest pins one archive per platform (macOS CLI zip,
  Linux tarball, Windows portable zip); `setup` extracts exactly the one
  `<app>-cli` from zip or tar.gz, uses per-OS paths
  (`%LOCALAPPDATA%\Storytold` on Windows, `$XDG_STATE_HOME` on Linux), the
  venv's `Scripts\python.exe`, and runs `.cmd` host shims through `cmd.exe`.
- Provenance: upstream does not code-sign Linux or Windows builds, so the new
  daily workflow signs every pinned CLI keyless with Sigstore cosign under its
  own GitHub OIDC identity and commits the bundles to `config/signatures.json`;
  on Linux and Windows `setup` requires that bundle and `cosign verify-blob`
  (`--trust-upstream-sums` to proceed on the manifest and `SHA256SUMS.txt`
  alone, recorded in the lock); macOS keeps Apple notarization and verifies the
  bundle too when cosign is present.
- `.github/workflows/releases.yml`: daily `refresh_releases.py` +
  `sign_releases.py`, plugin rebuild, checks, tests, a real `setup` on Linux,
  Windows and macOS runners, and one pull request on `bot/releases`; optional
  auto-merge via the `STORYTOLD_AUTO_MERGE` repository variable. Actions are
  commit-pinned, credentials are not persisted, only `github.token` is used.
- Manifest schema 2 with a `signers` block (Apple team, Sigstore identity and
  issuer); `make check` validates the manifest, the signature store and the
  workflow's permission rules.
- Refreshed pins: VectorCraft 0.10.0, PdfCraft 0.7.1, SoundCraft 0.6.1.
- Tests: 169 offline tests, including the setup flow on three simulated
  platforms.

## 1.1.0 — 2026-10-12

One command now takes a plugin user from "tools aren't connected" to twelve
registered native servers on macOS.

- `storytold.py setup --app <app> | --all [--acknowledge-unconfined]`: downloads
  the CLI release pinned in the new reviewed manifest `config/releases.json`,
  verifies the archive against the manifest and the release's `SHA256SUMS.txt`,
  requires Apple notarization by the ArtCraft team, installs to
  `~/.local/opt/craft/bin`, pins the hash in the private lock, runs `preflight`
  and the official-SDK probe (initialize, tools/list, one read-only call), and
  registers the server with `codex mcp add` / `claude mcp add --scope user`.
  Downloads are limited to GitHub release hosts; one registration per name;
  `--dry-run`, `--list`, `--upgrade`, `--replace`, `--skip-probe`, `--remove`.
  macOS only in this release; Windows/Linux installers already ship the CLI.
- Apps without file roots are installed but registered only with
  `--acknowledge-unconfined`, matching the existing preflight policy.
- `config/releases.json` pins all twelve latest releases (tag, commit, zip
  hash, size, smoke tool); `make refresh-releases` regenerates it for review
  and `make check` enforces its shape. Chosen paths are recorded in
  `~/.local/state/storytold/setup.json`, so `preflight`, `probe`, `configure`
  and `doctor` need no exported variables afterwards.
- `doctor` prints the exact `setup` command per missing app plus manifest and
  pinned versions; the `craft` Skill proposes that command, runs it only after
  the user agrees in chat, and never installs anything unasked.
- `storytold.py` explains the Python 3.11 requirement instead of failing with
  a syntax error on macOS system Python.
- Tests: 159 offline tests (setup flow with injected network, macOS tools and
  host CLIs; manifest rules; recorded state).

## 1.0.1 — 2026-10-12

Fixes "PhotoCraft's native tools aren't connected / `photocraft-cli` isn't on
PATH" after installing the plugin and the desktop apps.

- Root cause, now documented: each MCP server is the app's `<app>-cli`, and on
  macOS the ArtCraft Launcher and `.dmg` install only the `.app`. The CLI is the
  separate `<app>-cli-<version>-macos-universal.zip` release asset (Windows
  MSI/portable ZIP and Linux `.deb`/`.rpm` include it), and it must also be
  registered with the host. Operations section 0 lists the asset and tag commit
  for all twelve apps' latest releases, with download, checksum, notarization
  and install steps; the README setup steps start there.
- All twelve app cards were rechecked against each app's latest release tag
  (CLI parser, MCP docs, packaging) and now link docs pinned to that tag.
  Corrections include: GridCraft refuses legacy `.xls` (XLSB/ODS import values
  only); FilmCraft 0.6.0 renders offline media silently as a slate and reports
  success; DeckCraft 0.5.0 now exposes PDF export options; CADCraft
  `inspect_drawing` returns up to 200 entities unless `entities` is false;
  VectorCraft batch steps undo individually; SoundCraft 0.5.0 ignores unknown
  `mcp` flags; PdfCraft in-place saves are incremental except after redaction.
  Each card lists its release's main MCP tools.
- WordCraft keeps no root flags in the catalog: upstream `main` adds
  `--automation-read-root`/`--automation-write-root`, but the 0.5.0 CLI rejects
  them. All other catalog launch flags are accepted by the released CLIs.
- The `craft` Skill's missing-server report now names the fix (install the CLI
  asset, register it, start a new session) instead of only stating the gap.
- All twelve app cards state where the CLI comes from.
- `storytold.py doctor` adds a read-only `connections` report: per app, the
  desktop app, a CLI in `CRAFT_BIN_DIR`/PATH, Codex (`$CODEX_HOME`, `./.codex`)
  and Claude project registrations, whether the registered command exists, and
  the next step. Nothing is executed or edited.
- Codex registration guidance covers `~/.codex/config.toml` as well as a
  trusted project's `.codex/config.toml`, with backup and new-session steps.
- First native evidence: PhotoCraft 0.7.0 passed initialize, discovery and a
  read-only `doc_inspect` smoke call on macOS arm64; see `docs/verification.md`.

## 1.0.0 — 2026-10-12

First public release of devsolux/storytold, installable from GitHub as
`storytold@devsolux-storytold` in Claude Code and Codex. Released under the MIT
License.

- One `craft` Skill (`/storytold:craft`), twelve source-linked app cards, and
  single-app and file-handoff playbooks.
- Deterministic helpers: binary inventory and preflight without execution,
  private working-copy staging, limited artifact checks, an optional official
  MCP SDK 2.3.0 probe, and evidence-bound local Claude/Codex config generation.
- Guarded, reproducible plugin and source packaging with marketplace identity,
  install-command and generated-file ownership checks.
- One portable root `plugin.json` carries the OpenAI/Codex metadata under
  `extensions.com.openai`; Claude Code reads `.claude-plugin/plugin.json`. No
  `.codex-plugin` compatibility overlay is shipped.
- File hashing reads raw bytes on every OS (binary mode on Windows); corrupt
  containers, including damaged compressed OOXML members, fail as validation
  errors rather than tracebacks.

The default runtime has inactive launch templates only; it never starts Craft
apps by itself. Native app and host acceptance gates (M0–M4) remain operator
steps; see `docs/verification.md` for what this release actually ran.
