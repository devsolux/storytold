# Crafting Apps CLI and MCP Integration Reference

**Architecture and implementation reference for a unified MCP gateway serving Claude and ChatGPT**  
**Review date:** 2026-10-12 · **Projects:** 12 · **Language:** English  
**Source:** `storytold/*` GitHub repositories, `main` as publicly available at review time

> **Scope and evidence.** I reviewed the CLI entry-point source files and the CLI/MCP/agent documentation available through GitHub for all 12 projects, plus selected control-protocol and security documents. This is a source-grounded **integration reference**, not a claim of a complete line-by-line audit of every crate. This execution environment could browse GitHub source but **could not clone the repositories, compile their Rust workspaces, execute the CLIs, dump every live registry, or run their tests** (GitHub DNS/network was unavailable from the shell). Commands and tool names below are verified from published source/docs; examples are provided for implementation planning and are **not runtime-tested here**. Where a registry defines hundreds of commands, discover the authoritative current set from the built binary rather than treating this document as an exhaustive registry snapshot. Pin repository commits/releases and revalidate everything during implementation.

## 1. Executive architecture decision

**Build a thin, policy-enforcing MCP gateway over the existing native MCP servers. Do not reconstruct 12 command engines and do not put another LLM between client and engine.**

The upstream applications already own document semantics, command execution, formats, rendering, undo/history, and most MCP tool definitions. The missing responsibility is **cross-application discovery, session routing/lifecycle, unified authorization, safe local-vs-remote transport, resource limits, and a small discoverable interface**. Use one-shot CLI subprocesses only when a task is naturally stateless (conversion, validation, probing, isolated rendering), or when an application's native MCP interface lacks a needed one-shot capability.

### Suggested deployment

```text
             Claude Code / local MCP client
                         | stdio
                         v
                Craft MCP Gateway
                         ^
                         | authenticated remote Streamable HTTP
                         | (or supported secure tunnel)
                 ChatGPT custom MCP app
                         |
            +------------+-------------+
            | authorization + discovery|
            | app/session lifecycle     |
            | output/cost limits        |
            +------------+-------------+
                         |
                 MCP client adapters
                         |
    +--------------------+----------------------+-------------------+
    |                    |                      |                   |
 PhotoCraft CLI      GridCraft CLI        FilmCraft CLI         ... 9 more
   `mcp` (stdio)      `mcp` (stdio)         `mcp` (stdio)
    |                    |                      |
 native engine         native engine        native engine
 or live app           or live app          or live app
```

**Authority boundaries:**

1. **User/client** decides intent and approves high-impact actions.
2. **Gateway** deterministically enforces identity, permissions, executable allowlists, workspace roots, session ownership, transport and quotas. It does **not** infer permissions from tool descriptions or document content.
3. **Native MCP/CLI adapters** translate transport and preserve source tool schemas and results. They own no second copy of application semantics.
4. **Application engine** is final authority on valid commands, edit state, formats, undo semantics, and render results.
5. **Filesystem/process OS sandbox** is the external enforcement layer, especially for apps without a built-in root constraint. Engine-reported success is not proof that a file was written where expected.

**When *not* to build a gateway:** If a user needs only one app locally in Claude Code, register its own `*-cli mcp` directly. A gateway adds value only for unified cross-app access, scoped permissions, shared discovery, remote ChatGPT connectivity, session isolation, and operations policy.

## 2. Suite-wide capability matrix

Each link in the first column is to the actual project. Default MCP mode means the behavior of running `APP-cli mcp` with **no app-specific mode flags**; it is not necessarily equivalent across products.

