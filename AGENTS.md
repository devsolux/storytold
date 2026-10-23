# Storytold repository instructions

The native-MCP project plan in docs/sources is the architecture authority. The
older gateway reference supplies app facts only. Keep thirteen independent
native stdio servers (one per app in config/apps.json) and one instructional
craft Skill. No gateway, daemon, router, secondary agent, live GUI control, or
remote transport belongs in this project.

Work on the main branch only. There is no development, feature or release
branch: commit directly to main, and push main only when the operator asks.
The daily release workflow's bot/releases pull request is the one exception,
and it is merged into main on its own, so start with `git pull --ff-only origin
main` (or `make github-pull`) before reading or editing. Upstream references in
app cards, the catalog's documentation links and the docs point at each Craft
repository's main branch, never at a release tag or version number; release
pins belong only in config/releases.json and config/signatures.json, which the
workflow regenerates and nobody edits by hand.

A merged pin move is not finished until each moved app is rechecked at its new
tag: the CLI's `mcp` parser, MCP docs and tool definitions, the smoke tool,
packaging and release assets. Update the card (its recheck date included) and
record the findings, including "card unchanged", in docs/source-ledger.md. A
change to an app's launch arguments or confinement in config/apps.json is a
reviewed catalog change: source review plus a local `preflight` and `probe` of
the pinned binary, and because it changes the registration `setup` writes,
existing installs re-register with `setup --app <app> --upgrade --replace`.

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
Commit the regenerated plugins/storytold together with the source change that
produced it; public installs read it from main.

A release bumps packaging/project.json and updates CHANGELOG.md,
docs/verification.md and docs/source-ledger.md together, then passes make
release, make test-sdk and, with the Claude CLI installed, make host-validate.
Pushing main, the lightweight `v<version>` tag and the GitHub release happen
only when the operator asks, never as a side effect of a commit. The one
automated release is the workflow's own: a daily run that moves a pin bumps the
patch version with scripts/bump_release.py in its pull request, and its merge
job tags the squash commit `v<version>` and publishes that release from the
changelog section the run wrote. The moved cards' recheck and its record in
docs/source-ledger.md and docs/verification.md remain the operator's work.
