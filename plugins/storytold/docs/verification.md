# Verification status — 1.6.1

Native application and host *acceptance* (M0–M4) remain **not run**: this
repository neither ships nor executes Craft binaries. All fifteen CLIs have
passed the native probe through runner-run `setup` on GitHub runners, and all fifteen
through operator-run `setup` on a developer Mac (FigCraft there since October 18,
MaterialCraft and TextureCraft since November 13, 2026; tables below). That is M0-level evidence, not acceptance.
PdfCraft's, MaterialCraft's and TextureCraft's app scenarios are the acceptance runs so far
(November 13, 2026, below); they do not make any M gate pass. This report separates the checks actually executed for each
release from documentary evidence.

## TextureCraft acceptance scenario on the developer Mac — November 13, 2026

Operator-run on macOS (Darwin 27, arm64) with Python **3.11.18** and the official
MCP SDK **2.3.0**: the pinned `texturecraft-cli` 0.6.1 launched directly with its
registered arguments (`mcp --automation-read-root {work} --automation-write-root
{outputs}`, working directory `{work}`, from `preflight`). Inputs were the
built-in cube exported by TextureCraft as `.glb` and MaterialCraft's exported
height map from the run below, both staged with `stage`. Logs, renders and the
summary are kept privately outside the workspace; nothing from them is
committed.

| Required evidence (`tests/native/acceptance.json`) | Result |
|---|---|
| immutable_revision, binary_sha256 | `34a1961` = manifest commit (`--version` 0.6.1); binary SHA-256 = installation lock = the Sigstore-signed CLI hash; `preflight` ready. |
| help_and_flags | `mcp [--bridge] [--token] [--read-root] [--write-root]` with the `--automation-*` aliases the catalog uses. |
| initialize_and_tools_list, read_only_fixture_call | texturecraft 0.6.1, protocol 2025-11-25, 22 tools; session_inspect on the default session and the imported cube. |
| headless_no_gui | No socket held at start or end of any session, no TextureCraft entry in `lsappinfo list`. |
| native_save_export_reopen | Steps: mesh_import (256); paint_stroke; a fill layer; resource_import of the height map as a height layer; CPU bake of ambient occlusion and curvature; project_save; textures_export with the default preset; viewport_render 3D and 2D; mesh_export `.glb`. The reopened `.tcraft` gave the same texture sets (resolution, channels, baked maps) and layers (sources, painted tiles), and a byte-identical 3D render. The reimported `.glb` has the same topology (1728 triangles, 1014 vertices). The six textures match the export plan in size and bit depth (16-bit height, 8-bit others). The project ZIP is intact and embeds the height map byte-identical to MaterialCraft's export. `verify-artifact --format png` passed. |
| original_hashes_unchanged | `verify-inputs`: all staged inputs unchanged; outside files unchanged. |
| warnings_reviewed | Export plan and export: none. A non-ZIP `.tcraft` was a typed error ("malformed project file"). |
| failure_and_boundary_test | Refused with a clear error: absolute paths, `../`, a symlink in inputs pointing outside, resource_import and bake_mesh_add from outside, `file.save` and `textureSet.meshMap.import` through command_run ("with host paths is disabled"), project_save to /tmp and `../`. A missing file, an unknown command and a wrong parameter type were typed errors, and the server answered afterwards. |

