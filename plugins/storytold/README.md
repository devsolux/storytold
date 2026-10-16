# Storytold — installed plugin

**One Craft Skill. Thirteen direct native MCP servers. No gateway or extra agent.**

This is the generated `storytold` plugin from `devsolux/storytold`, marketplace
`devsolux-storytold`. Its canonical Skill is [craft](skills/craft/SKILL.md).
Claude Code exposes it as `/storytold:craft`; Codex lists it as `storytold:craft`
in its Skill picker. No remote ChatGPT integration is implied.

Installing this package does **not** install or launch Craft apps, grant tool
permissions or prove business readiness. `config/releases.json` carries the
reviewed release pins and `config/signatures.json` their Sigstore bundles, but
they act only when you run `setup`. The two MCP launch files under `config/`
are **inactive examples**.

Start with [operations](docs/operations.md), [architecture](docs/architecture.md),
[security](SECURITY.md) and the [acceptance gates](docs/acceptance.md).
[Verification](docs/verification.md) distinguishes executed core checks from
unexecuted native and host acceptance. App cards are source-derived guidance;
the connected binary's schemas remain authoritative.

`python3 /absolute/path/to/this/plugin/storytold.py doctor` reports local
capability and, per app, the desktop app, CLI and host registration it finds,
without execution. A desktop app is not an MCP server. On macOS, Linux x86_64
and Windows x64, `python3 /absolute/path/to/this/plugin/storytold.py setup
--app <app>` (or `--all --acknowledge-unconfined`) downloads the reviewed
`<app>-cli` release, verifies it (Apple notarization on macOS; the Sigstore
bundle with cosign on Linux and Windows), pins and probes it, and registers it
with `codex`/`claude` through their own CLIs; `doctor` prints that command for
each missing app. After a plugin update, `setup --list` shows moved pins and
`setup --all --upgrade --acknowledge-unconfined` applies them (add `--replace`
when a release changed an app's launch arguments, as SoundCraft's did after
1.5.1); `setup --remove --all` undoes everything
but the workspace. Elsewhere, register the CLI your installer provides
(operations, section 0 and troubleshooting). Nothing runs unless you invoke it.

The other helper commands are documented in operations. Core helpers require
Python 3.11+ and no third-party packages; `setup` creates its own virtual
environment for the official MCP client used by the probe. Native engines and
SDK dependencies are not included in this plugin.

For maintenance, tests, the Makefile and source packaging, use the complete source
repository at https://github.com/devsolux/storytold. Never edit this generated
runtime independently; rebuild it from canonical source. Paths printed by a host
may be a cache copy rather than your source repository.

No upstream affiliation or endorsement is asserted. Released under the
[MIT License](LICENSE); see the [license notice](LICENSE-NOTICE.md) for
third-party terms.
