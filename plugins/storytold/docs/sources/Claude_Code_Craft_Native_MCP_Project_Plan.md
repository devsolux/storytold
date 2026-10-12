# Project Plan — Claude Code × Craft Apps (Local Native MCP)

**Decision:** Use the 12 existing Craft CLI MCP servers **directly over local stdio**, plus a **small Claude Code skill** with on-demand app reference files. Start with a project-scoped integration; package it as a Claude Code plugin only when reuse across projects/users is required. **Do not build a thirteenth MCP server, MCP-to-MCP proxy, or new AI agent.**

**Date:** 2026-10-12  
**Status:** Architecture and implementation plan; **not** an implementation  
**Target:** Claude Code running locally on the same computer as the Craft CLI binaries  
**Applications:** PhotoCraft, VectorCraft, FilmCraft, LightCraft, PdfCraft, EffectCraft, DesignCraft, GridCraft, WordCraft, DeckCraft, CADCraft, SoundCraft  
**Basis:** Review of published CLI/MCP source and documentation plus current Claude Code MCP, Skills, and permission documentation. **No local app build or executable/protocol test has been performed here.** Versions and runtime behavior must be pinned and verified in Phase 0.

---

## 1. Executive architectural decision (ADR-001)

### Recommendation

**Native MCP for capabilities; Claude Code Skills for usage guidance; plugin only for distribution.**

```text
User request and local files
         |
         v
     Claude Code
     - understands the task
     - invokes one optional `craft` skill
     - selects native MCP tools via normal MCP discovery
         |
         |  local stdio (JSON-RPC/MCP)
         v
 .mcp.json (12 independent server entries)
         |
  +------+------+----------+----------------------------+
  |             |          |                            |
 PhotoCraft   PdfCraft   GridCraft                  ... 9 others
 `...-cli mcp` `...-cli mcp` `...-cli mcp`      native `...-cli mcp`
  |             |          |                            |
  +-------------+----------+----------------------------+
                      |
            Each app's native engine
       (own document state / commands / save)
                      |
             Local input/output files
```

The skill is **instructional**, not an execution service. It does not replace MCP, invent command IDs, create a command router, or implement application semantics. Claude Code already owns model reasoning, tool discovery, approval UX, MCP process lifecycle, and the local stdio transport.

### Decision matrix

| Option | Assessment | Decision |
|---|---|---|
| **Only CLI through shell/Bash** | Useful for isolated one-shot jobs, but loses structured MCP schemas and persistent editing sessions. | Not the main integration |
| **Only native MCP** | Lowest implementation cost; structured tools and retained app sessions. Needs workflow guidance and explicit file safety. | Required foundation |
| **Native MCP + one Claude Skill** | Structured execution with task-specific operating procedures and compact on-demand references. | **Recommended v1** |
| **Claude Code plugin with bundled MCP config + skills** | A distribution format, not another execution/reasoning layer. Useful across projects and teammates. | **Optional v2 packaging** |
| **New unified MCP server/gateway/proxy** | Duplicates Claude Code's native process/tool orchestration and adds state, protocol and authorization complexity. | **Reject unless a measured capability gap appears** |
| **New subagents, LLM routers, hosted services or HTTP API** | No unique responsibility for local stdio use. | **Out of scope** |

### Why this differs from a Claude+ChatGPT architecture

The earlier cross-client gateway concept was justified primarily by remote transport, unified client authorization, and cross-client session ownership. None are needed for **one local Claude Code client**. Direct native MCP is simpler, exposes upstream schemas without translation, and lets Claude Code launch/stop the child processes itself.

---

## 2. Goals, non-goals and constraints

### Goals

1. Claude Code can initialize and use **all 12 independently registered, headless MCP servers** via stdio.
2. A user can ask natural-language tasks (create, inspect, edit, export, validate), and Claude can select the right existing app without copying a second command catalog into the project.
3. Safe **original → working copy → exported result → verification** behavior is the default.
4. An app/server error does not corrupt unrelated files, cause an invisible fallback to another backend, or silently trigger repeated edits.
5. Tool discoveries, command schemas, save/export capability, and reproducible acceptance tests are checked against **pinned actual binaries**.
6. Keep integration configuration portable across trusted developer machines without embedding machine-specific paths or secrets in Git.

### Non-goals

- ChatGPT, HTTP/SSE/WebSocket, tunnels, cloud execution, shared remote sessions, authentication gateways.
- Driving live desktop windows using `--connect`, `--bridge`, control ports, screenshots of live UI, or simulated mouse input. **Headless-only v1.**
- Rebuilding document engines, format converters, rendering engines, command registries, or an extra MCP server.
- A generic workflow orchestration engine, database, event bus, background worker service, or additional LLM/agent.
- Automatically editing originals, deploying software, publishing files, or installing/updating upstream apps without user authorization.

### Hard invariants