Observed beyond the checklist, now in the TextureCraft card and the handoff
guide:
- **The MaterialCraft link is broken at the pinned pair** (storytold/texturecraft#473):
  - **`.mcmat`:** material_load refused MaterialCraft 0.4.1's file with
    "unsupported: MaterialCraft material version 2 (this version reads up to 1)".
  - **`.mcraft`:** refused with "malformed project file: specified file not found
    in archive". This is not the "material.json is missing" that the issue
    predicted from source.

  The exported-map route works.
- **Overwrite.** project_save over an existing `.tcraft` replaced it without
  asking. Over a hard-linked name it wrote a new file and left the other link
  unchanged.

**Not run:** the host-level M1 test, OS isolation, GPU bakes and high-poly or cage
bakes, a re-cook through `materialcraft-cli`, UDIM, and real-world meshes in other
formats.

## MaterialCraft acceptance scenario on the developer Mac — November 13, 2026

Operator-run on macOS (Darwin 27, arm64) with Python **3.11.18** and the official
MCP SDK **2.3.0**: the pinned `materialcraft-cli` 0.4.1 launched directly with
its registered arguments (`mcp --read-root {work} --write-root {outputs}`,
working directory `{work}`, both from `preflight`). Fixtures were packages
MaterialCraft saved from its built-in "Atomic sample", copied out of the
workspace and staged with `stage`. Logs, renders and the summary are kept
privately outside the workspace; nothing from them is committed.

| Required evidence (`tests/native/acceptance.json`) | Result |
|---|---|
| immutable_revision, binary_sha256 | `65f7bfd` = manifest commit (`--version` 0.4.1); binary SHA-256 = installation lock = the Sigstore-signed CLI hash; `preflight` ready. |
| help_and_flags | `mcp [--bridge] [--token] [--read-root] [--write-root]` with the `--automation-*` aliases; an unknown option (`mcp --help`) exits 1. |
| initialize_and_tools_list, read_only_fixture_call | materialcraft 0.4.1, protocol 2025-11-25, 20 tools; session_inspect on the default session and the staged package, package warnings empty. |
| headless_no_gui | No socket held at start or end of any session, no MaterialCraft entry in `lsappinfo list`. |
| native_save_export_reopen | node_param Blur intensity 1.5→4.0, package_save as `.sbs` and `.mcraft`, outputs_export (`Atomic_sample_height.png`, 256×256, 16-bit gray, matching the graph's u16 at 256), view_render 3D and 2D reviewed; both reopened packages' graphs (nodes, parameters, connections, format, size) equal the edited graph, package warnings empty. `verify-artifact --format png` passed. |
| original_hashes_unchanged | `verify-inputs`: all staged inputs unchanged; the outside files used as targets unchanged. |
| warnings_reviewed | None on clean packages. A non-XML file was a typed error ("not a MaterialCraft package"). The dependency fixture's warning is below. |
| failure_and_boundary_test | Refused with a clear error: absolute paths ("path rejected (absolute)"), `../` ("`.` or `..` component"), a symlink in inputs pointing outside ("a path led outside of the filesystem"), bitmap_import from outside, `command_run file.save` with a host path, package_save to /tmp and `../`. A missing file and an unknown node id were typed errors, and the server answered afterwards. |

Observed beyond the checklist, now in the MaterialCraft card and `safety.md`:
- **Dependency reads outside the read root.** A staged package instancing a graph
  from dependencies outside the workspace opened without error:
  - **Absolute dependency:** a canary package whose base colour was set to
    (0.9, 0.1, 0.2) cooked exactly that colour in the instance node, and its
    graph's outputs were listed.
  - **Relative `../../../..` dependency:** resolved the same way.
  - **Missing dependency:** produced a `Could not resolve <absolute path>: No
    such file or directory` warning, so file existence leaks.

  The outside files were not modified. This confirms at runtime what the
  November 12 source review found and upstream was told.
- **Overwrite and save path.** package_save over an existing outputs file
  replaced it without asking. Over a hard-linked name it wrote a new file and
  left the other link unchanged. Without a path, after a save, it wrote to the
  last saved path.
- **Image outputs only.** outputs_export wrote the image output only; the
  graph's value output produced no file.

**Not run:** the host-level M1 test, OS isolation, `.mcmat` export and the
TextureCraft handoff (known broken, storytold/texturecraft#473), bitmap
resources, `sbs://` library packages, large graphs and `.sbs` files from other
tools.

## PdfCraft acceptance scenario on the developer Mac — November 13, 2026

Operator-run on macOS (Darwin 27, arm64) with Python **3.11.18** and the official
MCP SDK **2.3.0**: the pinned `pdfcraft-cli` 0.21.1 launched directly with its
registered arguments (`mcp --automation-read-root {work} --automation-write-root
{outputs} --root {work} --compact`, working directory `{work}`), not through the
host, whose PdfCraft server predated the upgrade. Fixtures were generated
synthetic PDFs (two pages, a text field, a document `/OpenAction` script and a
marker string) staged with `stage`. The full logs, renders and summary are kept
privately outside the workspace; nothing from them is committed.

| Required evidence (`tests/native/acceptance.json`) | Result |
|---|---|
| immutable_revision, binary_sha256 | `b503b2e` = manifest commit; binary SHA-256 = installation lock = the Sigstore-signed CLI hash; `preflight` ready. |
| help_and_flags | `--version` 0.21.1; `mcp` takes `--root`, `--compact` and the two automation roots only. |
| initialize_and_tools_list, read_only_fixture_call | pdfcraft 0.21.1, protocol 2025-06-18, 17 compact tools; doc_inspect, doc_info, text_extract and form_fields on the fixture without error. |
| headless_no_gui | Four server sessions: no socket held at start or end, no PdfCraft entry in `lsappinfo list`; stderr names both roots. |
| native_save_export_reopen | page_rotate (page 2, 90°), doc_set_info Title, redact_mark and redact_apply on the marker, doc_save to a new outputs path, reopen: 2 pages, page 2 at 90° (792×612), new Title, field value kept, marker not found, doc_audit_redactions 0 findings; both pages rendered and reviewed. `verify-artifact --format pdf` passed (marker checks only). |
| original_hashes_unchanged | `verify-inputs`: all unchanged; the files outside the workspace used as escape targets unchanged. |
| warnings_reviewed | None on the clean fixture. A truncated copy opened as a one-page document: doc_open's reply showed nothing, doc_info listed `repairs`, `unreadable_objects` and a warning. |
| failure_and_boundary_test | Refused with a clear error: absolute paths (/etc/hosts, a file outside), `../` traversal, a symlink in inputs pointing outside, a save into the read root, to /tmp and through `outputs/../../`. A missing file, a wrong parameter type and an unknown document id were typed errors, and the server answered afterwards. |

Observed beyond the checklist, now in the PdfCraft card:
- **JavaScript on open:** `js_enabled` is on in every new server session, and
  opening the fixture ran its `/OpenAction` script. The open reply was already
  dirty with the undo step "Run JavaScript", and the field changed. With
  `js_enabled {enabled: false}` first, it did not change.
- **Script listing:** `js_document_scripts` returned none for the `/OpenAction`
  script while doc_info said `has_javascript: true`. The saved output keeps the
  script.
- **Overwrite:** `doc_save` over an existing outputs file replaced it without
  asking. Over a hard-linked name it wrote a new file (new inode, mode 0600) and
  left the other link unchanged.
- **Redaction:** besides the app's audit, a stdlib scan of the raw and
  Flate-decoded streams found no trace of the marker in Latin-1, UTF-16BE or hex
  form, while the kept text was present. Text extraction order changed around
  the redacted span.

**Not run:** the host-level M1 test (Claude Code `/mcp`, approval, a failing
server's isolation), OS isolation, LibreOffice and Tesseract conversions, printing,
signing, real-world documents, and fidelity in other viewers.

## MaterialCraft and TextureCraft on the developer Mac — November 13, 2026

Operator-run on macOS (Darwin 27, arm64) with Python **3.11.18**:
`setup --app materialcraft --app texturecraft`, after a `--dry-run` that predicted
both `registered`.

| App | Result |
|---|---|
| MaterialCraft 0.4.1 | `materialcraft-cli-0.4.1-macos-universal.zip` (11.9 MB), notarized by `DJ6XS33FX8` and Sigstore-verified; probe at `65f7bfd` `discovery_and_call_passed` (MCP 2025-11-25, SDK 2.3.0): 20 tools and the `session_inspect` smoke call. Registered with Claude Code as `mcp --read-root {work} --write-root {outputs}`. |
| TextureCraft 0.6.1 | `texturecraft-cli-0.6.1-macos-universal.zip` (16.9 MB), notarized by `DJ6XS33FX8` and Sigstore-verified; probe at `34a1961` `discovery_and_call_passed`: 22 tools and `session_inspect`. Registered as `mcp --automation-read-root {work} --automation-write-root {outputs}`. |
| Afterwards | `setup --list`: both hashes match their pins at the manifest commit; `doctor`: all fifteen apps `registered` with `up_to_date: true`; `claude mcp list`: both connected. Every probed tool name appears in its card except the bridge-only `ui_*` tools, which both cards cover as a group. |

**Not run:** no native edit, export, root denial or handoff. MaterialCraft's dependency reads
outside the read root (reported upstream) and the broken MaterialCraft→TextureCraft link
(storytold/texturecraft#473) rested on source review at the time; the MaterialCraft
acceptance run above has since observed the dependency reads.

## Card recheck at the November 12 releases — November 13, 2026

macOS (Darwin 27, arm64) with Python **3.11.18**, plus GitHub:

| Check | Result |
|---|---|
| Source review | All fifteen apps from their last rechecked tags to the 2026-11-12 pins on blob-less clones, nine reviewers; findings per app in the [source ledger](source-ledger.md). Every catalog launch accepted with unchanged meaning, every smoke tool present with no required parameter and read-only, no tool removed or renamed; WordCraft adds one tool and PdfCraft nineteen. No `config/apps.json` change. |
| Operator `setup --upgrade` on the developer Mac | The thirteen installed CLIs moved from 0.6.0–0.10.0 to the pins: notarized by `DJ6XS33FX8` and Sigstore-verified, probe `discovery_and_call_passed` each, registrations unchanged, `setup --list` hash and manifest commit matching, `claude mcp list` connected. Their probe `tools/list` matches the reviewed tool definitions. MaterialCraft and TextureCraft were installed there afterwards (section above). |
| Runners | Run 43231479584 (the pin move) and run 43432074822 (main at 1.6.5): the three `verify` jobs ran the strict `setup --all` on Linux, Windows and macOS and passed. |
| Binary strings | FilmCraft's `tts.downloadVoices` and `transcript.downloadModel` ids are present in the installed pinned macOS CLI (searched as bytes, not run). |
| `make check`, `make test`, `make build`, `make verify-build` | Passed: 77 checks, **292 tests**. |

**Not run:** no release archive was unpacked, so the CLI's place inside each archive rests on
the packaging scripts and the runners' `setup`; the shared release workflow in
craft-common-actions was not reviewed. New behaviour (PhotoCraft's path-less save refusal,
PdfCraft's document JavaScript, MaterialCraft's dependency reads, the broken
MaterialCraft→TextureCraft link, the download commands) was read in source, not exercised.

## Release refresh every third day — November 13, 2026

| Gate | Result |
|---|---|
| `make check`, `make test`, `make build`, `make verify-build` | Passed: 77 checks, **292 tests** (1 new in `tests/test_bump_release.py`: the workflow's only cron is `23 5 */3 * *`, `workflow_dispatch` stays, and the manifest's Sigstore identity names `releases.yml` by path, so the rename leaves signing alone; the changelog-section test now expects "the Craft release refresh"). Both workflows parse (Ruby YAML). |
| Before the change | `gh run list` on 2026-11-13: the scheduled run of that day (43432074822) passed with no pin moved; every app's latest release equals its 2026-11-12 pin. |

**Not run:** the new schedule has not fired yet; the first scheduled run after the push is
on the next day of the month in 1, 4, …, 31.

## Doctor reports installs behind their pin — November 13, 2026

macOS (Darwin 27, arm64) with Python **3.11.18**:

| Gate | Result |
|---|---|
| `make check`, `make test`, `make build`, `make verify-build` | Passed: 77 checks, **291 tests** (4 new in `tests/test_doctor.py`: an older pin is `registered_outdated` with the `--upgrade` step, the manifest pin stays `registered`, a manifest commit with a label from before the root flags is outdated as `setup` decides it, and a registration without a lock entry stays `registered` with `up_to_date: null`; the `cli_not_registered` case now asserts its `--upgrade` step). |
| `doctor` on the developer Mac | Before the operator's upgrade all thirteen installed CLIs read `registered` at pins from 0.6.0 to 0.10.0 against the 2026-11-12 manifest; with the change, each one not yet upgraded reads `registered_outdated` and each upgraded one `registered` with `up_to_date: true`. MaterialCraft and TextureCraft stay `desktop_app_only`. |

**Not run:** doctor still reads the lock alone and does not hash the binary; `setup --list`
remains the check that the installed file matches its pin.

## First runs of all fifteen apps — November 5 and 6, 2026

Read from the logs of the daily release workflow. Both runs used the strict
`setup --all --acknowledge-unconfined` of its `verify` jobs on `ubuntu-latest`,
`windows-latest` and `macos-latest`.

| Gate | Result |
|---|---|
| Scheduled run 42034977077 on `3ade728` (release 1.6.1) | All jobs passed. `refresh` moved thirteen pins and signed the six MaterialCraft and TextureCraft archives, so `config/signatures.json` went from 39 to 45 bundles. `verify` ran pull request #17 at `0148f21` and installed fifteen apps on each runner, the first execution of MaterialCraft and TextureCraft. Merged as `de5f89e`, published as v1.6.1. |
| Scheduled run 42222471577 on `de5f89e` | `refresh` and all three `verify` jobs passed; `publish` and `merge` were skipped because no pin moved. On each runner, fifteen apps were installed with `sigstore` in their label and no checksum-only fallback, and each passed its probe twice, staged and installed. MaterialCraft and TextureCraft answered `session_inspect`. |

CLI sizes in the second run: 21–263 MB on macOS, 9–116 MB on Linux and 10–127 MB
on Windows.

**Not run:** the runners have no host CLI, so every app ended
`installed_no_host_cli` and nothing was registered. MaterialCraft and TextureCraft
have not run on a developer machine, and a probe does not prove output correctness
or root enforcement (see [acceptance](acceptance.md)).

## Executed for 1.6.0 — November 5, 2026

macOS (Darwin 27, arm64) with Python **3.11.18**, plus GitHub:

| Gate | Result |
|---|---|
| `make release` | `make check` passed, **287 tests** (none new since the entry below), build, verify-build and reproducible 1.6.0 plugin and source ZIPs. |
| `make test-sdk` | The 8 synthetic-fixture checks passed with `mcp` 2.3.0 from the hash-locked `.venv`. |
| `make host-validate` (Claude Code 2.1.282) | `claude plugin validate --strict` passed for the 1.6.0 manifests. |
| CI run 42031487622 on `434a822` | All seven jobs passed: `core` on Linux, macOS and Windows with Python 3.11 and 3.13, and `sdk-contract`. |

**Not run:** the release workflow has not run on these changes. Neither new app has
executed, no Craft binary has been probed under the new tool rules, and the six new
archives are unsigned, so a real `setup --all` on Linux or Windows stops at MaterialCraft
without `--trust-upstream-sums` until that run. The earlier items below still stand.

## MCP 2026-07-28 tool schema rules — November 5, 2026

| Gate | Result |
|---|---|
| `make test` | **287 tests** passed, the new ones covering rejected and accepted `inputSchema` roots, `outputSchema` forms and stored evidence. |
| `make test-sdk` | Official SDK 2.3.0 against the synthetic fixture: 8 checks passed, including the new `tool-schema-2026-07-28-round-trip`. No Craft app ran. |
| Source audit | All fifteen apps build `type: "object"` input schemas (see the [source ledger](source-ledger.md)). |

**Not run:** no Craft binary was probed under the new rule. The next release-workflow
run does that, and one nonconforming tool would stop it.

## Card recheck at the November 5 releases — November 5, 2026

| Gate | Result |
|---|---|
| Card recheck at the thirteen latest tags | Source review of blob-less clones from each app's last rechecked tag, covering pull requests #13 to #16 and the November 5 releases (see the [source ledger](source-ledger.md)): every catalog launch accepted unchanged, every smoke tool present without a required parameter, no tool removed or renamed, no root flag for CADCraft, FilmCraft, GridCraft or LightCraft. |
| Offline gates | Locally on Python 3.11.18: `make check` (76 entries), **284 tests**, build and verify-build passed on the updated cards, ledger and changelog. |

**Not run:** the pins of these tags land through the release workflow, the only
identity that can sign them, so until its next run the cards describe releases
slightly newer than `config/releases.json`. None of the new binaries has run on a
developer machine, and an upstream release published before that run needs its own
recheck.

## MaterialCraft and TextureCraft in the catalog — November 5, 2026

| Gate | Result |
|---|---|
| Source review | MaterialCraft v0.1.2 and TextureCraft v0.3.2 on blob-less clones (see the [source ledger](source-ledger.md)); launches, confinement, smoke tools, the MaterialCraft child process and packaging scripts read, nothing built or run. |
| `setup --app materialcraft --app texturecraft --dry-run` | Resolves both pinned macOS CLI zips, `~/.local/opt/craft/bin/`, a probe and a Claude Code registration, with `sigstore_bundle: false`. Nothing was downloaded or registered. |
| Offline gates | Listed with the pin recheck of this date; the catalog tests assert both launches exactly. |

**Not run:** neither binary has executed anywhere. The next release-workflow run
signs their six archives and its three `verify` jobs make their first execution;
the local `preflight` and `probe` AGENTS.md asks of a launch change, and the two
native scenarios, remain the operator's.

## Pin move to the 1.5.8 releases and card recheck — October 29, 2026

| Gate | Result |
|---|---|
| `workflow_dispatch` run 40945242370 on `6b61878` | All jobs passed: `refresh` found new releases of all thirteen apps and signed all 39 archives, the three with a completion named like the CLI included (one Rekor `409 createLogEntryConflict`, on the DesignCraft macOS CLI, cleared by the retry), `publish` opened pull request #12, the three `verify` jobs ran `scripts/build.py check`, `scripts/check_bundles.py` and the real strict `setup --all --acknowledge-unconfined` with each app's smoke tool on `ubuntu-latest`, `windows-latest` and `macos-latest`, and `merge` squash-merged #12 as `bb3fe62` and published release v1.5.8 from its changelog section. CI on the push of `6b61878` (run 40945219011) passed all seven jobs. |
| Card recheck at the thirteen new tags | Source review of blob-less clones from each app's last rechecked tag, covering the moves of pull requests #10, #11 and #12 (see the [source ledger](source-ledger.md)): every catalog launch accepted unchanged, every smoke tool present without a required parameter, no tool removed or renamed, no root flag for CADCraft, FilmCraft, GridCraft or LightCraft. Every card gained what its new tag adds; DesignCraft and SoundCraft drop "each flag is given once", SoundCraft its ignored unknown flags, FilmCraft its "unauthenticated" control port, FigCraft "no rollback of the clipboard" (`session/exec.rs` restores it, although upstream `docs/mcp.md` still says otherwise), and PhotoCraft corrects a claim older than this range: `command_run` refuses `file.saveACopy`, `file.automate.batch` and every other `file.*` command outside a short in-document list. Locally on Python 3.11.18: `make check` (76 entries), **284 tests**, build and verify-build passed on the updated cards, ledger and changelog. |

None of the thirteen new binaries has run on a developer machine; the cards
are source-grounded, and the runner-side evidence is the three `verify` jobs
of run 40945242370. That run covers the item "the fixed signing step … and the
three-OS `verify` of the new pins" in the section below; the new failure
annotation has not fired yet, because nothing failed. Since PhotoCraft 0.16.0
a non-empty `PHOTOCRAFT_CONTROL_PORT` in the environment a host gives the
server stops the confined launch (exit 2); the card says so, but `setup` and
`doctor` do not check for it.

## Release workflow stopped in signing, October 26 to 29 — October 29, 2026

| Run or gate | Result |
|---|---|
| Scheduled runs 40314102671, 40490635202, 40680082986 (October 26 to 28) and 40866816860 (October 29) | Each failed in `refresh` at `scripts/sign_releases.py` with "archive must contain exactly one `<app>-cli`": PhotoCraft 0.16.0's Linux tarball on the first three, CADCraft 0.14.0's on the fourth, after the refresh had found new releases of all thirteen apps. The signature store was left unchanged; `publish`, `verify` and `merge` were skipped, so no pull request, pin move or release followed. |
| Upstream archive layout | Read without executing anything (ZIP central directories over HTTP range requests, tarballs streamed) for the 39 latest archives and the 39 pinned ones. Every CLI sits at `<top>/<app>-cli` (macOS ZIP, PdfCraft's standalone tarball), `<top>/<app>-cli.exe` (Windows portable ZIP) or `<top>/bin/<app>-cli` (Linux tarball). The CADCraft 0.14.0, PhotoCraft 0.17.0 and SoundCraft 0.14.0 tarballs add `<top>/share/bash-completion/completions/<app>-cli` (0644, 14 to 18 KB). Under the new rule each of the 78 archives yields exactly one CLI, and each pinned one the member the old rule took; `extract_cli` took the 59 MB `bin/cadcraft-cli` out of the real CADCraft 0.14.0 tarball. |
| Fix and gates | Locally on Python 3.11.18: `make check` (76 entries), **284 tests** (3 new: a completion named like the CLI is ignored in tarballs and ZIPs, the accepted CLI locations, and a signing rotation over such a tarball; the duplicate test adds a second `bin/` candidate; the new tests fail without the fix), build and verify-build passed. `.github/workflows/releases.yml` parses (Ruby YAML). |

Not run: the fixed signing step and the new failure annotation on a runner,
and the three-OS `verify` of the new pins with each app's smoke tool. Both
come with the first workflow run after this change reaches `main`; each moved
card then needs its recheck at the new tag.

## Executed for 1.5.5 — October 23, 2026

macOS (Darwin 27, arm64) with Python **3.11.17** (`.venv`), plus GitHub:

| Gate | Result |
|---|---|
| `make release` | 74 check entries, **270 tests** (the 4 refresh-retry tests added on October 21; none new since), build, verify-build and reproducible 1.5.5 plugin and source ZIPs. |
| `make test-sdk` | The 7 synthetic-fixture checks passed with `mcp` 2.3.0 from the hash-locked `.venv`. |
| `make host-validate` (Claude Code 2.1.282) | `claude plugin validate --strict` passed for the 1.5.5 manifests. |
| Scheduled runs 39583945102 (October 21) and 39762354104 (October 22) | Both passed on `main`. The first found no upstream change (`publish` and `merge` skipped; the three `verify` jobs ran the real strict `setup --all`). The second found new releases of eight apps, signed their 24 archives, opened pull request #9, ran the three-OS verify with each app's smoke tool and squash-merged it as `9e54271`. |

Still not run: the card recheck of the eight apps pull request #9 moved
(DesignCraft 0.11.0, EffectCraft 0.14.0, FigCraft 0.9.0, GridCraft 0.10.0,
LightCraft 0.11.0, PdfCraft 0.11.0, PhotoCraft 0.12.0, SoundCraft 0.11.0; see
the source ledger), the retry path against a real GitHub fault, and the earlier
items listed for 1.5.4.

## Card recheck at the pull request #9 pins — October 23, 2026

| Gate | Result |
|---|---|
| Card recheck at the eight new tags | Source review of blob-less clones (see the [source ledger](source-ledger.md)): every catalog launch accepted unchanged, every smoke tool present without a required parameter, no tool removed or renamed, no root flag appeared for GridCraft or LightCraft, every release carries the three manifest assets at the manifest's byte sizes plus `SHA256SUMS.txt`. EffectCraft, GridCraft and SoundCraft changed only in version and CI (cards: date only); DesignCraft, FigCraft, LightCraft, PdfCraft and PhotoCraft cards gained the behaviour their new tags add. Locally on Python 3.11.17: `make check`, **281 tests**, build and verify-build passed on the updated cards, ledger and changelog. |

None of the eight new binaries has run on a developer machine; the cards are
source-grounded, and the runner-side evidence is the three `verify` jobs of run
39762354104. The 1.5.5 item above, "the card recheck of the eight apps pull
request #9 moved", is now covered. All eight repositories have already tagged
newer versions (see the ledger), so the next daily run moves these pins again
and the recheck repeats.

## Automated patch release after a pin move — October 23, 2026

| Gate | Result |
|---|---|
| `scripts/bump_release.py`, the refresh report's `moves`, the workflow's bump and release steps, `ci.yml` | Locally on Python 3.11.17: `make check` (the two new files registered in `packaging/files.json`), **281 tests** (11 new: patch bump and malformed versions; pin lines by display name with an accepted re-publication named; the changelog with, without and with an empty Unreleased section; singular wording; every refusal leaves both files unchanged; the workflow bumps after the refresh and before the build, hands `packaging/project.json` and `CHANGELOG.md` to publish, and only the merge job, without Python or a checkout, runs `gh release create` after `--match-head-commit`; `ci.yml` ignores the two files), build and verify-build passed. Both workflows parse (Ruby YAML). |
| Repository side | `gh api` on 2026-10-23: no rulesets, no branch protection on `main`, no tag protection, Actions allowed to create pull requests; the merge job's `contents: write` token can create the tag and the release. |
| CI, push of `4f830fb` (run 39930750334) | Ubuntu, macOS and `sdk-contract` passed; both Windows jobs failed in five of the new `tests/test_bump_release.py` tests with `UnicodeDecodeError` on byte `0x97`. The tests wrote and read their changelog fixtures in the platform's default encoding, cp1252 on Windows, where the em dash of a section heading is `0x97`, while `scripts/bump_release.py` reads and writes UTF-8 throughout. The 19 file calls in the test module now name UTF-8; locally the module passes with `-X warn_default_encoding -W error::EncodingWarning`, so no call in it or in the script falls back to the platform encoding, and `make check`, **281 tests**, build and verify-build passed. The script and the release workflow, whose tests run on Ubuntu only, were not affected. |

Not run: the new steps on a runner. The next pin move is the first, and 1.5.6
is the release it publishes; its `verify` jobs run the rebuilt plugin as before.

## Executed for 1.5.4 — October 19, 2026

macOS (Darwin 27, arm64) with Python **3.11.17** (`.venv`), plus GitHub:

| Gate | Result |
|---|---|
| `make release` | 74 check entries, **266 tests** (6 new: the signing and download retries with a fake cosign that replays the 2026-10-18 Rekor `409`, and the four newly rooted apps' minimum releases), build, verify-build and reproducible 1.5.4 plugin and source ZIPs. |
| `make test-sdk` | The 7 synthetic-fixture checks passed with `mcp` 2.3.0 from the hash-locked `.venv`. |
| `make host-validate` (Claude Code 2.1.282) | `claude plugin validate --strict` passed for the 1.5.4 manifests. |
| CI, pushes of `e1e0781` (run 39167459727) and `13c38e0` (run 39170003488) | All seven jobs passed on each: `core` on macOS, Windows and Ubuntu with Python 3.11 and 3.13, and `sdk-contract`. |
| Release workflow and native acceptance | See the two sections below: the fixed run 39167465003 and its pin moves, and the local acceptance of the four newly rooted apps. |

Still not run: the new root launches on Linux and Windows (the release
workflow's next `verify` jobs run them), write denials for DeckCraft,
DesignCraft and FigCraft, and the earlier items listed for 1.5.3.

## Pin move to the 2026-10-21 releases and card recheck — October 21, 2026

| Gate | Result |
|---|---|
| `workflow_dispatch` run 39574679446 on `656515b` | All jobs passed: `refresh` found new releases of all thirteen apps and signed all 39 archives (no retry was needed; the refresh and signing reports and the changed files appeared on the run's summary page), `publish` opened pull request #8, the three `verify` jobs ran `scripts/build.py check`, `scripts/check_bundles.py` and the real strict `setup --all --acknowledge-unconfined` with each app's smoke tool on `ubuntu-latest`, `windows-latest` and `macos-latest`, and `merge` squash-merged #8 as `658e26f`. |
| Card recheck at the thirteen new tags | Source review of blob-less clones (see the [source ledger](source-ledger.md)): every catalog launch accepted unchanged, every smoke tool present without a required parameter, no tool removed or renamed. Locally on Python 3.11.17: `make check`, **270 tests**, build and verify-build passed on the updated cards, ledger and changelog. |

None of the thirteen new binaries has run on a developer machine; the cards
are source-grounded. The 1.5.4 item above, "the new root launches on Linux
and Windows", is now covered: the `verify` jobs of runs 39241323534,
39406281597 and 39574679446 ran the rooted launches of DeckCraft,
DesignCraft, FigCraft and PdfCraft on all three runners.

## Release workflow hardening after 1.5.4 — October 21, 2026

| Gate | Result |
|---|---|
| Scheduled runs since 1.5.4 | Runs 39241323534 (October 19) and 39406281597 (October 20) passed on `ff5f146`: no upstream change, `publish` skipped, the three `verify` jobs ran the real strict `setup --all` in one to three minutes each. The cron is 05:23 UTC; GitHub started both runs between 10:12 and 10:58 UTC. |
| Shared retry policy in `storytold_tools/releases.py`, refresh retries, workflow summary and change detection | Locally on Python 3.11.17: `make check`, **270 tests** (4 new: the refresh's metadata requests retry a 503, a 429 and dropped connections; a 404 and an oversized answer are final; the third failure propagates; the download test adds a final 404 and a retried 503), build and verify-build passed. `.github/workflows/releases.yml` parses (Ruby YAML). |
| `scripts/refresh_releases.py` against GitHub (dry run; the manifest was restored, pins are the workflow's to commit) | Exit 0 through the new retrying `get`. It found newer releases for all thirteen apps, none refused by the guard: CADCraft 0.10.0, DeckCraft 0.9.0, DesignCraft 0.10.0, EffectCraft 0.13.0, FigCraft 0.8.0, FilmCraft 0.10.0, GridCraft 0.9.0, LightCraft 0.10.0, PdfCraft 0.10.1, PhotoCraft 0.11.1, SoundCraft 0.10.0, VectorCraft 0.14.0, WordCraft 0.9.0. The next workflow run pins, signs and verifies them; each card then needs rechecking at its new tag. |

Not run: the retry path against a real GitHub fault, and the changed workflow
steps on a runner (the next daily run is the first).

## Release workflow runs after 1.5.3 — October 18, 2026

| Run or gate | Result |
|---|---|
| Scheduled run 39116490412 | Failed in `refresh`: all thirteen apps had new releases, and signing the third of the 39 archives (`cadcraft-cli.exe`) got Rekor `409 createLogEntryConflict`. Rekor had committed the entry (log index 3309717814, 09:44:48 UTC) without answering in time, and cosign's own HTTP retry resent it. The signature store was left unchanged and nothing was published. |
| `e1e0781`, retries in `scripts/sign_releases.py` | Locally on Python 3.11.17 (`.venv`): `make check`, **265 tests**, build and verify-build passed; `tests.test_sign` also on Python 3.13. CI on the push (run 39167459727) passed all seven jobs. |
| `workflow_dispatch` run 39167465003 on `e1e0781` | All jobs passed: `refresh` signed all 39 archives (no retry was needed), `publish` opened pull request #7, the three `verify` jobs ran `scripts/build.py check`, `scripts/check_bundles.py` and the real strict `setup --all --acknowledge-unconfined` with each app's smoke tool on `ubuntu-latest`, `windows-latest` and `macos-latest`, and `merge` squash-merged #7 as `37889e2`. As before, the merge created no CI run. |

The thirteen cards were rechecked at the new tags (see the
[source ledger](source-ledger.md)). None of the thirteen new binaries has run
on a developer machine, and the retry path has run only in the unit tests.

### DeckCraft, DesignCraft, FigCraft and PdfCraft confined with their root flags — October 18, 2026

The reviewed catalog change launches DeckCraft, DesignCraft and FigCraft with
`--automation-read-root` (the workspace) and `--automation-write-root`
(`outputs/`), and PdfCraft with the same two in addition to `--root` (the
workspace). Same machine as 1.5.3 (macOS, Darwin 27, arm64), with the
operator's approval for each step:

| Step | Result |
|---|---|
| `setup --app deckcraft --app designcraft --app pdfcraft --upgrade --replace` | Replaced the installed DeckCraft 0.5.0, DesignCraft 0.6.0 and PdfCraft 0.7.1 with the pinned 0.8.0, 0.9.0 and 0.9.0 (`deckcraft-cli-0.8.0-macos-universal.zip` 72,514,092 bytes, `designcraft-cli-0.9.0-…` 71,114,625, `pdfcraft-cli-0.9.0-…` 61,512,027; archive hashes matched the manifest and upstream sums; notarized `DJ6XS33FX8`; Sigstore bundles verified with cosign). Each staged candidate and then each installed binary was probed with the root launch (official SDK 2.3.0, protocol `2025-06-18`): DeckCraft 25 tools with `list_commands`, DesignCraft 26 with `inspect_document`, PdfCraft 17 compact tools with `doc_inspect`, each answering `isError: false`. In Codex and Claude Code the previous user-scope entry was removed and the root launch registered. |
| `setup --app figcraft` | First install on this Mac: `figcraft-cli-0.7.0-macos-universal.zip` (78,314,177 bytes, same checks), probed staged and installed (18 tools, `inspect_document` answered), registered in Codex and Claude Code with the root launch. |
| `preflight` for the four apps | Passes without `--acknowledge-unconfined`; the launches resolve to the pinned versions with `--automation-read-root ~/craft-work-storytold --automation-write-root ~/craft-work-storytold/outputs` (PdfCraft adding `--root ~/craft-work-storytold --compact`). |
| Root denial, an SDK script asking each server to open `/etc/hosts` | Each server announced its roots on stderr (`files confined: read root ~/craft-work-storytold, write root ~/craft-work-storytold/outputs`; FigCraft `file access confined to {"read": [workspace, outputs], "write": [outputs]}`). `open_presentation`, `open_document` and FigCraft's `open_file` answered `isError: true` with `automation path rejected: … outside the read root`; PdfCraft's `doc_open` was refused by `--root` first (`is outside the allowed directory`). |
| PdfCraft write root | A blank `doc_create` document saved into `inputs/` (inside `--root`) was refused with `automation path rejected: outside the write root ~/craft-work-storytold/outputs` and nothing was written; the same save into `outputs/` wrote 566 bytes, and that test file was removed. |

Not run: write denials for DeckCraft, DesignCraft and FigCraft, and these
launches on Linux and Windows, which the release workflow's `verify` jobs run
on their next run from `main`.

## Executed for 1.5.3 — October 17, 2026

macOS (Darwin 27, arm64) with Python **3.11.17** (`.venv`), plus GitHub:

| Gate | Result |
|---|---|
| `make release` | 74 check entries, **260 tests** (22 new for the operator-command changes: removal across hosts and scopes, the run lock in and across processes and through a fake `msvcrt`, dry-run predictions against the real run, host-file contents kept out of reports), build, verify-build and reproducible 1.5.3 plugin and source ZIPs. |
| `make test-sdk` | The 7 synthetic-fixture checks passed with `mcp` 2.3.0 from the hash-locked `.venv`. |
| `make host-validate` (Claude Code 2.1.282) | `claude plugin validate --strict` passed for the 1.5.3 manifests. |
| CI, push of `f259629` (run 39015290289) | All seven jobs passed for the first-pass operator changes: `core` on macOS, Windows and Ubuntu with Python 3.11 and 3.13, and `sdk-contract`. The Windows `core` jobs were the first to run the new run lock through the real `msvcrt`. |
| ECC review of `f259629` | The Python, silent-failure, security and test-coverage reviewers each reproduced their findings with the test fakes; every confirmed finding is fixed in 1.5.3 and covered by a test (see the changelog). |
| Host-file shape on this Mac | Only key names of the Craft entries were read: Claude Code user scope writes `type`, `command`, `args`, `env`; `codex mcp add` writes `command`, `args`. One older Codex entry (PhotoCraft) also carries a `cwd` from the manual `configure` path, so `--remove` keeps it as not Storytold's. No removal ran here. |

Still not run: `setup --remove` against the real host CLIs (the new rules are
exercised only through the fakes), the Windows lock under real contention, and
the earlier items listed for 1.5.2.

## Executed for 1.5.2 — October 16, 2026

macOS (Darwin 27, arm64) with Python **3.11.17** (`.venv`), plus GitHub:

| Gate | Result |
|---|---|
| `make release` | 74 check entries (new: release signers pinned to this repository, the probe SDK lock, parseable workflow `run:` values), **238 tests**, build, verify-build and reproducible 1.5.2 plugin and source ZIPs. |
| `make setup-probe`, `make test-sdk` | The `.venv` was reinstalled from `requirements-probe.lock` with `--isolated --require-hashes --only-binary=:all:`; the 7 synthetic-fixture SDK checks passed on it, and on a fresh scratch venv installed the same way. |
| `make host-validate` (Claude Code 2.1.282) | `claude plugin validate --strict` passed for the 1.5.2 manifests. |
| CI, push of `cd20f67` (run 38932460443) | All seven jobs passed, including the hash-locked SDK install on `ubuntu-latest`. The previous push (`0b97a1f`, run 38931864760) had failed in 0 s because `ci.yml` did not parse; that is the bug this release fixes. |
| Release workflow, `workflow_dispatch` (run 38932488545) | First run of the split layout: `refresh` (only `contents: read` and `id-token: write`) found VectorCraft v0.12.0, `publish` committed the hand-over and opened pull request #6, the three `verify` jobs checked out that exact commit, ran `scripts/build.py check` and the real strict `setup --all --acknowledge-unconfined`, and `merge` squash-merged it with `--match-head-commit` (`b7e243f`). No CI `pull_request` run was created for #6, so it shows no failing check. |

Still not run: the Windows install of the probe SDK lock (Windows wheels are
hashed, only CI's Linux and this Mac installed it), a refresh that hits the
new downgrade/re-publish guard, and SoundCraft's root denial (M3).

## Release workflow runs after 1.5.1 — October 15 and 16, 2026

The scheduled run 38717981671 moved seven pins (CADCraft 0.7.0, EffectCraft
0.10.0, FilmCraft 0.8.0, GridCraft 0.7.0, LightCraft 0.8.0, PhotoCraft 0.9.0,
SoundCraft 0.7.0), signed their archives, passed its `verify` jobs on
`ubuntu-latest`, `windows-latest` and `macos-latest` (the real
`setup --all --acknowledge-unconfined` with each app's smoke tool) and merged
pull request #4 as `f49ce1e`. Run 38883983466 changed only the review date and
merged #5 as `5fc911a`. The seven cards were rechecked at the new tags (see the
[source ledger](source-ledger.md)). None of the seven new binaries has run on a
developer machine, except SoundCraft below.

### SoundCraft confined with its root flags — October 16, 2026

The reviewed catalog change launches SoundCraft with `--automation-read-root`
and `--automation-write-root`. Same machine as 1.5.0 (macOS, Darwin 27, arm64).
The binary installed there was 0.6.1, which ignores the flags, so the local
acceptance ran through the documented upgrade:

| Step | Result |
|---|---|
| `preflight --app soundcraft` before the upgrade | Refused: the pinned binary (0.6.1) predates its root flags; nothing executed. |
| `setup --app soundcraft --upgrade --replace` | Downloaded `soundcraft-cli-0.7.0-macos-universal.zip` (6,733,366 bytes; archive hash matched the manifest and upstream sums; notarized `DJ6XS33FX8`; Sigstore bundle verified with cosign), probed the staged candidate with `mcp --automation-read-root ~/craft-work-storytold --automation-write-root ~/craft-work-storytold/outputs` (official SDK 2.3.0: protocol `2025-06-18`, server `soundcraft` 0.7.0, 17 tools, `inspect_session` answered with `isError: false`), promoted it over 0.6.1, probed it again at the installed path with the same result, and in both Codex and Claude Code removed the previous user-scope entry and registered the root-flag launch. Lock pinned to v0.7.0 (`3a28a657…`). |
| `preflight --app soundcraft` and `setup --list` afterwards | Preflight passes with the root arguments; `setup --list` reports SoundCraft pinned to the manifest commit, hash matching, registered with both hosts. |

Not done: no path outside a root was tried (denial is an M3 test), plug-in
loading and the open session are outside the roots by design, and host
sessions opened before the re-registration keep the old launch until
restarted. The probe evidence stays outside the repository.

## Executed for 1.5.0 and 1.5.1 — October 14, 2026

Same machine and gates as 1.4.1 (`make release`, `make test-sdk`,
`make host-validate`; the counts in the table below are from this run). The
reviewed catalog change confines WordCraft with `--automation-read-root` and
`--automation-write-root`, so the local binary acceptance that a flag change
requires ran on this Mac:

| Step | Result |
|---|---|
| `preflight --app wordcraft` | Launch resolved to the pinned `wordcraft-cli` 0.6.1 (notarized `DJ6XS33FX8`, Sigstore) with `mcp --automation-read-root ~/craft-work-storytold --automation-write-root ~/craft-work-storytold/outputs`; no `--acknowledge-unconfined` needed any more. |
| `probe --app wordcraft --confirm-execution` with the approved `inspect_document` call | The binary announced `files confined: read root …, write root …` on stderr, negotiated protocol `2025-06-18` as server `wordcraft` 0.6.1, listed 16 tools and answered `inspect_document` with `isError: false`; the evidence file was written outside the workspace and is not committed. |

The operator then ran the documented upgrade on the same Mac:

| Step | Result |
|---|---|
| `setup --app wordcraft --upgrade --replace` | Downloaded `wordcraft-cli-0.7.0-macos-universal.zip` (archive hash matched the manifest and upstream sums; notarized `DJ6XS33FX8`; Sigstore bundle verified with cosign), probed the staged candidate with the new arguments (protocol `2025-06-18`, server `wordcraft` 0.7.0, 16 tools, `inspect_document` answered), promoted it over 0.6.1, probed it again at the installed path, and in both Codex and Claude Code removed the previous user-scope entry and registered the root-flag launch; the previous entry would have been restored had the new one failed. Lock pinned to v0.7.0 (`fc419188…`); `setup --list` reports it installed, owned, pinned to the manifest commit and registered with both hosts. |

The release workflow's run 38588658915, triggered by hand after the push, then
ran `setup --all --acknowledge-unconfined` with the new WordCraft launch on
`ubuntu-latest`, `windows-latest` and `macos-latest`: WordCraft 0.7.0 was
installed, probed and pinned with the root arguments on all three, PdfCraft
0.8.0 came from its new standalone Linux CLI tarball, and the run merged pull
request #3 (`6fee7db`: DeckCraft 0.7.0, PdfCraft 0.8.0, VectorCraft 0.11.0;
cards rechecked, see the [source ledger](source-ledger.md)). Still not done:
no path outside a root was tried (denial is an M3 test), and host sessions
opened before the re-registration keep the old launch until restarted.

## Executed for 1.4.0 and 1.4.1 — October 14, 2026

macOS (Darwin 27, arm64) with Python **3.11.17** (`.venv`):

| Gate | Result |
|---|---|
| `make check` | Passed **71 check entries**: parsed 46 files (33 Python, 12 JSON, one TOML), checked 167 local Markdown links in source, translations and plugin, validated the thirteen-app catalog with its exact launch flags, the three-platform release manifest (now pinning FigCraft v0.5.1), the signature store, the release workflow rules and 15 native scenario definitions without executing any. |
| `make test` | **223 tests** passed in an isolated source copy, zero failures, errors or skips; the catalog, CLI, status, manifest, signature-rotation and strict-provenance tests now assert thirteen apps and 39 pinned archives. |
| `make build`, `make verify-build` | The generated plugin (51 files) matches its 91 allowlisted canonical inputs, including the new FigCraft card. |
| `make package`, `make source` | Reproducible 1.4.0 plugin and source ZIPs with SHA-256 files. |
| `make test-sdk` with `mcp==2.3.0` | Passed the same 7 checks against the synthetic stdio fixture as before; no Craft binary involved. |
| `make host-validate` (Claude Code 2.1.282) | `claude plugin validate --strict` passed for the 1.4.0 marketplace and plugin manifests. |
| `doctor`, `apps`, `setup --app figcraft --dry-run` | The read-only commands list thirteen apps; FigCraft reports `not_installed` with the `--acknowledge-unconfined` setup command, and the dry run names the macOS CLI zip, the install path and both host registrations, with `sigstore_bundle: false`. Nothing was downloaded or registered by these commands. |
| FigCraft release inspection | `figcraft-cli-0.5.1-macos-universal.zip`, `figcraft-0.5.1-linux-x86_64.tar.gz` and `figcraft-0.5.1-windows-x64-portable.zip` were downloaded into a scratch directory and matched both the manifest and the release's `SHA256SUMS.txt`; each archive lists exactly one `figcraft-cli` (`bin/figcraft-cli` in the tarball, `figcraft-cli.exe` in the portable ZIP, a 159 MB universal x86_64/arm64 binary on macOS). `codesign` and `spctl` report the macOS CLI as *Notarized Developer ID*, team `DJ6XS33FX8`. The binary was not executed; no `setup`, probe or host registration ran for FigCraft. |
| Upstream source review | FigCraft `main`: CLI parser (`mcp [--attach PORT]`, the global `--no-system-fonts`, no file-root flag), MCP documentation and tool definitions (18 tools; `inspect_document` has only optional parameters), packaging and release assets; see the [source ledger](source-ledger.md). |

Not run locally for 1.4.0 and 1.4.1: the host installs from the local marketplace and
any native `setup`, upgrade or removal on this Mac; the 1.3.2 results below
still describe the twelve binaries installed here, which 1.4.0 does not touch.

### Release workflow run after the 1.4.0 push — October 14, 2026

The daily release workflow was triggered by hand after the push (run
38583930461). Its refresh job moved eight pins to the releases upstream had
published since the last refresh (DeckCraft v0.6.1, DesignCraft v0.8.0,
EffectCraft v0.9.2, FigCraft v0.6.0, FilmCraft v0.7.2, LightCraft v0.7.1,
PhotoCraft v0.8.2, WordCraft v0.7.0), signed every archive without a bundle
keyless with cosign (39 bundles for thirteen apps), rebuilt the plugin, ran
`check` and `test`, and opened pull request #2. `scripts/check_bundles.py`
then confirmed 39 bundles on each runner, and the real
`setup --all --acknowledge-unconfined` passed on `ubuntu-latest`,
`windows-latest` and `macos-latest` with strict provenance: every archive
hash-checked against the manifest and upstream sums, cosign verification of
the bundle on all three (plus Apple notarization, team `DJ6XS33FX8`, on
macOS), staged probe (initialize, `tools/list`, read-only smoke tool), atomic
promotion and a second probe at the installed path. For FigCraft that was its
first execution anywhere: `figcraft-cli` 0.6.0 answered `inspect_document`
on all three runners (lock labels `sigstore` on Linux and Windows,
`notarized DJ6XS33FX8, sigstore` on macOS). The merge job squash-merged the
pull request into `main` as `88a97c6`; `make verify-build` and `make check`
pass on that commit. No host CLI exists on the runners, so registration is
still covered by simulated tests only, and no FigCraft binary has run on a
developer machine. The eight moved apps' smoke tools were exercised by that
run, and their cards were rechecked against the new tags on 2026-10-14 (see
the [source ledger](source-ledger.md)).

## Executed for 1.3.2 — October 12, 2026

macOS (Darwin 27, arm64) with Python **3.11.17**:

| Gate | Result |
|---|---|
| `make check` | Passed **71 check entries**: parsed 46 files (33 Python, 12 JSON, one TOML), checked 153 local Markdown links in source, translations and plugin, validated the three-platform release manifest, the signature store, the release workflow rules (including that the verify matrix checks bundle completeness before a strict `setup` without `--trust-upstream-sums`) and 14 native scenario definitions without executing any. |
| `make test` | **223 tests** passed in an isolated source copy, including the staged `setup`/upgrade flow, fault-injected promotion recovery (failure before promotion, during the file replace, while writing the lock, while clearing the marker; `completable`, `reverted`, `ambiguous` and `corrupt` reconciliation), whole-registration ownership on removal, recoverable `--replace` with restore and restore-failure, candidate-versus-active evidence identity, and the ownership-checked removal on simulated macOS, Linux and Windows with injected network, notarization, cosign and host CLIs, signature-store rotation with a fake signer, manifest rules and `doctor` scopes; zero failures, errors or skips. |
| `make build`, `make verify-build` | The generated plugin (50 files) matches its 90 allowlisted canonical inputs. |
| `make package`, `make source` | Reproducible plugin and source ZIPs with SHA-256 files. |
| `make test-sdk` with `mcp==2.3.0` | Passed 7 checks against the synthetic stdio fixture: initialize, two-page `tools/list`, wire aliases, typed structured content, `isError`, SDK context exit, and a native tool error not reported as success. |
| `claude plugin validate --strict` (Claude Code 2.1.282) | 1.3.2 marketplace and plugin manifests: no errors or warnings. |
| Claude Code install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `claude plugin details` lists one Skill (`craft`) and zero MCP servers. |
| Codex CLI 0.162.0-alpha.17.2 install from the local marketplace | `storytold@devsolux-storytold` 1.0.0 installed and enabled; `codex debug prompt-input` lists the `storytold:craft` Skill. |
| Portable manifests | `plugin.json` and `config/portable.mcp.example.json` validate against the published Agent Plugins 1.0.0 schemas. |
| External links | Every README, app catalog and source ledger URL resolved, except the repository itself before publication. The 15 release-pinned upstream links in the app cards exist at their tags. |
| Upstream release review | All twelve cards and catalog launch flags rechecked against each app's latest release tag; see the [source ledger](source-ledger.md). Source review only, not binary execution. |

Host installs used throwaway `CLAUDE_CONFIG_DIR` and `CODEX_HOME` directories, so
no real host configuration was changed. The two install rows ran for 1.0.0;
1.0.1 through 1.2.0 change Skill text, docs and helper commands, not manifest structure. Installation from GitHub reads the same
committed marketplace files and `plugins/storytold/` runtime.

## 1.3.0 and 1.3.1 behavior changes: offline evidence only

The staged upgrade (probe before promotion), the recovery marker outside
staging and its five reconciliation states, the whole-registration ownership
checks in `setup --remove`, the read-only `--remove --dry-run`, the
restore-on-failure `--replace`, the separate candidate and active probe
evidence, the Claude registration parsing and the signature-store rotation
were verified by the offline suite above with injected network, signing and
host CLIs and with fault injection at the binary replace, lock write, marker
cleanup and host add/remove boundaries. The strict verify matrix (bundle
completeness, then `setup` without `--trust-upstream-sums`) is enforced by
`make check` and a test on the workflow text; it has not yet run on GitHub
for 1.3.1. No live `setup`, upgrade, removal, signing run or
host-configuration change was executed for 1.3.0, 1.3.1 or 1.3.2; the native
evidence below predates them and still describes the installed binaries,
which none of these releases touches. The 1.3.1 lifecycle suite failed on
the Windows CI runners only (evidence archive name collision, fixed in
1.3.2); the macOS and Linux runners passed.

## Native app evidence — the first twelve apps via `setup`

Operator-run on macOS (Darwin 27, arm64) with the one-command path:
`python3 storytold.py setup --all --acknowledge-unconfined`, resumed twice after
fixes found during the run (the probe did not forward the acknowledgement for
unconfined apps; DeckCraft's headless session has no presentation open, so its
smoke tool became `list_commands`). Final state, confirmed by `codex mcp list`,
`claude mcp list` (every server health-checked as connected), `doctor` and
`setup --list`:

| App | Release | Probe (initialize, tools/list, read-only call) | Tools | Registered |
|---|---|---|---|---|
| PhotoCraft | v0.7.0 | passed (`doc_inspect`) | 21 | codex, claude |
| VectorCraft | v0.9.0 | passed (`doc_inspect`) | 32 | codex, claude |
| FilmCraft | v0.6.0 | passed (`doc_inspect`) | 17 | codex, claude |
| LightCraft | v0.6.0 | passed (`doc_inspect`) | 17 | codex, claude |
| PdfCraft | v0.6.0 | passed (`doc_inspect`) | 17 | codex, claude |
| EffectCraft | v0.8.0 | passed (`doc_inspect`) | 27 | codex, claude |
| DesignCraft | v0.6.0 | passed (`inspect_document`) | 25 | codex, claude |
| GridCraft | v0.5.0 | passed (`inspect_workbook`) | 21 | codex, claude |
| WordCraft | v0.5.0 | passed (`inspect_document`) | 16 | codex, claude |
| DeckCraft | v0.5.0 | passed (`list_commands`) | 25 | codex, claude |
| CADCraft | v0.5.0 | passed (`inspect_drawing`) | 11 | codex, claude |
| SoundCraft | v0.5.0 | passed (`inspect_session`) | 17 | codex, claude |

Every archive matched both `config/releases.json` and the release's
`SHA256SUMS.txt`; every binary was accepted by `spctl` as *Notarized Developer
ID* with team `DJ6XS33FX8`; the probe SDK was installed into
`~/.local/state/storytold/venv` from PyPI by `setup` itself. Re-running `setup`
afterwards reports every app as already installed and already registered.

Upgrade path (1.2.0): after the manifest refresh moved VectorCraft to v0.10.0,
PdfCraft to v0.7.1 and SoundCraft to v0.6.1, `setup --app … --upgrade` replaced
the three binaries (notarization verified; no Sigstore bundle exists before the
workflow's first run), re-probed them (32, 17 and 17 tools, servers reporting
0.10.0, 0.7.1 and 0.6.1) and left both hosts' registrations unchanged;
`setup --list` reports all twelve pins equal to the manifest commits.

Fresh-user simulation: in a throwaway `CODEX_HOME`, `codex plugin marketplace
add <this checkout>` and `codex plugin add storytold@devsolux-storytold`, then
`python3 <plugin cache>/storytold.py setup --app gridcraft --host codex
--acknowledge-unconfined` registered GridCraft only in that throwaway home; the
real `~/.codex/config.toml` hash was unchanged.

Real work: during this session a host chat on this Mac exported
`outputs/our-world.png` (1920×1200 RGB) together with the editable
`our-world.pcraft` through the registered PhotoCraft server; `verify-artifact`
accepted the PNG signature and dimensions, and the image was reviewed visually.
This is an M0/M1-level result for PhotoCraft only; edit, export, root-denial,
isolation and fidelity tests (M1–M3) have not run for the other eleven apps, and
no Windows or Linux machine was used.

### Earlier manual PhotoCraft run (1.0.1)

Operator-run on macOS (Darwin 27, arm64), following [operations](operations.md):

| Step | Result |
|---|---|
| Obtain the CLI | `photocraft-cli-0.7.0-macos-universal.zip` from the v0.7.0 release matched `SHA256SUMS.txt`; `spctl` reported *Notarized Developer ID*, team `DJ6XS33FX8`, the same team as the installed `PhotoCraft.app` 0.7.0, which contains no CLI. |
| Pin | Revision `79261615956ab21334e49ca1d384390272e647da` (tag v0.7.0); binary SHA-256 `31ce1ee0…c2e42f7f2d`; `preflight` passed. |
| `probe` discovery | Official SDK 2.3.0 negotiated protocol `2025-11-25` with server `photocraft` 0.7.0 and listed 21 tools, including `doc_inspect`, `command_list`, `command_run`, `doc_render_preview`, `doc_save` and `doc_export`. |
| `probe` smoke call | `doc_inspect` with `{}` (annotated read-only) returned `isError: false` and an empty session (`document: null`). |
| `configure --host codex` | Generated `[mcp_servers.photocraft]` with absolute command, root flags and workspace `cwd`; after registration, `codex mcp get photocraft` (Codex CLI 0.162.0-alpha.17.2) lists it as enabled stdio. |

That manual run is M0-level evidence only; the `setup` run above supersedes it.

## What the offline checks exercise

The standard-library core suite uses temporary isolated source/workspace copies.
Synthetic non-executable app fixtures test binary equality and config boundaries;
SDK-shaped stubs test discovery, error, timeout and evidence logic without starting
any Craft binary. Tests cover staging, preservation, limited artifact parsing,
explicit execution approval, generated-file ownership, cleanup, reproducible
packaging, install-command identity and offline release targets. These do **not**
constitute a native handshake; `make test-sdk` covers the real SDK transport.

`make check` parses Python AST, JSON and TOML; checks local Markdown links in both
canonical source and generated plugin; checks identities, README install commands,
Makefile script references, app topology, inactive templates, source hashes, Skill
policy and acceptance definitions. CI YAML is checked for the specific
privilege/action-pinning rules used here, not full GitHub server-side validation.
Host manifest schemas remain authoritative.

## Not verified

- **Craft apps.** All fifteen CLIs passed discovery and one read-only call on one
  macOS machine; PhotoCraft, PdfCraft, MaterialCraft and TextureCraft have
  produced real exports, and the last three have run their acceptance scenarios
  (edit, save, reopen and root denial, November 13, 2026). Native edit, export,
  root-denial, isolation and fidelity tests (M1–M3) have not run for the other
  twelve apps, and the host-level M1 test has not run for any.
- **MaterialCraft and TextureCraft.** Executed on the three GitHub runners
  (runs 42034977077 and 42222471577: download, provenance, discovery and the
  `session_inspect` smoke call) and, since November 13, 2026, through
  operator-run `setup` on a developer Mac, registered with Claude Code.
  Both apps' scenarios ran there (above), including the exported-map handoff
  between them. Every acceptance gate (M1–M3) is still open for both.
- **Linux and Windows.** Real runs exist only on GitHub-hosted runners: the
  release workflow's verify matrix (run 38278727530 on 2026-10-12 with twelve
  apps, runs 38583930461 and 38588658915 on 2026-10-14 with all thirteen, the
  latter with WordCraft's confined launch, runs 38717981671 on 2026-10-15
  and 38883983466 on 2026-10-16, and runs 42034977077 on 2026-11-05 and
  42222471577 on 2026-11-06 with all fifteen) installed, probed and
  Sigstore-verified every pinned app on `ubuntu-latest`,
  `windows-latest` and `macos-latest`. No host CLI was present there, so
  registration on Linux/Windows is covered by simulated tests only, and no
  Linux or Windows desktop machine has been used.
- **Sigstore signing.** Keyless signing ran only in that workflow. Its first
  pull request merged on 2026-10-12, #2 and #3 (thirteen apps) on 2026-10-14,
  #4 on 2026-10-15, #5 on 2026-10-16 and #17, with MaterialCraft and
  TextureCraft, on 2026-11-05, so `config/signatures.json` on `main` holds 45
  bundles, and `cosign verify-blob` (cosign v3.1.3 via Homebrew) has
  since verified five of them on this Mac during `setup --upgrade` of
  GridCraft 0.6.1, WordCraft 0.6.1 and 0.7.0, CADCraft 0.6.2 and SoundCraft
  0.7.0 (lock labels
  `notarized DJ6XS33FX8, sigstore`). Apps installed before cosign was present
  carry notarization-only labels until they are next upgraded.
- **CI matrix.** GitHub Actions ran Linux/macOS/Windows × Python 3.11/3.13 and
  the SDK contract job on the 2026-10-16 push of `main` (run 38927511616, all
  seven jobs passed); not run locally. On the release workflow's own pull
  requests (#1 to #5) the offline-checks run never started a job (see
  [operations](operations.md)); since 1.5.2 CI skips pull requests that touch
  only the bot-owned release files, and the release workflow's checks gate
  them.
  Windows-specific branches (binary-mode reads, read-only publication order)
  run in that matrix and are simulated on macOS.
- **Out of scope.** Remote ChatGPT connectors, cloud execution, live GUI control
  and real customer documents.

App cards remain source-derived guidance, not a tested registry.

## Reproduce and extend

```bash
make check
make test
make build
make verify-build
make package
make source
make setup-probe
make test-sdk
make host-validate
```

`make setup-probe` is the only network step; it installs the pinned SDK into a
local `.venv`. `make test-sdk` launches only the synthetic stdio fixture. After
that, follow [operations](operations.md) and [acceptance](acceptance.md) against
your pinned native apps and target hosts. Keep synthetic SDK results separate
from real app evidence.

Source and plugin ZIPs use sorted entries, fixed timestamps and file modes.
Byte-identical archive tests apply to repeated builds using the same Python/zlib
toolchain; cross-zlib byte identity is not promised. File hashes attest bytes,
not business correctness, safe execution, provenance or legal authorization.
