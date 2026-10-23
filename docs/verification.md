# Verification status — 1.5.5

Native application and host *acceptance* (M0–M4) remain **not run**: this
repository neither ships nor executes Craft binaries. All thirteen CLIs have
passed the native probe through operator- or runner-run `setup` (tables
below), on GitHub runners and on a developer Mac (FigCraft there since
October 18, 2026). That is M0-level evidence, not
acceptance. This report separates the checks actually executed for each
release from documentary evidence.

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

- **Craft apps.** Twelve CLIs passed discovery and one read-only call on one
  macOS machine; only PhotoCraft has produced a real export. Native edit,
  export, root-denial, isolation and fidelity tests (M1–M3) have not run for the
  other eleven apps.
- **FigCraft.** Executed only on the three GitHub runners (run 38583930461:
  download, provenance, discovery and the `inspect_document` smoke call at
  v0.6.0); its card and scenario rest on source review. No developer machine
  has run it, no host has registered it, and every acceptance gate (M1–M3)
  is still open.
- **Linux and Windows.** Real runs exist only on GitHub-hosted runners: the
  release workflow's verify matrix (run 38278727530 on 2026-10-12 with twelve
  apps, runs 38583930461 and 38588658915 on 2026-10-14 with all thirteen, the
  latter with WordCraft's confined launch, and runs 38717981671 on 2026-10-15
  and 38883983466 on 2026-10-16) installed, probed and
  Sigstore-verified every pinned app on `ubuntu-latest`,
  `windows-latest` and `macos-latest`. No host CLI was present there, so
  registration on Linux/Windows is covered by simulated tests only, and no
  Linux or Windows desktop machine has been used.
- **Sigstore signing.** Keyless signing ran only in that workflow. Its first
  pull request merged on 2026-10-12, #2 and #3 (thirteen apps) on 2026-10-14,
  #4 on 2026-10-15 and #5 on 2026-10-16, so `config/signatures.json` on `main`
  holds 39 bundles, and `cosign verify-blob` (cosign v3.1.3 via Homebrew) has
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
