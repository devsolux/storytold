# Architecture decisions and responsibility boundaries

## ADR-001 — direct native MCP is authoritative

The supplied **Claude Code × Craft Apps (Local Native MCP) Project Plan** is the
implementation plan and explicitly rejects an additional gateway server, MCP
proxy and secondary agent. The older **Crafting Apps CLI and MCP Integration
Reference** proposes a remote-capable gateway. These two architecture decisions conflict.
This project follows the native plan; the reference supplies app-specific facts,
not its gateway/session/HTTP design. Both originals are preserved unchanged in
[sources](sources/README.md). Their runtime claims were not locally tested.
The plan enumerates the twelve apps that existed when it was written;
FigCraft, released upstream afterwards, is integrated the same way as a
thirteenth catalog entry with its own stdio server, not as an exception to
the architecture.

## ADR-002 — marketplace distribution, not a new runtime layer

Storytold is distributed from devsolux/storytold through Claude Code and Codex
marketplaces, which covers the plan's M4 distribution need. Native/host M0–M4
acceptance remains an operator gate. Local Codex configuration is an additive
adapter; remote ChatGPT, cloud execution and live GUI mode remain out of scope.
No interpretation of a marketplace requirement creates a gateway need.

The generated plugin carries two manifests built from `packaging/project.json`:
`.claude-plugin/plugin.json` for Claude Code and a portable root `plugin.json`
whose `extensions.com.openai` object holds the Codex/OpenAI presentation. That
extension replaces the older `.codex-plugin/plugin.json` overlay, so the overlay
is not generated. Both marketplaces point at the same `./plugins/storytold`.

The default distributed plugin deliberately contains no active `.mcp.json` or
`mcp.json`. Its source-derived examples remain `*.example.json`. Without the real
binaries, emitting an automatically activated launch config would contradict the
plan's Phase-0 warning. `configure` creates operator-requested local config only
after matching executable pins and native discovery plus a smoke-call receipt.
`setup` is the one-command form of the same chain: it installs the reviewed
release pinned in `config/releases.json`, verifies provenance, pins, runs
preflight and the probe, and registers through the host's own CLI, all on an
explicit operator command. Both create a testable candidate, not an assertion
that M0–M3 passed. The native review checklist still owns
headless/isolation/fidelity evidence.

## Ownership

| Component | Owns | Does not own |
|---|---|---|
| Host + operator | Intent, native selection, process lifecycle, approvals | Engine commands, filesystem truth |
| `craft` Skill | Workflow and on-demand guidance | Authorization, background execution, command catalogs |
| Native MCP/apps | Tool schemas, state, edits, save, export | Cross-app transactions or user approvals |
| Catalog/config helpers | Fixed headless launch candidates and host syntax | Tool semantics or running a service |
| Preflight | Local paths, workspace identity, platform and binary-hash equality | Publisher authenticity, app behavior, sandboxing |
| SDK probe | Bounded discovery and one approved conformance call | Normal host orchestration, mutation retry, production routing |
| Workspace helpers | Safe copies, no-clobber receipts, limited file checks | Rendering, editing or OS isolation |
| OS/host permissions | Actual access controls and user approval | Inferences from prompt text |
| Builder | One canonical runtime, generated manifests and archives | Installation, enablement or publishing |
| `setup` | On explicit command: download, verification, pin, probe, user-scope registration via host CLIs | Choosing versions silently, running unasked, OS isolation, editing host files itself |
| Release workflow | Daily manifest refresh, keyless signing of pinned CLIs, three-OS verify, one reviewable pull request | Changing users' machines, bypassing a red verify matrix |

Probe fingerprints bind catalog entry, binary, source pin, workspace id, paths,
arguments, platform and working directory. Configuration rejects stale, synthetic,
future-dated, incomplete, mismatched or failed probe evidence. Receipts are local
consistency data, not signatures and not permissions. A user who controls the
files can edit them; no security claim depends on their authenticity.

## Upstream/downstream continuity

Approved product or business decisions arrive as intent and constraints; the
Skill uses them to guide native artifact work rather than repeating research.
Changes to native engines or to this integration are ordinary software changes
made in their own repositories with their own tests; Storytold does not embed a
software-engineering workflow. Native files remain the cross-app interface, with
one owner per transformation and no secondary model.

## Deliberate limits

No native binaries, vendored SDK, full static registries, MCPB, gateway, agent
router, queue, database, daemon, live bridge, hidden approval allowlist, or
file-level host configuration merger (registration goes through `codex mcp
add` / `claude mcp add`). The daily workflow updates the repository's pins; a
user's machine changes only when the operator runs `setup --upgrade`. No preflight wrapper runs on
every host tool call: once configured, the host launches native binaries directly.
Re-run preflight before sessions and after changes; use OS ownership/permissions
for continuous enforcement. A hash check cannot prevent replacement after it.
