# Storytold repository instructions

The native-MCP project plan in docs/sources is the architecture authority. The
older gateway reference supplies app facts only. Keep thirteen independent
native stdio servers (one per app in config/apps.json) and one instructional
craft Skill. No gateway, daemon, router, secondary agent, live GUI control, or
remote transport belongs in this project.

Work on the main branch only. There is no development, feature or release
branch: commit directly to main, and push main only when the operator asks.
The daily release workflow's bot/releases pull request is the one exception,
and it is merged into main. Upstream references in app cards, the catalog's
documentation links and the docs point at each Craft repository's main branch,
never at a release tag or version number; release pins belong only in
config/releases.json, which the workflow regenerates.

Read relevant source, configuration, and tests before editing. Canonical sources
are skills/, config/, storytold_tools/, scripts/, and docs/. plugins/storytold/
is generated; never edit it directly. Version belongs in packaging/project.json.
The build emits .claude-plugin/plugin.json and a portable root plugin.json whose
extensions.com.openai replaces any .codex-plugin overlay; do not add one back.
Keep English as the canonical language of code and docs (README.DE.md and
README.TR.md follow README.md), current source provenance, and explicit
verification limits.

The default plugin contains guidance and inactive templates. Creating real MCP
configuration requires local pinned executables and matching discovery evidence.
Do not auto-install native apps, launch real binaries during offline tests, write
host settings, grant permissions, publish, commit, or deploy implicitly. Explicit
operator commands may create a dedicated workspace or new config file, never
silently replace user data. Installation, activation, execution, and verification
are distinct. Tests and hashes are not authorization or proof of OS confinement.

Prefer the standard library for deterministic helpers. The optional short-lived
probe uses the official Python MCP client SDK, not a custom MCP implementation.
Do not copy native command registries or reimplement rendering/document engines.
Run make check, make test, make build, and make verify-build after changes. Keep
native-host acceptance separate from offline/synthetic test results. Build input
allowlists and generated-file ownership checks must preserve unexpected edits.
