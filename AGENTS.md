# Storytold repository instructions

The native-MCP project plan in docs/sources is the architecture authority. The
older gateway reference supplies app facts only. Keep twelve independent native
stdio servers and one instructional craft Skill. No gateway, daemon, router,
secondary agent, live GUI control, or remote transport belongs in this project.

Read relevant source, configuration, and tests before editing. Canonical sources
are skills/, config/, storytold_tools/, scripts/, and docs/. plugins/storytold/
is generated; never edit it directly. Version belongs in packaging/project.json.
The build emits .claude-plugin/plugin.json and a portable root plugin.json whose
extensions.com.openai replaces any .codex-plugin overlay; do not add one back.
Keep English code/docs, current source provenance, and explicit verification limits.

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