- Native app engine owns document semantics and command validity; **no duplicate command implementation** in this integration.
- Native MCP `tools/list` and runtime behavior are the operative API, not hand-maintained tool schemas in a Skill.
- Claude chooses tasks and tool calls; **filesystem scope, user approvals and OS permissions are enforced outside the Skill**.
- A tool success response does not prove durable export: **inspect the output file and, where applicable, reopen/parse/render it**.
- Never auto-retry a mutating command after a transport failure/timeout until state has been inspected; it may already have executed.
- No persistent state assumed across independent Claude Code sessions unless an app explicitly saves it to disk.

---

## 3. Responsibility boundaries

| Layer / component | Owns | Must *not* own |
|---|---|---|
| **User + Claude Code** | Task intent, action selection, interactive approvals, MCP tool discovery/calls | Reimplementing engine validations or inventing command IDs |
| **`.mcp.json` / `claude mcp add`** | Launch command, stdio arguments, environment, server identity, project/user scope | Application semantics, authorization policy by itself |
| **Claude Skill (`craft`)** | App selection guidance, file-state workflow, output verification, domain-specific pitfalls | Hard security enforcement, tool execution proxy, full static command catalogs |
| **Native `*-cli mcp`** | MCP protocol, tool definitions, long-running process-local app session, native file I/O, native errors | Cross-app transactions or Claude Code permission policy |
| **App engine** | Document truth, edit/undo, save/export/render, format limitations | Choosing user intent or client permissions |
| **OS/filesystem + Claude permissions** | Actual file/process rights, approval gates, optional isolated execution | Inferring safety from prose or model decisions |
| **Small deterministic preflight/test scripts** | Check installations, hashes, config variables, protocol and sample output | New MCP transport or AI task routing |

**Explicitly missing responsibility:** deployment configuration, curated workflow knowledge, reproducible conformance checks, and safe file staging. Those are small repository/configuration tasks, **not a reason to write a new server**.

---

## 4. The 12-app integration matrix

Launch all as **headless**, independent stdio processes. The table is based on source/docs; exact supported flags must be reconfirmed against each pinned build.