| Application | Executable | Principal one-shot CLI operations | Native MCP default | Live-app argument | Typical desktop control |
|---|---|---|---|---|---|
| [PhotoCraft](https://github.com/storytold/photocraft) | `photocraft-cli` | `convert`, `info`, `run`, `batch`, `droplet`, `commands`, `serve` | Headless, file access scoped by flags | `--bridge ADDR` plus token | `7878`, token-authenticated |
| [VectorCraft](https://github.com/storytold/vectorcraft) | `vectorcraft-cli` | `run`, `convert`, `info`, `commands`, `bench`, `perf` | **Auto-detect live app, then headless fallback** | `--connect ADDR`; force `--headless` | `7979` |
| [FilmCraft](https://github.com/storytold/filmcraft) | `filmcraft-cli` | `exec`, `run`, `commands`, `describe`, `inspect`, `import`, `export`, `render`, `probe`, `bench-decode` | Headless, empty project | `--bridge ADDR` | `9876`, documented **without authentication** |
| [LightCraft](https://github.com/storytold/lightcraft) | `lightcraft-cli` | `run`, `render`, `snapshot`, `merge`, `synth-merge`, `denoise-serve`, `calibrate`, `commands`, `controls` | Headless photo session | `--connect [ADDR]` | `7980` |
| [PdfCraft](https://github.com/storytold/pdfcraft) | `pdfcraft-cli` | `info`, `render`, `text`, `edit`, `combine`, `extract`, `split`, `check`, `audit`, `tools`, `run`, `ui` | Headless, optionally `--root DIR`; MCP build feature required | **Separate** `ui --control FILE`, not a documented MCP `--connect` | Secure control-file/token channel |
| [EffectCraft](https://github.com/storytold/effectcraft) | `effectcraft-cli` | `info`, `commands`, `exec`, `run`, `props`, `get`, `set`, `render-frame`, `render`, `bench`, `script` | Headless, empty project by default | `--bridge PORT` | `9877` |
| [DesignCraft](https://github.com/storytold/designcraft) | `designcraft-cli` | `run`, `script`, `commands`, `describe`, `app`, `perf`, `bench`, `validate-pdf`, `links` | Headless document | `--connect PORT` | `7979` |
| [GridCraft](https://github.com/storytold/gridcraft) | `gridcraft-cli` | `info`, `convert`, `eval`, `cat`, `check`, `run`, `commands`, `functions`, `send` | Headless workbook | `--connect PORT` | `7979` |
| [WordCraft](https://github.com/storytold/wordcraft) | `wordcraft-cli` | `convert`, `info`, `text`, `inspect`, `render`, `run`, `commands`, `parity`, `zotero` | Headless document | `--connect HOST:PORT` | `7981`, key-authenticated |
| [DeckCraft](https://github.com/storytold/deckcraft) | `deckcraft-cli` | `info`, `render`, `convert`, `run`, `commands`, `describe`, `app`, `links` | Headless deck | `--connect PORT` | `7990` |
| [CADCraft](https://github.com/storytold/cadcraft) | `cadcraft-cli` | `info`, `convert`, `run`, `commands`, `perf`, `sample` | Headless drawing | `--connect HOST:PORT`, **fails on error** | `7979` |
| [SoundCraft](https://github.com/storytold/soundcraft) | `soundcraft-cli` | `info`, `convert`, `run`, `script`, `commands`, `describe`, `app`, `parity`, `plugins` | Headless DAW, no audio device | `--connect PORT` | `7801` |

**Port collisions:** VectorCraft, DesignCraft, GridCraft and CADCraft all document `7979` as a sample/default desktop control port. The gateway must allocate **distinct per-process ports** and never assume a port identifies the intended app. Require an explicit configured app target; reject identity/version mismatches.

**Native MCP naming is not uniform:** FilmCraft/PhotoCraft/VectorCraft/LightCraft/EffectCraft expose a common family (`command_list`, `command_run`, `command_batch`, `doc_inspect`, `render_preview`). Other apps expose domain names such as `execute`, `execute_command`, `run_command`, `inspect_workbook`, `inspect_session`. **Normalize at gateway discovery/routing, not by inventing unsupported engine command IDs.**

## 3. Source-by-source CLI and MCP reference

### 3.1 PhotoCraft — raster layers, masks and PSD

**Verified code:** [`apps/photocraft-cli/src/main.rs`](https://github.com/storytold/photocraft/blob/main/apps/photocraft-cli/src/main.rs) delegates to [`src/lib.rs`](https://github.com/storytold/photocraft/blob/main/apps/photocraft-cli/src/lib.rs). Also read [automation CLI](https://github.com/storytold/photocraft/blob/main/book/src/automation/cli.md), [automation MCP](https://github.com/storytold/photocraft/blob/main/book/src/automation/mcp.md), [MCP conventions](https://github.com/storytold/photocraft/blob/main/docs/mcp.md), and [control protocol](https://github.com/storytold/photocraft/blob/main/docs/control-protocol.md).

| CLI subcommand | Arguments / verified semantics |
|---|---|
| `convert IN OUT` | `--format EXT`, `--quality 1..100`, `--tiff-layers`, `--tga-bits 24\|32`. Format normally comes from output extension. |
| `info FILE` | `--compact`; document size, mode, depth, layer tree as JSON. Compact output includes missing-font warnings. |
| `run FILE` / `run --new JSON` | Repeat `--cmd ID [--params JSON]`; optional `--out FILE`, `--format`, `--quality`, TIFF/TGA flags. Each `--params` belongs to the previous command. One JSON result per command. |
| `batch --actions FILE --in DIR --out DIR` | Optional `--action NAME`, `--format`, `--quality`, `--in-place`, TIFF/TGA flags. Refuses same in/out directory unless `--in-place`. |
| `droplet FILE.pcdroplet FILE_OR_DIR…` | Optional `--out DIR`; runs a recorded droplet. |
| `commands` | `--filter TEXT`, `--json`; exposes registry and params docs. |
| `serve` | `--port PORT`, token options, `--automation-read-root DIR`, `--automation-write-root DIR`. Headless JSON-lines session over stdio or loopback TCP; not identical to MCP. |
| `mcp` | `--bridge ADDR`, `--control-token TOKEN` or `--control-token-file PATH`, independent read/write roots; stdio MCP. |

```bash
photocraft-cli info source.psd --compact
photocraft-cli run source.psd \
  --cmd image.adjustments.invert --out inverted.png
photocraft-cli batch --actions actions.json --in ./images --out ./processed --format jpg
photocraft-cli mcp --automation-read-root /work/input --automation-write-root /work/output
# Desktop app must have its own token-authenticated listener:
photocraft-cli mcp --bridge 127.0.0.1:7878 --control-token-file /private/control.token
```

**Action files:** `[["id",{...}], ...]`, `[{"command":"id","params":{...}}, ...]`, or bare command IDs; lists may be wrapped in `{"actions":...}` or `{"steps":...}`. **Native tools:** `command_list`, `command_run` (`id`, `params?`, `wait?`), `command_batch` (`steps`, `stop_on_error?`; **NOT atomic**), `doc_inspect`, `render_preview`, document/session/job tools, plus live UI operations in bridge mode. Direct headless video export has special progress/cancellation. **Critical security distinction:** one-shot CLI paths are ordinary OS paths; **MCP/serve roots** can confine them. Missing roots do not implicitly grant file access in scoped headless MCP. File-root security is not a replacement for tool authorization. CLI parser reports usage errors with exit status `2`; runtime errors `1`.

**MCP role:** Useful for complex PSD editing and long-lived layer/history state. Route opaque command JSON through engine registry. Never promise rollback from `command_batch`: earlier successful steps remain after failure. Save explicit copies before high-impact edits. Warn if fallback fonts change appearance.

### 3.2 VectorCraft — vector art and interchange

**Verified code:** [CLI `main.rs`](https://github.com/storytold/vectorcraft/blob/main/apps/vectorcraft-cli/src/main.rs), [MCP reference](https://github.com/storytold/vectorcraft/blob/main/docs/mcp.md), [control protocol](https://github.com/storytold/vectorcraft/blob/main/docs/control-protocol.md).

| Command | Arguments / semantics |
|---|---|
| `run` | `[--in FILE] [--cmd ID [--params JSON]]… [--export FILE]… [--scale N]`; steps execute in encounter order, JSON per step. `$N.path` references results of previous steps. |
| `commands` | Command registry JSON. |
| `convert IN OUT` | `--scale N`, `--artboard I` (0-based) or `--range 1-3,5` (1-based), `--outline-text`, `--replace-lossy`. Refuses certain lossy overwrite cases without explicit acknowledgement. |
| `info FILE` | JSON with import warnings, artboards, kinds, fonts. |
| `bench FILE` | `--size WxH`, `--iters N`; timing comparison. |
| `perf` | `--paths N`; synthetic performance budgets, nonzero on failure. |
| `mcp` | `--headless` or `--connect ADDR`; optional scoped roots for **headless only**. |

```bash
vectorcraft-cli mcp --headless  # IMPORTANT: prevent silent binding to a running app
vectorcraft-cli run --in art.vectorcraft \
  --cmd paint.setFill --params '{"fill":"#3366ff"}' --export out.svg
vectorcraft-cli convert art.vectorcraft out.pdf --range '1-3,5'
vectorcraft-cli mcp --automation-read-root /work/in --automation-write-root /work/out
```

**Critical mode behavior:** bare `mcp` tries `127.0.0.1:7979` and **falls back** to headless. Prefer explicitly `--headless` or `--connect` in production to prevent editing the wrong document. Root flags imply headless and conflict with `--connect`; desktop root flags must be applied on the desktop process instead. The documented resolver follows symlinks, treats read/write independently, and rejects path escapes; it is still subject to ordinary filesystem race concerns.

**Native tools:** `command_list/run/batch`, `doc_inspect`, `render_preview`, `list_commands`, `run_command`, `inspect_document`, `draw_shape`, `draw_path`, `set_paint`, `open_file`, `save_file`, `export`, `screenshot`, tool/pointer operations and live UI helpers. MCP can return PNG image content. `command_batch.atomic=true` can group edits into one undo step; do not confuse grouped undo with a guaranteed multi-file transaction. The extensive [MCP doc](https://github.com/storytold/vectorcraft/blob/main/docs/mcp.md) also describes resources, prompts and per-object drill-down; it explicitly notes its synchronous one-line/one-reply transport lacks active-call progress/cancellation and HTTP.

**Format caveat:** Native `.vectorcraft` plus many vector/raster read/export formats, not full semantic fidelity across conversions. Surface all import/export warnings. PDF/artboard selection conventions differ from other apps.

### 3.3 FilmCraft — video timeline, color and audio

**Verified code:** [CLI `main.rs`](https://github.com/storytold/filmcraft/blob/main/apps/filmcraft-cli/src/main.rs), [agent reference](https://github.com/storytold/filmcraft/blob/main/docs/agents.md), [desktop control protocol](https://github.com/storytold/filmcraft/blob/main/docs/control-protocol.md).

**CLI syntax:** global options can precede the subcommand: `--project FILE.fcproj`, `--demo`, `--save`, `--save-as FILE`, `--bridge ADDR`, `--data-dir DIR`, `--keep-going`, `--compact`. Commands are `exec ID [key=value... | JSON]`, `run FILE.jsonl|-`, `commands [FILTER] [--json]`, `describe ID`, `inspect [project|sequence]`, `import FILE...`, `export OUT`, `export --list-presets`, `render --seconds S --out FILE.png`, `probe MEDIA [--image-sequence]`, `bench-decode MEDIA [--frames N]`, `mcp`.

**Export flags:** `--preset NAME`, `--format FORMAT`, `--range entire|inOut|workArea`, `--start S`, `--end S`, `--settings JSON`, `--gpu-rendering auto|off`, `--scale FRACTION`, `--quality 0..100`, `--no-audio`, `--queue`, `--allow-offline`. Examples of documented formats include H.264, HEVC, ProRes, DNxHR, APV, MJPEG, MXF, image sequences/GIF, WAV/AIFF/AAC. Consult current help for full choices.

```bash
filmcraft-cli --project edit.fcproj inspect sequence
filmcraft-cli --project edit.fcproj --save exec timeline.razor seconds=3.5
filmcraft-cli --project edit.fcproj export review.mp4 --start 0 --end 10
filmcraft-cli mcp --demo
filmcraft-cli mcp --bridge 127.0.0.1:9876
```

**Script:** JSONL lines such as `{"id":"sequence.addEdit","params":{"seconds":3}}`. `key=value` recognizes JSON values and dotted nested fields. `run` stops at first failure unless `--keep-going`. CLI exit statuses: success `0`, execution failure `1`, usage error `2`. **Offline media subtlety:** an export may **write a file yet exit `1`** because clips were offline and placeholders appeared; `--allow-offline` explicitly accepts placeholders. Do not auto-retry such failures or assume the file is good based on existence alone.

**Native MCP:** `command_list`, `command_run`, `command_batch`, `doc_inspect`, `render_preview`, `project_inspect`, `sequence_inspect`, `media_import`, `render_frame`; bridge adds `ui_inspect`, `ui_elements`, `ui_click`, `ui_drag`, `ui_key`, `ui_type`, `ui_screenshot`, `ui_control`. Native export jobs support progress/cancellation via MCP when configured. **Security:** the documented `filmcraft --control 9876` listener is loopback-only **but unauthenticated** and its MCP headless mode has **no read/write root options**. Treat both as higher-risk and isolate by OS user/sandbox; don't expose the listener or wrap arbitrary `--bridge` hosts. Timestamps are measured using FilmCraft's internal tick timebase; commands may also accept seconds/frame/timecode.

### 3.4 LightCraft — photo catalog and RAW development

**Verified code:** [CLI `main.rs`](https://github.com/storytold/lightcraft/blob/main/apps/lightcraft-cli/src/main.rs), [MCP/CLI reference](https://github.com/storytold/lightcraft/blob/main/docs/mcp.md), [control protocol](https://github.com/storytold/lightcraft/blob/main/docs/control-protocol.md).

| Command | Key flags |
|---|---|
| `run` | `--demo`, `--library DIR`, repeated `--import PATH`, `--connect [ADDR]`, `--script FILE|-`, `--keep-going` and chained command IDs with `key=value` or JSON object. Prints `{"command","ok","result"|"error","ms"}` per command. |
| `mcp` | `--demo`, `--library DIR`, `--connect [ADDR]`, `--compact`, optional starting file/folders. |
| `render IN -o OUT` | repeated `--set CONTROL=VALUE`, `--settings JSONFILE`, `--preset ID`, `--size N`, `--quality Q`, repeated `--opt KEY=VALUE`. |
| `snapshot` | `--demo`, `--library`, `--script`, `-o/--output`, `--size WxH`, `--scale`; CPU-render the UI headlessly. |
| `merge hdr|panorama|hdr-panorama` | `--deghost`, `--no-align`, `--bracket`, `--projection`, `--boundary-warp`, `--auto-crop`, `--fill-edges`, `--no-auto-settings`, `--preview`. |
| `synth-merge` | Test-input generator for HDR/panorama. |
| `denoise-serve` | Separate **network service** for denoise models: `--listen`, `--token-env`, `--model`, `--models`, `--run-on`, `--max-connections`. This is NOT MCP. |
| `commands`, `controls`, `calibrate` | Command catalog, develop control/ranges, or camera profile calibration (`--max`, `--out`). |

```bash
lightcraft-cli run --import photo.dng develop.set control=light.exposure value=0.7 \
  app.export path=/work/out.jpg longEdge=2048
lightcraft-cli render in.dng -o out.tif --set light.exposure=0.5 --opt bitDepth=16
lightcraft-cli mcp --library /work/lightcraft-library --compact
```

**Native MCP:** shared command tools; `query_photos`, `import`, `select_photos`, `list_controls`, `get_develop`, `set_develop`, `apply_preset`, `crop`, `render_photo`, `export`; live mode adds widgets, clicks, pointer gestures, screenshots. `--compact` removes the very large auto-generated `cmd_*` tool set while retaining access via `run_command`. Importing with `mode:move` can **move and remove originals after verification**; require explicit authorization. Persistent `--library` writes survive subsequent sessions. **Library locking:** one process at a time; headless MCP cannot open a library the desktop app holds—use `--connect` instead. Export defaults may generate new filenames on collisions; repeated calls are not inherently idempotent. `denoise-serve` is plain TCP intended for protected LAN/VPN, requires careful token/network setup, and should not be started casually by an agent.

### 3.5 PdfCraft — PDF reading, manipulation and protection

**Verified code:** [CLI `main.rs`](https://github.com/storytold/pdfcraft/blob/main/apps/pdfcraft-cli/src/main.rs), [README automation](https://github.com/storytold/pdfcraft#built-for-agents-too), [control/security](https://github.com/storytold/pdfcraft#driving-the-app-itself).

| Subcommand | Syntax |
|---|---|
| `info` | `FILE.pdf [--password PW]` → JSON document summary. |
| `render` | `FILE.pdf --page N [--dpi 96] --out FILE.png` (also JPEG/TIFF/PAM). |
| `text` | `FILE.pdf [--page N]` → extracted text. |
| `edit` | `IN.pdf --out OUT.pdf [--rotate 1,3:90] [--delete 2,4] [--move 5:1] [--insert-blank 1] [--title T] [--author A] [--full]`. |
| `combine` | `A.pdf B.pdf … --out COMBINED.pdf`. |
| `extract` | `IN.pdf --pages 1,3,5 --out OUT.pdf`. |
| `split` | `IN.pdf (--every N | --before 3,7) [--out-dir DIR]`. |
| `check` | `FILES_OR_DIRS... [--timeout 20] [--dpi 36] [--json OUT.json]`; robustness harness forks children. |
| `audit` | `FILE.pdf [--password PW]`; identifies faux redactions; fails when found. |
| `tools` | Full JSON-Schema tool table. |
| `run` | `TOOL [key=value...] [--root DIR] [--out image.png]` or `--script FILE.json [--root DIR]`. |
| `mcp` | `--root DIR`, `--compact`; optional Cargo `mcp` feature (can be compiled out). |
| `ui` | `--control FILE METHOD [key=value...] [--out image.png]`; **separate authenticated desktop control channel**. |

```bash
pdfcraft-cli tools > pdfcraft-tools.json
pdfcraft-cli info document.pdf
pdfcraft-cli audit document.pdf
pdfcraft-cli run --script actions.json --root /work/pdfs
pdfcraft-cli mcp --root /work/pdfs --compact
# Desktop-side control is separate from headless MCP:
pdfcraft-cli ui --control /private/pdfcraft-control.json inspect query=rotate
```

**Native tool table:** JSON Schema definitions are first-class. MCP and CLI `run` share tools such as `doc_open`, `doc_inspect`, `page_render`, `text_find`, comments, forms, edits, security, undo/redo and `doc_save`. Run scripts preserve in-process document IDs, so do not spread dependent calls over separate one-shot `run` invocations. With `--root`, tool file paths, including image output, must be inside the root; the **script file itself may be read from outside**. The `mcp --compact` tool list retains a core and discovery/dispatch (`tool_search`, `tool_call`). Document edits are held in memory until `doc_save`. Save semantics include incremental atomic updates; confirm path ownership and permissions before overwriting.

**Security:** desktop control uses a secure control file and bearer token; follow upstream recommendations for owner-only locations and symlink avoidance. Do not treat PDF encryption/password permissions as a replacement for filesystem access controls. Before editing a PDF with redactions or sensitive content, use `audit` and verify actual sanitized output rather than assuming a drawn black rectangle removes text.

### 3.6 EffectCraft — compositions, keyframes and VFX

**Verified code:** [CLI `main.rs`](https://github.com/storytold/effectcraft/blob/main/apps/effectcraft-cli/src/main.rs), [agents reference](https://github.com/storytold/effectcraft/blob/main/docs/agents.md), [MCP conventions](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md).

**CLI operations:** `info`; `commands [--filter TEXT] [--enabled]`; `exec ID [--params JSON]`; `run ID JSON [ID JSON ...]`; `props COMP LAYER [--flat] [--time S]`; `get COMP LAYER PATH [--time S]`; `set COMP LAYER PATH VALUE [--time S] [--expression E]`; `render-frame [--comp C] [--time S|--frame N] [--max-side PX|--scale K] [--out FILE] [--transparent]`; `render [--comp C] --out FILE` with video/audio/image flags; `bench`, `script FILE.jsx | --eval CODE`, `mcp`. Common globals: `--project FILE.ecproj | --demo | --empty`, `--save | --save-as FILE`, `--bridge PORT`, `--json`, `--gpu`.

**Render controls:** `--start`, `--end`, `--work-area`, `--fps`, `--resolution full|half|third|quarter|K`, `--quality best|draft`, `--channels rgb|rgba`, `--jpeg-quality`, `--bitrate`, `--prores`, `--audio`, `--profile`, `--level`, `--rate-control`, `--video-quality`, `--keyint`, `--webm-codec`, `--audio-bitrate`, `--opus-app`, or render queue `--queue`. Formats include H.264, HEVC, AV1, ProRes, WebM, PNG, JPEG, TIFF, EXR, GIF, WAV, AIFF. `--template FILE.ectemplate --values values.json` supports template rendering.

```bash
effectcraft-cli --project intro.ecproj props Main '#1' --flat
effectcraft-cli --project intro.ecproj set Main '#1' transform/position '[100,360]' --time 0 --save
effectcraft-cli render intro.ecproj --comp Main --out intro.mp4
effectcraft-cli mcp --autosave --automation-read-root /work/in --automation-write-root /work/out
```

**Native MCP:** `list_commands`, `describe_command` with schemas, `execute_command`, `batch` (atomic rollback for that engine batch), `get_state`, `get_project`, `get_comp`, `get_layer`, `get_property`, `set_property`, `add_keyframe`, `list_effects`, `add_effect`, `render_frame`, `run_script`, open/save/history/undo; live UI tools behind `--bridge`. `mcp --autosave` is **headless-only**, writes checkpoints after modifying calls and helps recover from server restart. The actual checkpoint should still be verified; an interrupted edit before response may not be durable. `--automation-read-root`/`--automation-write-root` are supported for MCP, and documentation states **scripts are refused under those filesystem restrictions**.

**Data contracts/pitfall:** comp and layer IDs/names (or `#n` indexed layer); paths from `get_layer` such as `transform/position`; *set* keyframe times normally use **layer time**, while `get_property`/`render_frame` use comp time. Pass `timeBase: "comp"` explicitly when the layer is offset or stretched. Scripts can execute arbitrary JS-like project operations: classify them as privileged and do not offer unrestricted scripting to remote clients.

### 3.7 DesignCraft — page layout and publishing

**Verified code:** [CLI `main.rs`](https://github.com/storytold/designcraft/blob/main/apps/designcraft-cli/src/main.rs), [agent guide](https://github.com/storytold/designcraft/blob/main/docs/agents.md), [MCP reference](https://github.com/storytold/designcraft/blob/main/docs/mcp.md).

**CLI:** `run [--in FILE | --sample] [--cmd ID[=JSON]]... [--page N] [--scale S] [--pdf-options JSON] [--export OUT] [--all-pages DIR]`; `commands [FILTER]`; `describe ID`; `script FILE|- [--in FILE|--sample] [--connect PORT] [--save OUT] [--export OUT] [--keep-going]`; `app [--port PORT] COMMAND [JSON]` or `--method METHOD [JSON]`; `mcp [--connect PORT] [--sample]`; `perf`, `bench`, `validate-pdf FILE.pdf`, `links`.

```bash
designcraft-cli commands footnote
designcraft-cli describe xref.insert
designcraft-cli run --sample --cmd 'frame.create={"rect":[72,72,540,300],"content":"text","text":"Hello"}' \
  --page 0 --export page.png
designcraft-cli script pages.dcs --save pages.designcraft --export pages.pdf
```

**Script format:** lines of `command.id {json}`; JSONL or array of `{command, params}`; `#` comments. Step-result references `$N.path`, `$last.path` and `${N.path}` interpolation. Script results contain completed count and failed index/command/error; `--keep-going` changes continuation, not atomicity. **Export option ordering matters:** `--page`, `--scale` and `--pdf-options` apply to **following** `--export`/`--all-pages`, not preceding exports. It is an error to set one without a later export.

**Native MCP:** `list_commands`, `execute`, `batch`, `inspect_document`, `get_story`, `set_story_text`, `new_document`, `open_document`, `save_document`, `place_image`, `render_page`, `export_png`, selection/tool/keyboard; connected mode offers screenshots and dialog/pointer/menu operations. Coordinates are 1/72 inch (points), y down, **spread** space; page indices 0-based. **Text offsets are UTF-8 bytes, not Unicode code points**, including `text.select` and story-range operations. The gateway must not compute offsets from JavaScript `String.length` or Python character count without UTF-8 encoding. A failed connected request might have executed; inspect state before retrying. Native `.designcraft` supported; documented PDF export/validation and IDML interchange have evolving maturity; consult actual built binary and error warnings.

### 3.8 GridCraft — spreadsheets, formulas and workbook interchange

**Verified code:** [CLI `main.rs`](https://github.com/storytold/gridcraft/blob/main/apps/gridcraft-cli/src/main.rs), [CLI guide](https://github.com/storytold/gridcraft/blob/main/docs/cli.md), [MCP reference](https://github.com/storytold/gridcraft/blob/main/docs/mcp.md).

| Command | Options / result |
|---|---|
| `info FILE` | `--json`; sheets, used ranges, tables, charts, names. |
| `convert IN OUT` | `--sheet NAME`; output `.xlsx`, `.csv`, `.tsv`, `.json`, `.html`. |
| `eval FORMULA` | `--in FILE`, `--sheet NAME`, `--cell A1`, `--json`; formula evaluator. |
| `cat FILE` | `--range A1:D20`, `--sheet`, `--formulas`, `--csv`; human-readable or CSV. |
| `check FILE_OR_DIR...` | `--json`, `--tolerance 1e-9`, `--max-report N`; checks cached-formula oracle and XLSX round-trip. |
| `run` | `--in FILE` or `--sample budget|sales|grades`, repeated `--cmd 'id={json}'`, `--script FILE.jsonl`, `--out FILE`, `--print RANGE|used`, `--sheet`, `--csv`, `--formulas`, `--quiet`. |
| `commands`, `functions` | `--json`, `--search`; functions also `--category`. |
| `send PORT METHOD [JSON]` | One desktop JSON-control request. |
| `mcp` | `--connect PORT` or `--in FILE` or `--sample NAME`. |

```bash
gridcraft-cli eval '=PMT(5%/12,360,-300000)' --json
gridcraft-cli cat budget.xlsx --range B4:F15
gridcraft-cli run --sample budget --cmd 'cell.set={"cell":"D2","input":"=B2*C2"}' \
  --out /work/budget.xlsx --print A1:D5
gridcraft-cli mcp --in /work/budget.xlsx
```

**Scripts:** `id`, `id={json}`, `id {json}` or `{"command":"cell.set","params":{...}}` with `#` comments. `run` stops at first failing step; JSON for non-null command results. `check --json` has a documented versioned schema (`gridcraft-check/1`); exit `0` if all pass, `1` for mismatches/open failure, `2` usage. **Import fidelity warning:** `.xls`, `.xlsb`, `.ods` are *partial import* formats and cannot be saved back in those formats. `.xlsb` / `.ods` formulas may use cached values rather than recalculating source formula semantics. Do not claim round-trip equivalence.

**Native MCP:** `execute_command`, `list_commands`, `inspect_workbook`, `read_range`, `write_range`, `set_cell`, `get_cell`, `evaluate_formula`, `select`, `format_range`, `insert_chart`, `create_table`, `sort_range`, `filter`, open/save/new, undo/redo, `list_functions`, remote `screenshot`. Formula values can be numbers/text/boolean/null/error objects; preserve these types instead of coercing all to strings. No per-workspace file-root flags appear in the documented MCP syntax—enforce external sandbox/allowlists.

### 3.9 WordCraft — rich-text documents

**Verified code:** [CLI `main.rs`](https://github.com/storytold/wordcraft/blob/main/apps/wordcraft-cli/src/main.rs), [MCP guide](https://github.com/storytold/wordcraft/blob/main/docs/mcp.md).

| Command | Arguments |
|---|---|
| `convert IN OUT` | `--markup` for tracked changes/comments in supported outputs. Formats include `.docx`, `.doc` **read-only**, `.pdf`, `.odt`, `.rtf`, `.html`, `.md`, `.tex`, `.txt`, `.json`, `.png` (actual reader/writer capability differs). |
| `info FILE`, `text FILE`, `inspect FILE` | Metadata/word/page counts; extracted text; structure JSON. |
| `render FILE OUT.png` | `--page N`, `--scale S`. |
| `run` | `--file FILE` or `--template TEMPLATE`, repeated `--cmd 'id={json}'`, `--save OUT`, `--print`, `--author NAME` (CLI parser also recognizes `--page`/`--scale`). |
| `commands` | `--json`; engine catalog. |
| `parity` | `--markdown`; feature summary. |
| `zotero` | Zotero document integrations (`addEditCitation`, `addEditBibliography`, `addNote`, `refresh`, `removeCodes`, `setDocPrefs`), needs running Zotero; `--cmd`, `--save`, `--trace`, `--port`. |
| `mcp` | `--connect HOST:PORT` or `--author NAME`; headless default. |

```bash
wordcraft-cli inspect report.docx
wordcraft-cli convert report.docx report.pdf
wordcraft-cli run --template sample --cmd 'select.text={"text":"Membership"}' \
  --cmd format.bold --save revised.docx
wordcraft-cli mcp --author 'Claude (copyedit)'
```

**Native MCP:** `list_commands`, `execute`, `batch`, `new_document`, `open_document`, `save_document`, `type_text`, `select_text`, `get_text`, `inspect_document`, `render_page`, `parity`; connected mode adds screenshot, click, key and UI inspection. Desktop remote control uses a key (`WORDCRAFT_CONTROL_KEY` or secure key file) on loopback. **Tracked edits:** set an explicit `--author`; use `review.trackChanges {"value":true}` rather than toggling with empty parameters (which can turn tracking off). Rendering and formats require fidelity checks; missing fonts can change pagination or line breaks.

### 3.10 DeckCraft — slide decks

**Verified code:** [CLI `main.rs`](https://github.com/storytold/deckcraft/blob/main/apps/deckcraft-cli/src/main.rs), [MCP guide](https://github.com/storytold/deckcraft/blob/main/docs/mcp.md).

**CLI:** `info FILE`; `render (FILE | --sample) [--slide N | --all] [--scale S] [--edit] OUT`; `convert IN OUT`; `run [--in FILE | --sample] [--cmd ID[=JSON]]... [--save OUT] [--export OUT] [--print]`; `commands [FILTER]`; `describe ID`; `app [--port PORT] COMMAND [JSON] | --method METHOD [JSON]`; `mcp [--connect PORT] [--sample]`; `links`.

```bash
deckcraft-cli run --sample \
  --cmd 'slide.new={"layout":"titleOnly","title":"Hello"}' \
  --save hello.deckcraft
deckcraft-cli convert hello.deckcraft hello.pptx
deckcraft-cli mcp --sample
```

**Native MCP:** `list_commands`, `run_command`, `batch`, `new_presentation`, `open_presentation`, `save_presentation`, `export`, `inspect_document`, `inspect_slide`, `render_slide`, `add_slide`, `go_to_slide`, `add_shape`, `add_text_box`, `set_text`, `insert_picture`, `insert_table`, `insert_chart`, selection and input helpers; live `screenshot`, `call_app`. Export includes PPTX, PDF slides/notes/handouts, PNG/JPEG and outline. Native `.deckcraft` round trips may preserve semantics differently than PPTX/PDF. Review the effective tool discovery schema for exported formats; a [recent issue](https://github.com/storytold/deckcraft/issues/44) documented divergence between an MCP export schema and supported PDF options, with a subsequent fix. **Never treat descriptive MCP tool metadata alone as evidence of format fidelity; probe the actual command and verify its output.**

### 3.11 CADCraft — CAD/drafting

**Verified code:** [CLI `main.rs`](https://github.com/storytold/cadcraft/blob/main/apps/cadcraft-cli/src/main.rs), [MCP guide](https://github.com/storytold/cadcraft/blob/main/docs/mcp.md).

**CLI:** `info FILE.dxf`; `convert IN OUT [--window x0,y0,x1,y1 | --view extents|current]` (output `.dxf`, `.dwg`, `.svg`, `.png`, `.pdf` according to current source); `run [FILE|--sample|--metric] [--script TEXT|--script-file FILE.scr] [--cmd 'id {json}']... [--save OUT] [--export OUT] [--window|--view]`; `commands [FILTER]`; `mcp [--connect HOST:PORT]`; `perf [N|FILE]`; `sample (bracket|floorplan) OUT`.

```bash
cadcraft-cli run --sample --script 'CIRCLE 22,3 1\n' --save out.dxf --export out.png
cadcraft-cli info drawing.dxf
cadcraft-cli convert drawing.dxf drawing.svg --view extents
cadcraft-cli mcp --connect 127.0.0.1:7979
```

**Native MCP:** `command_line {text}`, `script {text}`, `execute {command,params}`, `list_commands`, `inspect_drawing`, `query_entities`, `render`, `new_drawing`, `open`, `save`, `cancel`; remote UI screenshot/inspect/click. `command_line` is the app's native CAD prompt (interactive syntactic grammar such as `line 0,0 @10,0 @0,5 c`), not a shell command. `query_entities` paginates handles/geometry; use `limit`/`offset` rather than huge full-drawing dumps. `--window` uses model-space drawing units; framing only applies to image outputs. **Explicit `--connect` fails** when the desktop is unreachable, so do not silently replace it with headless mode. Saving to SVG/PNG/PDF exports, and may leave the native drawing marked unsaved.

### 3.12 SoundCraft — audio / DAW

**Verified code:** [CLI `main.rs`](https://github.com/storytold/soundcraft/blob/main/apps/soundcraft-cli/src/main.rs), [MCP guide](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md).

**CLI:** `info FILE` (audio metadata JSON or `.scraft` session summary); `convert IN OUT [--bit-depth 16|24|32f] [--rate HZ] [--normalize]`; `run [--in FILE.scraft|--demo] [--cmd ID[=JSON]]... [--bounce OUT] [--start T --end T] [--save FILE.scraft] [--inspect]`; `script FILE [--in FILE|--demo] [--save FILE] [--bounce OUT]` (`ID JSON` per line); `commands [FILTER]`; `describe ID`; `app [--port PORT] METHOD [JSON]`; `mcp [--connect PORT] [--demo]`; `parity [--write PATH]`; `plugins`.

```bash
soundcraft-cli run --demo \
  --cmd 'mix.volume={"track":"Kick","db":-6}' \
  --cmd 'mix.insert={"track":"Bass","plugin":"eq_7band"}' \
  --bounce mix.wav
soundcraft-cli mcp --demo
```

**Native MCP:** `list_commands`, `execute`, `batch`, `inspect_session`, `new_session`, `open_session`, `save_session`, `import_audio`, `bounce_mix`, `parity`; connected mode adds UI screenshot/inspect/edit controls. Headless MCP uses the mix engine **without a live audio device**, so playback/recording hardware operations are not equivalent to an attached desktop DAW. Session format `.scraft`; audio imports WAV/AIFF/FLAC/MP3/OGG/AAC/M4A/ALAC/CAF; `bounce_mix` documents WAV/AIFF/FLAC and reports loudness measures. Time inputs can be samples, seconds objects or bars/beats notation. `save_session` refuses replacement of an existing unrelated target unless `replace:true`; make replacement consent explicit. `open_session` reports missing media—don't render a final deliverable without checking it.

## 4. Native capability discovery: runtime truth over static lists

A unified MCP server should **not** copy all command IDs into its own hand-maintained list. Generate snapshots using the actual binaries and the native MCP protocol in CI for each pinned release.

### Discovery commands by app

```bash
photocraft-cli commands --json
vectorcraft-cli commands
filmcraft-cli commands --json
lightcraft-cli commands --json
lightcraft-cli controls --json
pdfcraft-cli tools
effectcraft-cli commands --filter export
designcraft-cli commands
gridcraft-cli commands --json
gridcraft-cli functions --json
wordcraft-cli commands --json
deckcraft-cli commands
cadcraft-cli commands
soundcraft-cli commands
```

Also call native MCP `initialize` then `tools/list`, `resources/list` and (where implemented) `prompts/list`. **Do not assume every CLI prints the same JSON envelope**: some print pretty JSON, some JSONL, some text; MCP content may be JSON in `content[].text`, binary images as MCP image blocks, and/or `structuredContent`. Preserve image MIME types, warnings, stdout vs stderr, `isError`, and underlying exit codes in your adapter. Do **not** infer a JSON Schema solely from prose when the underlying registry exposes only a description (e.g. many `command_*` APIs); validate only what is actually specified and let the engine reject invalid params.

**Recommended generated artifacts (build-time, not hard-coded runtime permissions):**

- `catalog/<app>/<version>/cli-help.txt`
- `catalog/<app>/<version>/commands.json` (where machine-readable)
- `catalog/<app>/<version>/mcp-tools.json`
- `catalog/<app>/<version>/capabilities.json` (derived summary + manual corrections)
- `catalog/<app>/<version>/verified.json` (test results, commit/tag, binary hash and platform)

Use these for search/UI and drift detection, but always check **current session enablement**, command schemas and dynamic state before executing. A file's mere presence does not prove the exact binary version; record `--version` or `version` per app and hash the executable.

## 5. Suggested gateway contract — minimal coherent set

Expose a **small fixed tool surface**, while delegating domain operations to each native MCP server:

| Gateway tool | Responsibility | Mutation? |
|---|---|---|
| `craft_list_apps` | Installed/available apps, versions, modes, health and permission summary. | No |
| `craft_search_tools` | Search the native tool registry of an `app` with query/filter; return namespaced tool id, compact schema, annotations, and cost/permission category. | No |
| `craft_open_session` | Open one owned app session with explicit `app`, backend (`headless` or `desktop`), optional input document/library and bounded workspace; return an opaque `session_id`. | May open files; policy-dependent |
| `craft_call_tool` | Call an allowlisted native MCP tool in an existing session; preserve exact native arguments and return normalized envelope without inventing application behavior. | Depends on tool |
| `craft_close_session` | Close a session with explicit choice to save or discard **after confirmation** of dirty state; release child and locks. | Conditional |
| `craft_get_job` / `craft_cancel_job` | **Only if needed**: expose underlying native jobs/progress for apps that support them; do not simulate cancellation when it cannot happen. | Conditional |

Do **not** add a separate `craft_convert`, `craft_draw`, `craft_edit_video`, etc. layer until a real cross-app workflow requires it. These semantic actions already have owners. If tool-discovery volume is small enough, native app servers can be exposed directly by a namespaced aggregator with only `list/search/call` plus lifecycle.

### Example gateway tool arguments (proposed, not existing Craft tools)

```json
{
  "name": "craft_call_tool",
  "arguments": {
    "session_id": "sess_8c7e...",
    "app": "gridcraft",
    "tool": "read_range",
    "arguments": {"sheet": "Budget", "range": "A1:D12"}
  }
}
```

```json
{
  "name": "craft_call_tool",
  "arguments": {
    "session_id": "sess_8c7e...",
    "app": "gridcraft",
    "tool": "set_cell",
    "arguments": {"cell": "D2", "input": "=B2*C2"}
  }
}
```

**Gateway invariants** (must be deterministic, enforced outside any LLM):

1. `app`, tool name, session ID and backend identity must agree and belong to the same authenticated principal. No cross-session guessing or shared global active document.
2. Tool-name catalog is scoped to one pinned server version. No generic `shell`, `exec`, `run arbitrary file`, `eval arbitrary code` tool exposed.
3. Sensitive actions require explicit allowlist policy and, when applicable, client/user confirmation; source `readOnlyHint` is **advisory**, not authoritative policy.
4. Paths resolve against permitted read/write roots and reject traversal, escaping symlinks, remote/UNC shares if unapproved, and special devices. Use an OS sandbox for apps lacking native enforcement. Restrict spawn binary, args, env and cwd by config.
5. Persist side-effect provenance: app version, command, session, sanitized args, destination paths, outcome, and native warnings. **Do not log document contents or tokens.**
6. One writer per stateful session; serialize mutations unless the underlying engine explicitly supports concurrent calls. Protect against stale UI selection and stale document revisions.
7. On timeout/disconnect, a command might have executed. Return **indeterminate outcome** and require a re-inspection before retry; never auto-replay non-idempotent writes.
8. Exit code `0` or MCP `isError:false` is insufficient by itself: verify the requested file/artifact and domain-specific warnings before reporting completion.
9. No silent mode fallback from desktop to headless. Require explicit backend. This matters especially for VectorCraft.
10. Enforce resource budgets for CPU, memory, output size, image pixels, script length, open files, session idle TTL, concurrent jobs and long exports. Preserve authentic cancellation semantics.

### Suggested normalized response shape (gateway-owned only)

```json
{
  "app": "filmcraft",
  "session_id": "sess_8c7e...",
  "native_tool": "command_run",
  "ok": false,
  "outcome": "failed_after_side_effects_possible",
  "content": [],
  "warnings": ["offline media or source-provided warnings if any"],
  "native_error": {"kind": "tool", "message": "..."},
  "artifacts": [],
  "retry_safe": false
}
```

`outcome` may be `completed`, `rejected_before_execution`, `failed_after_side_effects_possible`, or `indeterminate`. This is a **proposed gateway status vocabulary**, not a native response. Include raw/typed MCP content when feasible rather than collapsing image data or detailed result metadata. `retry_safe` is a deterministic policy outcome, not an LLM prediction.

## 6. Process model, lifecycle and state

**Application sessions:** launch one pinned native `*-cli mcp` **per logical headless session**. Hold its stdin/stdout MCP conversation open; do not invoke `mcp` once per tool call. This retains selections, open documents, undo history, imported media and in-memory changes. `pdfcraft-cli run --script` and `lightcraft-cli run --library` are exceptions suited to bounded workflows, not equivalent replacements for a multi-call MCP session.

**Ownership:** gateway mints opaque session handles with user/tenant/app/version/back-end mapping; application engine owns actual document. Every request must supply a valid handle. For a desktop bridge, bind the handle to an explicit port and verify the target identity; do not silently spawn a new headless document if the app is disconnected.

**Saving:** do not assume the apps share a single dirty/commit API. PhotoCraft's batch is not atomic; VectorCraft and EffectCraft have grouped/atomic engine batches; PdfCraft edits remain in memory before `doc_save`; LightCraft may persist a catalog after each mutation and enforces a catalog lock; some DAW/media apps copy or move large external files. The gateway must preserve these distinct semantics rather than promising a universal transaction.

**Concurrency:** ideally single-thread mutation queue per session; independent read-only previews may be allowed only after checking native thread safety/transport behavior. Capture session and revision before a destructive edit and inspect again afterward. Limit session lifetime and implement graceful close; on abort preserve autosave/recovery guidance where the native server supports it.

**Progress/cancel:** PhotoCraft and FilmCraft document special long-export MCP progress/cancellation; EffectCraft has render/checkpoint behavior; VectorCraft explicitly lacks cancellation during a synchronous call in its existing stdio server. The gateway must forward progress where supported and otherwise offer honest job status and coarse process stop with clear side-effect warnings.

## 7. Remote ChatGPT support vs local Claude support

- **Claude Code / local clients:** launch gateway directly over stdio (or register each native server independently for baseline verification). Example configuration:

```json
{
  "mcpServers": {
    "craft-gateway": {
      "command": "/absolute/path/to/craft-gateway",
      "args": ["serve", "--transport", "stdio", "--config", "/private/craft-gateway.yaml"]
    }
  }
}
```

The `craft-gateway` binary and flags above are a **proposed design**, not a currently existing program.

- **ChatGPT:** according to [OpenAI's MCP developer-mode guidance](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt), it connects to **remote** MCP endpoints, not local stdio; use a suitably authenticated endpoint or [Secure MCP Tunnel](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt) to reach the local process. Write/modify support depends on plan/workspace/developer permissions; do not assume universal eligibility. Avoid exposing raw loopback app control ports through a tunnel. Expose only the gateway's authorized public transport.
- **Protocol:** official MCP transports include stdio for local and Streamable HTTP for remote. See the [MCP transports specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) and [MCP TypeScript SDK](https://ts.sdk.modelcontextprotocol.io/). Native repos often advertise newline-delimited JSON-RPC over stdio and subsets of MCP versions. Implement version/format adapters at the gateway edge and test against your chosen SDK. Do not assume every native server supports all 2026-era features, streamable HTTP, sampling, elicitation or cancellation.

**Authentication:** use upstream-supported OAuth / authenticated client integration as required for deployed ChatGPT MCP apps; enforce user-scoped authorization in the gateway. A token protecting a desktop control channel is **not** automatically an authentication policy for remote ChatGPT users. Do not store control tokens in URLs, rendered tool schemas, prompts or logs.

## 8. Mandatory security boundary for this suite

The applications expose powerful file, document, media, scripting and UI operations. In an MCP context, malicious document contents, filenames or tool descriptions can be prompt-injection inputs; none should expand permission.

| Risk | Concrete example | Gateway countermeasure |
|---|---|---|
| Unrestricted filesystem | FilmCraft MCP lacks root flags; CLI conversions use normal paths | OS filesystem sandbox, per-app workspace mount/allowlist, read vs write scope |
| Dangerous mutation | LightCraft `import` with `mode:move`; PdfCraft delete/redact; audio overwrites | Explicit risk categorization, safe defaults, confirmation for delete/move/overwrite |
| Remote UI compromise | FilmCraft control port lacks authentication; other app ports vary | Only loopback, isolated process/user, do not publish ports, gateway allowlist and binding |
| Token exfiltration | PhotoCraft control-token CLI flag or WordCraft key | Prefer private token files/env; redact logs; no secrets in tool replies |
| Arbitrary code/script execution | EffectCraft `script`/`run_script`, app-specific scripts/actions | Disable by default for untrusted/remote clients; separate privilege tier and sandbox |
| Unexpected live app | VectorCraft MCP auto-connect behavior | Force `--headless`, or explicitly verify connected app identity |
| Session crossover | Two users edit same LightCraft catalog, same desktop port, reused document IDs | Opaque owner-bound sessions; LightCraft lock-aware selection; per-app port allocation |
| Format fidelity loss | Pdf, SVG, PPTX, XLS/ODS and other conversions | Surface loss warnings and run content/layout/round-trip checks where available |
| Output spoofing | A tool returns 'success' but file missing or offline frames rendered | Check actual artifact and app-native status (e.g. FilmCraft offline media) |
| Repeated non-idempotent calls | Retry export after disconnect | Treat indeterminate result as unknown; inspect before any retry |
| Shell/flag injection | Filenames starting with `-`, hostile JSON, spaces | Spawn via argv array, never concatenate a shell command; use `--` where supported; validate per CLI grammar |
| Resource exhaustion | Large PSD/RAW/video/PDF, long encode, huge image return | Constrain CPU/RAM/time/image/output sizes and quotas; isolate subprocesses |

**Required default posture:** headless, least-privileged OS account, dedicated input/output mounts, no live control port, no network denoise service, no scripts, no destructive file changes, no silent overwrite, and no executing arbitrary CLI selected by the model. A separate opt-in profile may allow live desktop control with explicit approval and monitoring.

## 9. High-value integration recipes

### A. Spreadsheet report to presentation

1. GridCraft `open_workbook` → `read_range` / `evaluate_formula`, verify data and formula errors.
2. Gateway moves **structured data** between apps in memory; it does not recreate spreadsheet evaluation in a second LLM.
3. DeckCraft `new_presentation` → `add_slide`/`insert_chart`/`insert_table`; use native slide commands for layout.
4. DeckCraft `render_slide` for visual review; `save_presentation` native and optional `export` PDF/PPTX.
5. Reopen/inspect final deck and record warnings. Separate files have no shared transaction: preserve checkpoints.

### B. RAW development to layered composition

1. LightCraft open library/import asset → `get_develop` → `set_develop` → `render_photo`/export.
2. PhotoCraft open exported raster via `doc_open`, apply layer/mask commands through command registry, `render_preview`, then `doc_save`/export.
3. Preserve original RAW plus catalog state; new artwork lives in a different project. Do not assume RAW edits can be copied as identical PSD adjustment-layer parameters.

### C. Vector illustration into page layout

1. VectorCraft create/edit shape, `export` SVG/PDF/PNG as appropriate.
2. DesignCraft `place_image` into a frame; `get_story` / `inspect_document` to check overset text.
3. `render_page` then export. Be explicit about coordinate spaces (VectorCraft artboard vs DesignCraft spread) and embedding/linked files.

### D. Motion graphics into video/audio pipeline

1. EffectCraft composition `get_comp`, `set_property`/`add_keyframe`, render with consistent frame rate and alpha.
2. FilmCraft import rendered media, place/edit clips, inspect timeline and offline-media status.
3. SoundCraft optional sound work or FilmCraft native mix, depending on *one chosen owner* of final audio mix; avoid two authoritative mixes.
4. Export final FilmCraft sequence and verify file, audio and offline warnings. Track timebase conversions explicitly.

## 10. Validation plan before coding production gateway

### Phase 0 — executable + protocol baseline (required)

For **each** pinned app build/release on your target OS:

- [ ] Record repository commit, release tag, executable SHA256, `--version`/`version` and platform.
- [ ] Execute `--help` (and relevant subcommand help) and save output.
- [ ] Execute `commands` or `tools`; parse and snapshot the current registry (do not hard-code counts).
- [ ] Launch native `mcp` headless in a temporary sandbox; test `initialize`, `tools/list`, a read-only inspection and a minimal edit with save.
- [ ] Test image content and error envelopes (`isError`, JSON-RPC errors, stderr, process exits).
- [ ] Test desktop bridge only in a separate opt-in run, with verified app identity, port and token/key requirements.
- [ ] Test invalid flags, invalid/missing paths, symlink escapes and denied write requests.
- [ ] Test corrupt/unsupported input, missing fonts/media, big input, bad command params and cancellation or transport loss.
- [ ] Test whether failed operations partially mutate state; verify undo/save behavior.

### Phase 1 — small gateway (required)

Implement only: config/allowlist; stdio native MCP child adapter; discovery/search; owner-scoped session registry; `call_tool`; lifecycle; bounded output + errors; OS sandbox. Integration-test two distinct apps first, e.g. GridCraft and DeckCraft. Preserve native schemas; do not introduce semantic re-interpretation.

### Phase 2 — all 12 apps (recommended)

Add one config descriptor per app (binary, args, mode, sandbox policy, special checks), unit-test each mode/flag and file behavior; build a nightly capability-diff job against pinned versions. Add special risk guards for LightCraft move-import, PdfCraft redaction/save, FilmCraft offline exports, EffectCraft scripts, and VectorCraft auto-connection.

### Phase 3 — ChatGPT remote edge (required for ChatGPT integration)

Add authenticated Streamable HTTP or supported secure tunnel, user-scoped sessions, audit trail, rate limits and plan/workspace capability checks. No direct remote exposure of the native apps or app control ports. Test read-only and write-capable clients separately.

### Phase 4 — optional extras (only if needed)

Cross-app artifact manifests, resumable long-job UX, cache of *read-only* previews, workflow recipes, and versioned catalog embeddings for search. Only add these when testing identifies the specific missing responsibility.

## 11. Recommended repository structure for **your new project**

This is a design suggestion, not extracted from the repositories:

```text
craft-mcp-gateway/
├── README.md
├── config/
│   ├── apps.example.yaml         # binary allowlist, headless/live modes, roots
│   └── policy.example.yaml       # permissions, quotas, human confirmations
├── src/
│   ├── server/                   # local stdio and optional remote MCP transport
│   ├── discovery/                # native MCP tools/list, caching, search
│   ├── sessions/                 # app/session identity and child lifecycle
│   ├── native_mcp/               # subprocess stdio client, request/response transport
│   ├── policy/                   # authorization, paths, tool risk, limits
│   ├── artifacts/                # output metadata, verification, not another renderer
│   └── apps/                     # per-app configuration + minimal compatibility quirks
├── tests/
│   ├── contract/                 # 12 pinned CLI/MCP snapshots
│   ├── security/                 # escape, auth, collision, replay, stale-state
│   ├── integration/              # real installed apps with fixtures
│   └── e2e/                      # Claude local and ChatGPT remote
└── catalog/                      # generated, versioned capability snapshots
```

A Rust implementation aligns with upstream workspaces and can link native crates **later** if a real embedding need emerges. A TypeScript/Python implementation is also viable when it acts purely as a standards-conformant MCP client/gateway; pick based on your team's runtime, SDK support and deployment, not to introduce another agent layer. The *smallest coherent implementation* is a normal MCP server plus stdio MCP clients, a process manager, strict policy and tests.

## 12. Primary source index

Direct code entry points (reviewed):

| App | CLI implementation | Domain docs |
|---|---|---|
| PhotoCraft | [CLI main](https://github.com/storytold/photocraft/blob/main/apps/photocraft-cli/src/main.rs), [CLI lib](https://github.com/storytold/photocraft/blob/main/apps/photocraft-cli/src/lib.rs) | [CLI](https://github.com/storytold/photocraft/blob/main/book/src/automation/cli.md), [MCP](https://github.com/storytold/photocraft/blob/main/docs/mcp.md), [control](https://github.com/storytold/photocraft/blob/main/docs/control-protocol.md) |
| VectorCraft | [CLI main](https://github.com/storytold/vectorcraft/blob/main/apps/vectorcraft-cli/src/main.rs) | [MCP](https://github.com/storytold/vectorcraft/blob/main/docs/mcp.md), [control](https://github.com/storytold/vectorcraft/blob/main/docs/control-protocol.md) |
| FilmCraft | [CLI main](https://github.com/storytold/filmcraft/blob/main/apps/filmcraft-cli/src/main.rs) | [Agents/CLI](https://github.com/storytold/filmcraft/blob/main/docs/agents.md), [control](https://github.com/storytold/filmcraft/blob/main/docs/control-protocol.md) |
| LightCraft | [CLI main](https://github.com/storytold/lightcraft/blob/main/apps/lightcraft-cli/src/main.rs) | [MCP+CLI](https://github.com/storytold/lightcraft/blob/main/docs/mcp.md), [control](https://github.com/storytold/lightcraft/blob/main/docs/control-protocol.md) |
| PdfCraft | [CLI main](https://github.com/storytold/pdfcraft/blob/main/apps/pdfcraft-cli/src/main.rs) | [README agents](https://github.com/storytold/pdfcraft/blob/main/README.md) |
| EffectCraft | [CLI main](https://github.com/storytold/effectcraft/blob/main/apps/effectcraft-cli/src/main.rs) | [Agents/CLI](https://github.com/storytold/effectcraft/blob/main/docs/agents.md), [MCP](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md) |
| DesignCraft | [CLI main](https://github.com/storytold/designcraft/blob/main/apps/designcraft-cli/src/main.rs) | [Agents/CLI](https://github.com/storytold/designcraft/blob/main/docs/agents.md), [MCP](https://github.com/storytold/designcraft/blob/main/docs/mcp.md) |
| GridCraft | [CLI main](https://github.com/storytold/gridcraft/blob/main/apps/gridcraft-cli/src/main.rs) | [CLI](https://github.com/storytold/gridcraft/blob/main/docs/cli.md), [MCP](https://github.com/storytold/gridcraft/blob/main/docs/mcp.md) |
| WordCraft | [CLI main](https://github.com/storytold/wordcraft/blob/main/apps/wordcraft-cli/src/main.rs) | [MCP](https://github.com/storytold/wordcraft/blob/main/docs/mcp.md) |
| DeckCraft | [CLI main](https://github.com/storytold/deckcraft/blob/main/apps/deckcraft-cli/src/main.rs) | [MCP](https://github.com/storytold/deckcraft/blob/main/docs/mcp.md) |
| CADCraft | [CLI main](https://github.com/storytold/cadcraft/blob/main/apps/cadcraft-cli/src/main.rs) | [MCP](https://github.com/storytold/cadcraft/blob/main/docs/mcp.md) |
| SoundCraft | [CLI main](https://github.com/storytold/soundcraft/blob/main/apps/soundcraft-cli/src/main.rs) | [MCP](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md) |

Other applicable external references: [ChatGPT MCP developer-mode guidance](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt), [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports), [MCP SDK overview](https://ts.sdk.modelcontextprotocol.io/).

### Limits and outstanding verification

- **Complete clone and compilation:** not achieved in the current environment; no tests were run. All 12 CLI entry-point source files and documented MCP surfaces were accessed via the web.
- **Full dynamic command/tool catalogs:** **not enumerated**; they change as repositories evolve and must be generated with the prescribed `commands`/`tools`/MCP `tools/list` calls against a pinned binary.
- **Version pinning:** source links target `main` and are therefore mutable; pin exact SHAs/tags before implementation.
- **Control-channel authentication:** specifically verified for FilmCraft (not authenticated), PhotoCraft (token), PdfCraft (token/control file), and WordCraft (key). For the other apps, **do not infer authentication**; investigate actual control-server code and bind to loopback/sandbox until verified.
- **Headless filesystem confinement:** verified native flags for PhotoCraft, VectorCraft and EffectCraft, and `--root` for PdfCraft. Other apps must be treated as unconfined unless a source/runtime audit proves otherwise.
- **Not an official upstream manual:** this is a consolidation and architecture analysis; treat each repository's executable help and command registry as its operational source of truth.

---

**Bottom line:** A unified **Craft MCP Gateway** should be an *authorization + discovery + session/transport router*, not another editing engine or reasoning agent. Test existing native MCP endpoints directly first. Preserve their separate document models, file semantics, time/coordinate systems, and error/undo behavior; then add only the cross-app capabilities that are genuinely missing.
