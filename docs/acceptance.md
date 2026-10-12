# Local acceptance gates — not replaced by unit tests

This repository implements the integration kit. **M0–M4 are not recorded as
passed.** Shipping code/templates is different from a validated native deployment.
The fourteen scenario definitions in the source `tests/native/acceptance.json`
start as `not_run`; they are a checklist, not fabricated run results. Retain real
execution evidence privately, outside the native writable workspace.

## M0 — pins, actual binaries and protocol

For every selected app, record OS/architecture, reviewed source revision, trusted
binary SHA-256, actual help/version output and build feature flags. Test `mcp`
help, especially optional PdfCraft MCP support. Check Video/RAW/font dependencies
rather than assuming the executable alone is sufficient.

Run `inventory` and `preflight`, followed by the explicit official-SDK probe.
Keep initialization, paginated tools, typed content/error and one operator-reviewed
fixture-only inspection call. Compare tool snapshots across upgrades. Probe
receipts must match current paths, catalog, binary, platform and workspace. A
thirty-day freshness window is an operational bound, not continuous monitoring.

A successful probe is **partial M0 evidence only**. It does not prove stdout
purity under every operation, actual process exit code/EOF behavior, safe native
root enforcement, no GUI attachment, output correctness, runtime version
truthfulness or publisher authenticity. Test these separately on the installed
build. For VectorCraft, an available GUI must not be contacted by the headless
configuration. All twelve pass before claiming the full-suite M0 gate.

## M1 — each local host and independent failures

Create a new candidate host config only after matching native probe+call evidence.
Start Claude Code in the probed workspace; inspect `/mcp` and resolved server
commands. Approve project servers normally. Inspect the native working directory
and paths actually used. For Codex, review/merge only the generated TOML tables;
inspect the intended local session independently. Both hosts are separate tests.

Begin with PhotoCraft, PdfCraft and GridCraft to cover the three scope models.
An intentionally missing or failing server must not disable another working app.
Measure startup/memory/tool volume; add selective registration only as needed,
not a proxy. Test install, disable/enable, reload and removal of the guidance plugin
without hidden native registration, duplicate servers or permission grants.

## M2 — editing, durable saves and cross-app handoffs

For all twelve app scenarios: inspect a non-sensitive staged input or new native
document, make one bounded edit, preview, explicitly save/export, reopen, and
check the actual result. Verify original and staged input hashes when the copy
must remain unchanged. A useful unsupported-format result must state its limit;
it is not a completed output or a silent alternative engine.

Run both file-handoff scenarios: PhotoCraft → DesignCraft → PdfCraft; EffectCraft
→ FilmCraft, with SoundCraft only when chosen as audio owner. Save durable
intermediates and verify before the next app consumes them. No shared in-memory
IDs, universal transaction or duplicate decision-making is introduced.

## M3 — real safety, failures and fidelity before business data

Use a restricted OS account/container/VM or equivalent tested enforcement for
confidential work, particularly the eight apps without verified native roots.
An `--acknowledge-unconfined` switch only acknowledges non-sensitive testing; it
does not create or attest isolation. Include the host's other shell/file tools in
the same threat model. Test unauthorized absolute paths, traversal, symlink and
hard-link escapes, overwrite attempts, disabled scripts, locks and wrong roots.

Use fixture-only failure tests: invalid params/corrupt files, partial batch,
transport loss during a mutation, export timeout, missing fonts/media and held
LightCraft library lock. Outcomes after lost mutation responses are unknown;
inspect state and artifacts before any new command. No automatic replay.

App-specific fidelity requirements remain with the native engines and reviewer:
pixels/layers, vector artboards/fonts, video time/media, RAW settings, real PDF
redaction, composition timebases, layout overset/UTF-8 offsets, typed formula
values, DOCX tracked changes, PPTX slide renders, CAD units and audio duration/mix.
PNG/JPEG/PDF signature checks and OOXML structure checks in this kit are explicitly
weaker checks, not native reopening or visual approval. Record unresolved warnings.

## M4 — distribution validation

The reusable plugin is packaged and published through the marketplaces; its
activation and full twelve-app acceptance remain gated. Validate the generated
bundle with installed Claude and the actual supported local Codex workflow
(release-time install results are in [verification](verification.md)). Check per-user
trust, namespacing, install/reload/uninstall, and new clean machines without hidden
dependencies. The plugin must never create a thirteenth MCP server, live control
listener, remote connector or extra agent. This project is MIT-licensed; do not
infer licensing of upstream Craft apps, SDKs or assets from it.

## Evidence handling

Keep original machine logs, binary identity, tool snapshots, approvals, native
warnings, artifact hashes and reviewer decisions distinguishable. A local JSON
report is not signed authorization and can be forged by someone with write
access. The helper validates consistency; OS restrictions and authorized humans
remain the authority. Store sanitized summaries in the repository only after
reviewing for secrets, document contents and personal paths. Never commit private
locks, actual customer workspaces or native result bodies indiscriminately.