| App | Native server | Recommended v1 mode/flags | Critical integration note |
|---|---|---|---|
| [PhotoCraft](https://github.com/storytold/photocraft) | `photocraft-cli mcp` | `--automation-read-root ... --automation-write-root ...` | File access denies ungranted directions; keep inputs/outputs within roots. |
| [VectorCraft](https://github.com/storytold/vectorcraft) | `vectorcraft-cli mcp` | `--headless` plus read/write roots | **Force headless**: without explicit mode/roots, it can attach to the desktop at `127.0.0.1:7979`. |
| [FilmCraft](https://github.com/storytold/filmcraft) | `filmcraft-cli mcp` | Bare `mcp` (empty headless project) | No documented MCP file-root flags; external isolation is necessary for strong file confinement. |
| [LightCraft](https://github.com/storytold/lightcraft) | `lightcraft-cli mcp` | `--compact`; optional explicit `--library` | A persistent library is locked to one process; don't open it simultaneously in GUI/headless. Avoid move-import without explicit consent. |
| [PdfCraft](https://github.com/storytold/pdfcraft) | `pdfcraft-cli mcp` | `--root ... --compact` | MCP support depends on the build feature; document edits require explicit save. Root restricts the tree, not a separate read-vs-write directory. |
| [EffectCraft](https://github.com/storytold/effectcraft) | `effectcraft-cli mcp` | `--automation-read-root ... --automation-write-root ...` | Restricted mode disables scripts/UI controls; this is desirable in v1. Long render jobs need status/cancellation tests. |
| [DesignCraft](https://github.com/storytold/designcraft) | `designcraft-cli mcp` | Bare `mcp` | Validate UTF-8 **byte** positions for stories and exports; no root flag verified in MCP docs. |
| [GridCraft](https://github.com/storytold/gridcraft) | `gridcraft-cli mcp` | Bare `mcp` | Preserve typed formula/error values; verify XLSX round-trip. No root flag verified. |
| [WordCraft](https://github.com/storytold/wordcraft) | `wordcraft-cli mcp` | Bare `mcp`; optionally `--author` | Preserve track-change semantics, fonts, and DOCX/PDF quality. No root flag verified. |
| [DeckCraft](https://github.com/storytold/deckcraft) | `deckcraft-cli mcp` | Bare `mcp` | Verify actual PPTX/PDF export schemas on pinned version; don't infer fidelity from tool descriptions. |
| [CADCraft](https://github.com/storytold/cadcraft) | `cadcraft-cli mcp` | Bare `mcp` | Model-space units, geometry/viewport framing and entity pagination must be respected. |
| [SoundCraft](https://github.com/storytold/soundcraft) | `soundcraft-cli mcp` | Bare `mcp` | Headless offline engine is not a live audio-device session; check missing media and mix/bounce outputs. |

**No live mode in v1.** Do not register each app twice (`-headless` and `-live`) or start control TCP listeners. This avoids mode ambiguity, shared port collisions, unnecessary attack surface, and unexpectedly editing a user's open GUI session.

---

## 5. Installation and configuration strategy

### 5.1 Target operating arrangement

- Keep **12 trusted, version-pinned executable binaries** in one local binary directory (e.g. `$HOME/.local/opt/craft/bin/`). They may originate from releases or separate Cargo builds. This directory is a **deployment convention**, not another daemon or tool.
- Keep the original inputs outside the agent's writable area. Stage copies under an absolute `CRAFT_WORK_ROOT` with an `inputs/` area and an `outputs/` area.
- Set absolute environment variables in the shell that starts Claude Code:
  - `CRAFT_BIN_DIR`: directory containing all 12 `*-cli` executables (with `.exe` on Windows).
  - `CRAFT_WORK_ROOT`: dedicated trusted temporary/project working directory.
  - `CRAFT_OUTPUT_ROOT`: absolute `CRAFT_WORK_ROOT/outputs` directory, **created before launching**.
- For local development, use `.mcp.json` at the project root; keep machine-specific env values outside the repo. For one person's integration across many projects, use Claude Code **user-scoped MCP registration** instead. Do not register duplicate names at multiple scopes.
- In interactive Claude Code sessions, review/approve the project's MCP servers when prompted. Do not commit auto-approval overrides or secrets.

**Note:** An unset `${VAR}` may remain unexpanded in Claude Code's MCP config; the startup preflight must reject missing variables rather than guessing a root. `CLAUDE_PROJECT_DIR` exists in spawned server environments, but is not a substitute for explicit, validated security roots in `.mcp.json` arguments.

### 5.2 Proposed project-scoped `.mcp.json` (configuration *example*, not deployed)

For clarity and least privilege, PhotoCraft/VectorCraft/EffectCraft get read and write roots; PdfCraft gets a single confined root. Other apps run in headless mode and require external filesystem controls where necessary.

```json
{
  "mcpServers": {
    "photocraft": {
      "command": "${CRAFT_BIN_DIR}/photocraft-cli",
      "args": ["mcp", "--automation-read-root", "${CRAFT_WORK_ROOT}", "--automation-write-root", "${CRAFT_OUTPUT_ROOT}"]
    },
    "vectorcraft": {
      "command": "${CRAFT_BIN_DIR}/vectorcraft-cli",
      "args": ["mcp", "--headless", "--automation-read-root", "${CRAFT_WORK_ROOT}", "--automation-write-root", "${CRAFT_OUTPUT_ROOT}"]
    },
    "filmcraft": {
      "command": "${CRAFT_BIN_DIR}/filmcraft-cli",
      "args": ["mcp"]
    },
    "lightcraft": {
      "command": "${CRAFT_BIN_DIR}/lightcraft-cli",
      "args": ["mcp", "--compact"]
    },
    "pdfcraft": {
      "command": "${CRAFT_BIN_DIR}/pdfcraft-cli",
      "args": ["mcp", "--root", "${CRAFT_WORK_ROOT}", "--compact"]
    },
    "effectcraft": {
      "command": "${CRAFT_BIN_DIR}/effectcraft-cli",
      "args": ["mcp", "--automation-read-root", "${CRAFT_WORK_ROOT}", "--automation-write-root", "${CRAFT_OUTPUT_ROOT}"]
    },
    "designcraft": {
      "command": "${CRAFT_BIN_DIR}/designcraft-cli",
      "args": ["mcp"]
    },
    "gridcraft": {
      "command": "${CRAFT_BIN_DIR}/gridcraft-cli",
      "args": ["mcp"]
    },
    "wordcraft": {
      "command": "${CRAFT_BIN_DIR}/wordcraft-cli",
      "args": ["mcp"]
    },
    "deckcraft": {
      "command": "${CRAFT_BIN_DIR}/deckcraft-cli",
      "args": ["mcp"]
    },
    "cadcraft": {
      "command": "${CRAFT_BIN_DIR}/cadcraft-cli",
      "args": ["mcp"]
    },
    "soundcraft": {
      "command": "${CRAFT_BIN_DIR}/soundcraft-cli",
      "args": ["mcp"]
    }
  }
}
```

This JSON demonstrates the desired topology. **Do not paste it into a production project until OS/platform binary paths, roots, builds and every application's runtime flags pass Phase 0 tests.** On Windows use the actual `.exe` names or platform-specific configuration generation; don't assume the Unix example works unchanged. The config grants native scopes only to the four apps that expose verified per-MCP root arguments in the reviewed material; for all others it is *not* a confinement layer.

### 5.3 Useful Claude Code commands

```bash
# Once the local binaries and project config exist:
claude mcp list                    # configured/health status
claude mcp get photocraft         # resolved server info
claude mcp get vectorcraft
claude                            # open interactive session; approve project MCP entries
# Inside Claude Code:
# /mcp                           # connection and tool status
# /craft                         # invoke the proposed skill explicitly
```

**Alternative user-scope registration** (for one independently installed binary):

```bash
claude mcp add --scope user --transport stdio photocraft -- \
  /absolute/path/photocraft-cli mcp \
  --automation-read-root /absolute/work \
  --automation-write-root /absolute/work/outputs
```

Use **one registration mechanism per server name**: do not configure the same binary in both project scope and user scope. Prefer an absolute executable path over an untrusted or mutable `PATH` lookup.

---

## 6. Skill design: one coordinator, on-demand references

### 6.1 Proposed skill

Name: **`craft`**  
Location: `.claude/skills/craft/SKILL.md`  
Purpose: Tell Claude **which existing server to use and how to verify work**, not how to emulate app engines.

Example frontmatter for the *future implementation*:

```yaml
---
name: craft
description: Use the installed Craft app MCP tools for local image, vector, video, photo, PDF, layout, spreadsheet, document, presentation, CAD, audio or motion-graphics tasks. Select the appropriate app, inspect before editing, save to staged outputs and verify results.
---
```

**Avoid `allowed-tools` auto-grants** in the initial skill. Skill instructions are not permissions; a broad tool allowlist can silently grant editing operations. Let Claude Code's permissions UI and explicit per-tool rules handle approvals.

### 6.2 Core skill procedure

1. Identify input type, desired output, format and the application that actually owns the needed semantics.
2. Confirm the corresponding MCP server is connected. If not, report the specific binary/configuration problem; never silently substitute a live UI backend or shell script.
3. Read **only** the app-specific reference needed for this task. Discover live tool IDs, params and formats from MCP tools (`tools/list`, `list_commands`, `commands`, `describe`, `tool_search`, as provided by that specific app).
4. Inspect the input before mutation (document/workbook/drawing/session structure and supported export format).
5. Use a working copy or a new headless document; never assume original files are writable or intended to be overwritten.
6. Make a bounded sequence of native tool calls. Use a native batch/undo transaction only when its documented semantics fit.
7. Render/inspect after important edits, then save/export into `CRAFT_OUTPUT_ROOT` or another expressly approved output location.
8. Verify file existence, nonzero size, expected format, successful reopen/parse, expected page/slide/duration/dimensions/formulas/media, and obvious warnings. Preview visually for graphical output.
9. Report output paths, changes, limitations, and any incomplete verification. Never claim success after an `isError`, missing output, or unresolved export warning.

### 6.3 On-demand reference files

- **12 app cards** in `references/apps/` (one per app), each containing: *When to choose it; correct native MCP server name; discovery/inspect/edit/save/render tools; input/output formats; irreversible actions; known limitations; references to upstream docs*.
- **Two shared playbooks** in `references/workflows/`: `single-app.md` and `cross-app-handoff.md`.
- **One short safety page**: `references/safety.md` for staged files, approvals, retry rules and durable output checks.
- Keep the skill's entry `SKILL.md` concise; detailed material is read only when applicable. Do not hard-code hundreds of upstream command schemas into any skill file.

### 6.4 Cross-app work (no second workflow engine)

Treat each app's exported **file** as the only cross-app contract, never another app's in-memory document ID.

Example: photo edit → page layout → PDF:

```text
PhotoCraft MCP: inspect/edit/export to outputs/photo.png
     -> verify PNG on disk
DesignCraft MCP: import outputs/photo.png + build layout
     -> verify document structure and exported outputs/page.pdf
PdfCraft MCP: inspect/audit/check outputs/page.pdf
     -> verify final file and report
```

Ownership: PhotoCraft owns pixels, DesignCraft owns layout, PdfCraft owns PDF validation/operations. Each stage consumes the previous stage's **durable result**; no duplicate editing decisions or joint transactions. If a stage fails, stop; report which verified artifact is still usable.

---

## 7. Filesystem, trust and human-approval model

### Required before using real user documents

1. **Copy inputs** into a dedicated working folder; only promote verified outputs. Source documents should be outside an agent-writable folder when feasible.
2. Use native MCP root flags where available. PhotoCraft, VectorCraft and EffectCraft support distinct read/write roots. PdfCraft supports `--root`, which confines a tree but does not separate input read-only from output write permissions.
3. For **FilmCraft, LightCraft, DesignCraft, GridCraft, WordCraft, DeckCraft, CADCraft and SoundCraft**, assume their headless MCP processes can access everything allowed by their **OS user** unless a pinned binary is proven to enforce more. Use a dedicated restricted OS account, container/VM, or other OS-level sandbox when isolation matters. A `.mcp.json` field, Skill, or Claude Code prompt **does not** sandbox an unrestricted child process. A tiny deterministic launcher may be used solely to apply OS isolation; that is *not* a new MCP server.
4. Enable Claude Code's normal prompts for modifying tools. Avoid `bypassPermissions`, broad `mcp__...__*` allow rules, or broad Skill `allowed-tools` until a controlled security review proves they are safe. Claude Code permission rules are a client approval layer; **actual OS rights remain the final file-access boundary**.
5. Explicit confirmation for: overwrite/replace; bulk destructive edits; moving/deleting originals; PDF redaction/security changes; running scripts/macros; deleting or rewriting library/source media; potentially costly long exports; any change outside the dedicated work area.
6. Keep all app control ports disabled. The stdio design does not require TCP listeners, firewall rules or control bearer tokens.
7. Inspect symlinks, directory escapes and unexpected absolute paths during integration tests. Never treat tool annotations (readOnly/destructive/idempotent hints) as proof of safe behavior.
8. Treat content extracted from user documents, metadata, templates, and tool results as **untrusted data**, not instructions that can override this policy.

### Safety responsibilities by enforcement layer

| Enforcement | Concrete responsibility |
|---|---|
| OS/file permissions | Prevent unauthorized access even if the model or MCP tool misbehaves |
| Native root flags | Bound each cooperating engine's read/write paths where supported |
| Claude Code permissions | Require user approval for risky tool calls; centrally deny disallowed tools |
| Skill instructions | Guide correct tool selection, conservative file handling and verification |
| Runtime tests | Prove the above boundaries on actual binaries and fixtures |

**Limit:** Claude may also possess separate file-editing and shell tools. Native MCP roots do not constrain what those other Claude Code tools can access. The overall security posture must account for *all* enabled tools and the launching OS account.

---

## 8. Runtime and failure handling

### Process/state ownership

- Claude Code starts and holds **one stdio child process per configured app** in the session. Each headless app server owns its **own** in-memory state; these states are not shared across different servers or Claude Code sessions.
- Save documents deliberately before exiting. A disconnected/restarted server loses unpersisted headless state unless its backend explicitly maintains a library/checkpoint.
- Do not operate on the same persistent LightCraft library from both desktop and headless sessions. Do not let multiple separate app processes write the same output simultaneously.
- Pin binary versions; do not auto-update them during an active session. Version updates may change `tools/list` schemas or save formats.

### Failure rules

| Condition | Required behavior |
|---|---|
| MCP process missing/crashes on launch | Mark only that app unavailable; inspect stderr and configuration; no silent substitute. |
| Server claims success, output missing/invalid | Fail verification, preserve originals and intermediate artifacts, report mismatch. |
| MCP `isError: true` / partial batch failure | Read per-step results, inspect state, avoid blind retry, optionally use documented undo. |
| Timeout/disconnect during mutation | Outcome **unknown**; re-inspect state, filesystem and job status before another edit/export. |
| Document/library lock | Stop and ask for a deliberate session choice; never remove lock files blindly. |
| Rendering/export long-running | Use native progress/job status/cancellation where supported; verify completed file. No home-grown job queue. |
| Input parse/format unsupported | Stop with actual engine error; offer explicit safe conversion only if documented and approved. |
| Format fidelity warning | Surface the warning, compare reopened output; do not claim equivalence. |
| Unconfined app needs sensitive file | Run under an OS-isolated account/container or mark that task blocked. |

**Stdio contract:** stdout must contain MCP protocol messages only; diagnostics belong on stderr. Validate initialization negotiation and JSON-RPC tool errors on real binaries; don't assume the protocol version or every tool schema is identical across applications.

---

## 9. Capability discovery and context efficiency

- Keep all 12 servers **independently discoverable**; allow Claude Code's native MCP tool search to defer schemas when supported by the installed client/model.
- Enable upstream `--compact` only where source/runtime tests confirm it preserves needed discovery/dispatch (`LightCraft`, `PdfCraft` in the current source review). Do not invent `--compact` for other apps.
- Do not maintain a frozen copy of every generated command (`cmd_*`) or tool schema in the Skill. Gather `tools/list` at test time and, for diagnostics, persist versioned metadata snapshots.
- Limit search/inspect result sizes (filters, page/range/entity pagination, thumbnail sizes). Prefer a small structural inspection over dumping a whole workbook, timeline, page or CAD database.
- If 12 running processes create an unacceptable startup/resource cost, measure it and then adopt **project profiles or selective registration** (e.g. document/design/media) rather than implementing a new lazy-loading proxy.
- One-shot CLI commands are an **explicit exception** for unique stateless features not exposed through native MCP (e.g., offline validation utilities). Use known CLI commands with shell approval and OS restrictions; never turn the Skill into an unrestricted shell-command generator.

---

## 10. Proposed repository deliverables (to be implemented later)

```text
claude-craft-local/
├── README.md                        # quick start and platform setup
├── .mcp.json                        # 12 native stdio server definitions
├── .claude/
│   ├── CLAUDE.md                    # tiny integration invariants; no duplicate manual
│   └── skills/
│       └── craft/
│           ├── SKILL.md             # one task-selection/verification skill
│           └── references/
│               ├── safety.md
│               ├── apps/           # 12 focused upstream-linked app cards
│               │   ├── photocraft.md
│               │   ├── vectorcraft.md
│               │   ├── filmcraft.md
│               │   ├── lightcraft.md
│               │   ├── pdfcraft.md
│               │   ├── effectcraft.md
│               │   ├── designcraft.md
│               │   ├── gridcraft.md
│               │   ├── wordcraft.md
│               │   ├── deckcraft.md
│               │   ├── cadcraft.md
│               │   └── soundcraft.md
│               └── workflows/
│                   ├── single-app.md
│                   └── cross-app-handoff.md
├── config/
│   ├── env.example                  # variables, never actual secrets/paths
│   └── installations.lock.example  # app, release/commit, binary SHA-256
├── scripts/
│   ├── preflight.*                  # deterministic executable/root checks
│   └── probe-mcp.*                  # deterministic initialize/tools-list probe
├── tests/
│   ├── fixtures/                    # tiny non-sensitive inputs
│   ├── contracts/                   # collected real binary/protocol snapshots
│   ├── integration/                 # tests against installed native apps
│   └── e2e/                         # local Claude Code task acceptance
└── docs/
    ├── architecture.md              # this decision and authority boundaries
    ├── security.md                  # app-specific file restrictions
    └── operations.md                # install, diagnose, pin, rollback
```

This is a **target structure**, not files created by this plan. Skip any directory that does not carry actual content; avoid generic scaffolding. The scripts should be plain deterministic programs, not a long-running service and not an MCP proxy.

---

## 11. Milestones, dependencies and acceptance gates

Do not schedule a fixed duration until the target OS, upstream build availability and binary versions are known. Execute these milestones in dependency order. A milestone is finished only when its **gate** passes.

### M0 — Pin and prove the native servers (required)

**Tasks**

- Select target OS/architecture and a supported local Claude Code version.
- Install/build each native CLI from a pinned release/tag or commit and record executable SHA-256, version and path. Verify published release checksums where available.
- Verify each `--help` / `mcp` flag and headless behavior against *its installed binary*.
- Verify MCP `initialize`, `tools/list`, representative read-only tools, `isError` behavior and clean process exit for each app.
- Validate files and filesystem roots; test that **VectorCraft never connects to an available GUI by accident**.
- Identify and record every app lacking enforceable native file-root flags.

**Gate M0:** 12/12 binaries discoverable and checksummed; 12/12 headless MCP handshakes succeed; mode/flag matrix is updated with any real divergences. **No unsupported assumptions remain in the launch config.**

### M1 — Direct Claude Code integration (required)

**Tasks**

- Create minimal project `.mcp.json` and environment example with actual validated arguments.
- Start with three deliberately different pilots: **PhotoCraft** (root-scoped), **PdfCraft** (compact single-root), **GridCraft** (no verified native root flag). Exercise isolated workspace access.
- Validate `claude mcp list`, `claude mcp get`, `/mcp`; accept the project entries explicitly.
- Add remaining apps in small groups, preserving independent failures and no duplicate registrations.
- Record startup/memory footprint and tool-discovery counts; make process/profile decisions only from measured data.

**Gate M1:** Claude Code connects to all 12; for each, a real read/inspect call works; one intentionally failing app does not prevent another from working; no live-control port is used.

### M2 — One skill and safe editing workflows (required)

**Tasks**

- Write `craft/SKILL.md` and 12 concise upstream-linked app reference cards; keep app command schemas discovered at runtime.
- Implement instruction-level workflow: inspect → working copy → native edit → preview → save/export → independent verify → report.
- Define explicit approvals for destructive operations and known cases (LightCraft move import, PdfCraft destructive/redaction, SoundCraft replace, batch overwrites, scripts/macros).
- Test both explicit `/craft` invocation and natural-language skill triggering across the 12 domains.
- Add an example cross-app pipeline that hands off **files**, not in-memory session identifiers.

**Gate M2:** 12/12 small fixture-based single-app workflows produce parseable, verified outputs or a clear, justified unsupported result. Two representative cross-app workflows pass without a second router, AI agent or workflow engine.

### M3 — Security, failure and fidelity gates (required before real data)

**Tasks**

- Apply OS-level isolation for any unconfined app when the task requires confidentiality or path restriction; test real boundary enforcement.
- Exercise symlink escape, path traversal, overwrite denial, missing root, unexpected absolute path, unsafe script call, and file-lock scenarios.
- Run kill/restart and interrupted-edit/export tests; require inspect-before-retry and preserved originals.
- Validate formats by app: PSD/layers, SVG/vector structure, video duration/offline-media, RAW/library, PDF text/redactions, motion frame, layout overset, workbook formula results, DOCX re-open, PPTX slides, CAD units and audio mix.
- Compare saved/exported output against small known fixtures and surface fidelity/unsupported-format warnings.

**Gate M3:** Boundary tests pass on a restricted OS environment; no unauthorized writes in controlled escape tests; no unverified success reports; failures preserve source inputs and are recoverable without blind repeated mutations.

### M4 — Reusable Claude Code plugin (optional; only if distribution is required)

**Trigger:** The same integration must be installed across several unrelated projects, or distributed to teammates/users.

**Tasks**

- Package the already-working `.mcp.json` and skill inside a Claude Code plugin; **do not rewrite any server**.
- Add plugin metadata, installation/preflight documentation, platform binary resolution, and configuration templates.
- Respect Claude Code's plugin MCP tool naming/permissions differences; reevaluate `mcp__plugin_<plugin>_<server>__...` rules rather than copying project-level tool patterns.
- Verify installation, disable/enable, reload and per-user trust approvals; do not bundle confidential files or machine-specific paths.

**Gate M4:** The same 12 native server processes and existing Skill work from the plugin without any proxy, without duplicating tool registrations, and without default auto-approval of write tools.

### M5 — Maintenance (ongoing once deployed)

- Track pinned upstream tags/commits and changed MCP capabilities (schema snapshots).
- Upgrade one native binary at a time after contract + small end-to-end checks; retain a known-good binary for rollback.
- Keep app guides short and accurate; remove obsolete tips as engines evolve.
- Add scripts or automation only in response to a demonstrated test/operation gap.

---

## 12. Test plan and measurable Definition of Done

### Deterministic checks

| Test family | Minimum evidence |
|---|---|
| Install + config | 12 binary paths exist, versions/hashes logged, required env/root dirs validated. |
| Protocol | Each native stdio process accepts initialize, tools/list, representative tools/call and shutdown/EOF without stdout pollution. |
| Functional | For every app: open/new or inspect, one safe edit where supported, render or export, reopen or independently validate. |
| Discovery | Tool/schema snapshots are associated with the correct pinned binary. Changes are visible in diffs; no invented tool names. |
| Safety | Input originals unchanged, unauthorized root writes rejected or blocked by OS, risky operations demand consent. |
| Failure | Invalid params, corrupt input, disconnected server, timeout, locked library, missing fonts/media, partial save/export. |
| Cross-app | Durable intermediate files; correct stage ownership; output passes next app's reopen/inspect test. |
| Client | `/mcp` healthy, `/craft` available, no unintended live GUI attach, no project-approval bypass. |

### Final acceptance scenarios

1. **Photo:** Open a copied image, apply a reversible change, preview, export and verify dimensions/format.
2. **Vector:** Create/edit a small illustration, save native project and export SVG, verify **headless** backend.
3. **Film:** Create/load sample sequence, inspect clips/timeline, render a frame or short output, verify offline-media warnings.
4. **Light:** Develop a copied photo, render and export; test library lock and avoid moving the original.
5. **PDF:** Open a small PDF, inspect, make an allowed edit in memory, save a new file, reopen and run PDF audit when relevant.
6. **Effect:** Create a tiny composition, add keyframe, render frame; verify restricted mode behavior.
7. **Design:** Insert text/image into a page layout, inspect story structure, export and reopen PDF.
8. **Grid:** Change a formula/cell, recalculate, save XLSX, reopen and compare typed values/formulas.
9. **Word:** Modify text/formatting with a named author where appropriate, save DOCX, reopen and render a page.
10. **Deck:** Create/edit a slide, save native deck and export PPTX/PDF, verify slide count/content.
11. **CAD:** Draw known geometry, inspect entities/units, export DXF/SVG or PNG, compare geometry.
12. **Sound:** Import a tiny audio asset, adjust session settings, bounce and verify duration/rate/channels and missing-media handling.
13. **Cross-app A:** PhotoCraft → DesignCraft → PdfCraft: verified PNG handoff then verified PDF.
14. **Cross-app B:** EffectCraft → FilmCraft, optionally SoundCraft: verified timing, frame rate, media references and final export.

**Done means:** All applicable M0–M3 gates pass on the target local OS; test logs identify exact upstream versions; app docs and config agree; no custom MCP gateway exists; v1 execution remains headless stdio; user files are protected by real permissions; generated artifacts are independently verified. M4 is not necessary for a single-project setup.

---

## 13. Known trade-offs, risks and deliberate deferrals

| Risk/trade-off | Handling now | Add something later only when... |
|---|---|---|
| 12 server processes could use substantial memory | Measure process cost, prefer selective registration/profiles if needed | Actual startup/resource data makes direct launch impractical |
| Several apps have no native root flags | Restrict OS permissions/sandbox; stage copies; keep approvals | Upstream adds better native restrictions or an isolated launcher is needed |
| Project config works only in its project | Use user-scope setup for personal global use | Reuse/distribution across projects justifies plugin packaging |
| Skills can hallucinate command names | Native discovery, run-time schemas, app cards as guidance | Upstream tool discovery demonstrably lacks a needed capability |
| Cross-app file formats are not perfectly equivalent | Handoff via verified files and known format boundaries | A specific deterministic conversion/validator is missing |
| Large MCP tool listings | Claude Code tool search and native compact flags where available | Measured tool/context limit justifies app-profile management |
| Session restart loses unsaved state | Save/verify; report process loss and recover from disk | User needs explicit resumable multi-session jobs (not v1) |
| Parallel edits can conflict | Single writer per artifact/library, no implicit parallelism | Real workloads prove a need for a lock-aware workflow scheduler |

### Changes that are deliberately **not** required

- No Rust/TypeScript/Python MCP server in this project.
- No MCP aggregation/discovery proxy; Claude Code already provides tool discovery.
- No app API adapters for 12 different tools unless an actual missing capability is demonstrated.
- No agent graph, multi-agent dispatcher, vector database, or AI semantic router.
- No control-port manager, authentication service, web interface, or ChatGPT connector.
- No new task queue for long renders when upstream job/progress APIs work.

---

## 14. Open validation items (not reasons to redesign)

These must be resolved on the actual target machine before implementation is considered complete:

1. Target OS/architecture, Claude Code version, app release/build versions, CLI availability (including optional PdfCraft MCP feature).
2. Exact, versioned MCP tool schemas and flags for all 12 binaries; upstream `main` changes frequently.
3. Whether strong filesystem isolation is mandatory for all workloads or only those touching confidential/original content; test the chosen OS sandbox rather than relying on a skill.
4. Whether any application must use a persistent library/project across Claude Code sessions (notably LightCraft), and who holds its lock.
5. Measured startup/memory cost of 12 servers, and whether profiles are necessary.
6. Format-fidelity acceptance thresholds for each type of deliverable (PDF/DOCX/PPTX/audio/video/PSD/CAD).

None of these require an additional MCP gateway for v1.

---

## 15. Primary references

### Claude Code (official)

- [Connect Claude Code to tools via MCP — stdio, project scope, environment expansion, tools and plugin servers](https://code.claude.com/docs/en/mcp)
- [Extend Claude with Skills — SKILL.md, skill locations, references and invocation](https://code.claude.com/docs/en/skills)
- [Configure permissions — MCP tool approvals, deny/ask/allow](https://code.claude.com/docs/en/permissions)
- [Plugins overview](https://code.claude.com/docs/en/plugins)

### Upstream Craft source/docs

- [PhotoCraft native MCP and filesystem roots](https://github.com/storytold/photocraft/blob/main/docs/development.md)
- [VectorCraft CLI source — `mcp --headless`, default live attach and root flags](https://github.com/storytold/vectorcraft/blob/main/apps/vectorcraft-cli/src/main.rs)
- [FilmCraft agent guide — stdio modes and lack of native root flags](https://github.com/storytold/filmcraft/blob/main/docs/agents.md)
- [LightCraft MCP — `--compact`, headless library and locks](https://github.com/storytold/lightcraft/blob/main/docs/mcp.md)
- [PdfCraft README — `mcp --root --compact` and save behavior](https://github.com/storytold/pdfcraft/blob/main/README.md)
- [EffectCraft MCP — restricted file roots and command safeguards](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md)
- [DesignCraft MCP](https://github.com/storytold/designcraft/blob/main/docs/mcp.md)
- [GridCraft MCP](https://github.com/storytold/gridcraft/blob/main/docs/mcp.md)
- [WordCraft MCP](https://github.com/storytold/wordcraft/blob/main/docs/mcp.md)
- [DeckCraft MCP](https://github.com/storytold/deckcraft/blob/main/docs/mcp.md)
- [CADCraft MCP](https://github.com/storytold/cadcraft/blob/main/docs/mcp.md)
- [SoundCraft MCP](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md)
- [Earlier 12-app CLI/MCP integration reference](./Crafting_Apps_CLI_MCP_Integration_Reference.md) (reference from the previous deliverable)

---

## Final recommendation

**Build a local Claude Code integration project consisting of `.mcp.json` + one `craft` Skill + concise app references + deterministic preflight/contract/integration tests. No new MCP server.** Let the 12 native CLI servers own their tools and engines, and let Claude Code own their lifecycle and tool selection. Treat packaging as a Claude Code plugin **only after** direct local integration passes every acceptance gate and broader distribution is a concrete requirement.
