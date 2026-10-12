# Changelog

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
