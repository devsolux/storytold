# Changelog

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
