# Changelog

## Unreleased

- Release workflow: the 2026-10-18 daily run (39116490412) failed while
  signing `cadcraft-cli.exe`, the third of the 39 archives that 13 new
  upstream releases put up for signing. Rekor committed the entry but did not answer in
  time; cosign's own HTTP retry resent it and got `409
  createLogEntryConflict`. `scripts/sign_releases.py` now tries each signing up
  to three times (15 s, then 45 s apart), each in a fresh cosign process with
  a new ephemeral key, so the retry makes a new, distinct log entry. A hung
  cosign is stopped after 600 s and counts as a failed attempt. Each archive
  and SHA256SUMS.txt download is retried the same way on network errors; a
  size-limit refusal is final. The store is still published only when all 39
  bundles are complete.
- The release workflow's `actions/upload-artifact` and
  `actions/download-artifact` pins moved to v7.0.2 and v8.0.2 (HTTP 429
  retries); the source ledger records the reviewed commits.
- The fixed workflow run (39167465003) moved all thirteen pins (pull request
  #7: CADCraft 0.8.0, DeckCraft 0.8.0, DesignCraft 0.9.0, EffectCraft 0.11.1,
  FigCraft 0.7.0, FilmCraft 0.9.0, GridCraft 0.8.0, LightCraft 0.9.1, PdfCraft
  0.9.0, PhotoCraft 0.10.0, SoundCraft 0.8.0, VectorCraft 0.13.1, WordCraft
  0.8.0). Every card was rechecked at its new tag; every catalog launch and
  smoke tool still works, and no tool was removed or renamed. Cards now
  cover: VectorCraft's cancellation and `-32003` busy refusal (the old "may
  not support active cancellation" is gone, from the acceptance scenario
  too); WordCraft's `file.rename` and `get_text` without tracked deletions;
  PdfCraft's XFA-removing edits and what roots do not cover; LightCraft's
  writes into photo folders and background slideshow export; GridCraft's
  8,192-character formula limit; DesignCraft's `ime` tool, PowerPoint export
  and argument refusal; DeckCraft's GIF export and argument refusal;
  FigCraft's `{"$step": n}` batch references; and the stored-path rules of
  CADCraft, DesignCraft, EffectCraft, FilmCraft and SoundCraft.
- DeckCraft, DesignCraft, FigCraft and PdfCraft now ship read/write root
  flags that the catalog does not pass yet, so their cards, the safety list,
  the README legend and the `setup` messages say these apps are launched
  without root flags instead of claiming they have none. Their launches are
  unchanged; confining them is a separate reviewed catalog change.

## 1.5.3 — 2026-10-17

Operator-command hardening: `setup --remove`, concurrent runs, `--host` and
`--dry-run` now do what the operator asked, refuse what they cannot do and
say so. A second pass with the ECC Python, silent-failure, security and
test-coverage reviewers closed the gaps the first pass left (listed after the
first-pass items). No release pin moved since 1.5.2, so no card was due for a
recheck.

- `setup --remove` no longer deletes a binary that another host still
  launches. Every host gets a row; one whose CLI is not run (not on PATH, or
  left out with `--host`) has its user-scope file read, and while it still
  registers the app at the managed binary, or cannot be read, the binary, pin
  and evidence stay. Before, `--remove --host claude` deleted the binary under
  a live Codex registration, and a host CLI missing from PATH left its
  `~/.claude.json` or `config.toml` entry pointing at a deleted file, both
  reported `ok`.
- A failing `mcp remove` is reported in that host's row and the run continues
  with the other hosts and apps; before, it aborted the whole removal without
  a report after earlier hosts were already unregistered. A failed binary
  delete or pin rewrite is reported the same way.
- The pin now stays while any registration that may still launch the managed
  path is kept (for example one whose `mcp get` timed out), so a later
  `--remove` can still prove that entry is Storytold's and remove it. Before,
  the pin was dropped and that registration could never be removed by
  Storytold.
- One changing run at a time: `setup` and `setup --remove` hold an OS advisory
  lock (`setup.lock` in the state directory) for the whole run, released by
  the OS when the process ends. The `<lock>.writing` marker guarded only the
  lock rewrite, so two runs could clear each other's staging or recovery
  marker.
- An app without root flags and no `--acknowledge-unconfined` is skipped
  whatever its install path holds; an outdated pin or a foreign file there no
  longer stops the rest of the batch. The message names what the next run
  would meet.
- A host named with `--host` whose CLI is not on PATH now fails the run
  (other named hosts are still registered); before, it was a warning with
  exit status 0.
- `--dry-run` shares the real run's decision function and reports, per app,
  `binary` (`keep`, `install`, `upgrade`, `skip`, `refuse` with `reason`), a
  `download` only where one is needed, per-host `registrations` judged from
  the user-scope files, `predicted_status` and an overall `would_pass`.
  Before, it listed a download and a registration for every app, including
  ones the real run would skip or refuse. A work root that exists but is not a
  Storytold workspace is now refused before any directory is created.
- Tests: nine new regression tests; the test runner strips
  `CLAUDE_CONFIG_DIR` and `CODEX_HOME`, and the CLI tests point
  `CLAUDE_CONFIG_DIR` at a temporary directory, so no test reads the
  operator's real host settings.

Second pass (ECC review of the first):

- `setup --remove` keeps the binary and pin under a kept registration whose
  command the host CLI does not show (`claude mcp get` text without a
  `Command:` line, unparseable `codex mcp get --json`), and under one a local
  or project entry shadows in `mcp get` while the user-scope file still names
  the binary. Before deleting, it now searches both hosts' files for any
  registration that starts the binary: another server name, another spelling
  or symlink of the path, or a Claude Code local-scope entry, listed in
  `references` by host, scope and name only. An `mcp remove` that exits 0 is
  trusted only once the user-scope file no longer lists the entry.
- A registration carrying settings `mcp add` never writes (tool lists,
  timeouts, a non-stdio type) is no longer treated as Storytold's: removal
  keeps it, and `--replace` refuses it instead of losing those settings on a
  failed add.
- A failing evidence archive, or any unexpected error in one app, no longer
  ends `setup --remove` without a report: it becomes that app's row and the
  other apps still run. A real `setup` that stops at a failure lists the apps
  it never attempted as `not_reached`.
- Refused before anything is created or downloaded: a leftover
  `<lock>.writing` marker (also by `--remove`, before any binary is deleted),
  a state or evidence directory that is not owner-only, and a bin directory
  that group or others can write, which used to be found only after a
  candidate was promoted and pinned.
- `--dry-run` predicts those refusals, the Linux/Windows provenance gate (no
  bundle or no cosign without `--trust-upstream-sums`), a `--replace` that
  could not restore the old entry, and an unreadable user-scope file
  (`registration_unknown`); it exits 1 when `would_pass` is false, like
  `--remove --dry-run`. A real `setup` report without a recognized status no
  longer reads as success.
- Host files never reach a report: unparseable or too deeply nested JSON or
  TOML (a `RecursionError` used to escape as a traceback) gives a fixed
  message instead of the parser's text, which could quote keys, and only text
  commands of at most 300 characters are shown. `doctor` does the same.
- The run lock refuses a lock file that is a symlink, reparse point or not a
  regular file (Windows has no `O_NOFOLLOW`), names a filesystem without file
  locks instead of reporting "another setup run", always closes its file on
  Windows, and two first runs racing to create the state directory meet the
  lock instead of a raw `FileExistsError`.
- Docs: operations says that `claude mcp get`, used by `--remove`, its dry
  run, `--list` and registration, starts the registered server for its health
  check, as a Claude Code session does.
- Tests: thirteen more, 260 in all, including a run lock held by another
  process blocking `setup` and `--remove`, the Windows `msvcrt` branch through
  a fake module, every `unrun_host` branch, failed deletes and pin rewrites,
  recovery markers in a dry run and a Linux provenance preview; the
  killed-holder test has a watchdog and waits briefly for Windows to release
  the lock.

## 1.5.2 — 2026-10-16

SoundCraft joins the root-confined apps; card rechecks for the seven pins
moved since 1.5.1; fixes from a security, silent-failure, Python and
consistency review (release-workflow token split and merge pinning, refresh
guards, hash-locked probe SDK, setup and doctor hardening); and a CI fix that
removes the failing checks on the bot's "Refresh Craft release pins" pull
requests.

- Release workflow: the verify jobs check out the exact commit the refresh
  job pushed, and the merge job merges only that commit
  (`--match-head-commit`) of a same-repository pull request (a fork could
  name its branch `bot/releases`). A missing pull request now fails the
  merge job instead of ending green, and the pull request body no longer
  claims verify results before they exist. `make check` enforces both rules.
- `scripts/refresh_releases.py` stops instead of pinning when an app's latest
  release is older than its pin, when a pinned tag now points at another
  commit, or when an asset is re-published under an unchanged tag and name;
  it moves the `reviewed` date only with a pin, so an unchanged day opens no
  pull request (#5 was such a date-only change), and it restores the old
  manifest if the new one fails validation. New tests cover the guard.
- `make check` pins the manifest's `signers` to this repository's release
  workflow on `main` and the Apple team `DJ6XS33FX8`, so a pull request cannot
  swap the trust root together with matching signatures.
- `setup`: macOS verifiers run as `/usr/sbin/spctl` and `/usr/bin/codesign`,
  not from PATH; `promote` checks the candidate's bytes against the verified
  hash before replacing the live binary; every subprocess has a 30-minute
  timeout reported as an error; the state directory and binaries, like the
  lock and evidence, must lie outside the workspace; a Windows `.cmd` host
  shim refuses paths with characters `cmd.exe` would reinterpret and prints
  the manual command; a requested host CLI missing from PATH is warned about
  even when another host remains; an existing registration with the right
  command but extra env, cwd or another scope is reported with a warning;
  and the overall status is an allow-list of success states.
- The SoundCraft version guard accepts only ASCII `x.y.z` followed by a space,
  parenthesis or the end, so `0.7.0-rc1` and non-ASCII digits are refused;
  `setup` treats such a pin as stale even at the manifest commit, so
  `--upgrade` rewrites the label instead of looping on the refusal.
- `setup --remove` keeps the binary, pin and evidence when a registration it
  must keep still launches that binary (for example an older launch's
  arguments) and names the `mcp remove` commands, instead of leaving the host
  entry pointing at a deleted file; a registration that differs only in its
  arguments is now reported as such, not as "a different command".
- `verify-artifact --expected-sha256 ""` fails instead of skipping the digest
  check; `setup --all --app <x>` is refused instead of quietly installing only
  `<x>`; `--timeout` accepts only the probe's (0, 120] seconds before anything
  is downloaded; a non-string workspace id or receipt path is a validation
  error, not a traceback.
- Release workflow split: the job that downloads, unpacks and signs upstream
  archives and runs repository code now holds only `contents: read` and
  `id-token: write`; a separate `publish` job holds the write token, runs
  only `git` and `gh` (through `gh auth setup-git`, so no token in a URL),
  and receives the files through the pinned `actions/upload-artifact` v7.0.1
  and `actions/download-artifact` v8.0.1. The verify jobs also run
  `scripts/build.py check` on the published commit. A test keeps the split.
- `scripts/refresh_releases.py --accept <app>` lets one app through the
  downgrade/re-publish guard after a maintainer reviewed it by hand.
- The first run of the split release workflow (run 38932488545) moved
  VectorCraft to v0.12.0 and merged pull request #6 with no failing check.
  The card was rechecked at the new tag (same flags and 32 tools; new
  `query`/`brief` discovery, stroke options, `vertical` text, `ai` export) and
  corrected: the `command_batch` tool never rolls back, even with `atomic`;
  only the engine command `command.batch` puts the documents back.
- CI: the `0b97a1f` push broke `ci.yml` (an unquoted `run:` value containing
  `:all: -r` is a YAML mapping, so GitHub could not load the workflow and the
  run failed in 0 s); the value is quoted and `make check` now refuses any
  unquoted `run:` value with `": "` in either workflow. CI's `pull_request`
  trigger ignores pull requests that change only `config/releases.json`,
  `config/signatures.json` and `plugins/storytold/**`: on the bot's
  "Refresh Craft release pins" pull requests (#1 to #5) GitHub never started a
  job and the run failed when the merge deleted `bot/releases`; the release
  workflow's own check, test and three-OS verify jobs gate them.
- The probe SDK is hash-locked: `requirements-probe.lock` (uv universal
  resolution, 28 packages, every wheel's SHA-256, `pywin32` for Windows only)
  ships with the plugin, and `setup`'s probe venv, `make setup-probe` and the
  CI SDK job install only from it with `--isolated --require-hashes
  --only-binary=:all:`, so no source build runs and no `PIP_*` variable or pip
  configuration can redirect the index. `make lock-probe` regenerates it and
  `make check` refuses a pin without a hash or an `mcp` that disagrees with
  the SDK version.
- `codex`/`claude mcp get`: only the host's own "No MCP server named" answer
  means "not registered"; any other failure is an error in `register`, an
  uninspectable entry that keeps the binary in `--remove`, and
  `registration_unknown` in `setup --list`, whose `probe_evidence` now shows
  the recorded probe status instead of "a file exists".
- `doctor`: an unreadable host config makes a server `registration_unknown`
  instead of "not registered" or "not installed"; a corrupt lock is reported
  in `host_config_errors` instead of being read as empty; the printed setup
  command quotes its path and says `python` on Windows.
- `setup`: an unacknowledged unconfined app is reported
  `needs_acknowledgement` and skipped while the other selected apps are still
  processed; lock updates are serialized with a `<lock>.writing` marker so
  parallel runs cannot drop each other's pins; `--remove` archives the
  candidate and call evidence instead of deleting it; `preflight`, `probe`
  and `configure` derive the output root from `--work-root` unless
  `--output-root` or `CRAFT_OUTPUT_ROOT` is given.
- Docs: the READMEs say what the confined apps really read (the whole
  workspace) and write (`outputs/`); operations corrects the unconfined-app
  rule, adds `not_installed` to the doctor table and documents the workflow
  guarantees and the job-less CI runs on bot pull requests; verification and
  the source ledger are brought up to date; CONTRIBUTING lists
  `make test-sdk`; the plugin README names `--acknowledge-unconfined` and
  `--replace` for upgrades; `.claude/CLAUDE.md` mentions `make github-pull`.

- `config/apps.json` launches SoundCraft with `mcp --automation-read-root
  {work} --automation-write-root {outputs}` (`read_write`), the flags its CLI
  ships since 0.7.0. `ROOTED`, the inactive launch templates, the catalog
  tests (five `read_write`, seven `os_only`), `make setup-confined` (six
  apps), the card, the safety list, the READMEs, operations and acceptance
  follow; SoundCraft no longer needs `--acknowledge-unconfined`.
- SoundCraft before 0.7.0 silently ignores unknown `mcp` flags, so the new
  launch would run an older binary unconfined. `preflight`, and with it
  `setup`, `probe` and `configure`, now refuses a SoundCraft pin older than
  0.7.0 or without a readable version and names
  `setup --app soundcraft --upgrade --replace`; a new catalog test covers it.
- Existing installs: run `setup --app soundcraft --upgrade --replace`. On the
  maintainer's Mac that moved SoundCraft from 0.6.1 to 0.7.0, probed it with
  the root arguments and replaced both host registrations (see the
  verification report). Denial of an outside path was not tested.
- The scheduled run 38717981671 merged pull request #4 (CADCraft 0.7.0,
  EffectCraft 0.10.0, FilmCraft 0.8.0, GridCraft 0.7.0, LightCraft 0.8.0,
  PhotoCraft 0.9.0, SoundCraft 0.7.0), with the real `setup` passing on the
  Linux, Windows and macOS runners; run 38883983466 merged #5, which changed
  only the review date.
- The seven cards were rechecked at the new tags; no catalog launch flag or
  smoke tool changed. CADCraft's card covers `find_text`, `--lazy`/`--launch`
  and the new AutoLISP, whose file functions reach any path, so the safety
  list now names it among scripts. GridCraft's card corrects `.xls` (partial
  BIFF8 import, not refused) and lists the new save refusals. PhotoCraft's
  covers the lossy-ORA copy rule, `dpxBits` and Krita import, LightCraft's
  `rendereddng`, and SoundCraft's the root flags 0.7.0 accepts (adopted
  above) plus `bounce_mix` overwriting. EffectCraft's and
  FilmCraft's only change their recheck dates. The source ledger records it.
- AGENTS.md and `.claude/CLAUDE.md`: pull `main` first because the workflow
  merges on its own, finish every pin move with a card recheck and a ledger
  entry, treat a launch-flag change as a catalog change with local binary
  acceptance and `--upgrade --replace`, and push, tag or release only on the
  operator's request. The Skill notes that cards describe the pinned release
  and that an older installed binary's live tool list wins.

## 1.5.1 — 2026-10-14

Documentation and pin release; no code change.

- The release workflow's run 38588658915, the first whose three-runner
  `setup` used WordCraft's root-flag launch, installed, probed and pinned
  WordCraft 0.7.0 with the root arguments on Linux, Windows and macOS, moved
  DeckCraft to 0.7.0, PdfCraft to 0.8.0 (now from its standalone Linux CLI
  tarball) and VectorCraft to 0.11.0, signed their nine archives and merged
  pull request #3.
- The three moved apps' cards were rechecked at the new tags: no `mcp`
  launch flag changed. VectorCraft's card gains the unknown-parameter
  refusal, the atomic `command_batch` mode with its 256-step and 8 MiB caps,
  the rule that a failed atomic batch restores documents but not written
  files, text overflow reporting, undecodable-image notes and the
  `[Converted]` save behaviour; PdfCraft's card notes the standalone Linux
  CLI tarball; DeckCraft's is unchanged. The source ledger records the
  findings and the verification report cites the run.

## 1.5.0 — 2026-10-14

WordCraft joins the root-confined apps. One reviewed catalog change; no new
architecture.

- `config/apps.json` launches WordCraft with `mcp --automation-read-root
  {work} --automation-write-root {outputs}` (`read_write`), the flags its CLI
  has shipped since 0.6.1: every path a command opens must lie inside the
  workspace and every save, export or print inside `outputs/`; a refused path
  is an ordinary tool error, `--connect` with the flags is an error and the
  desktop app stays unconfined. `ROOTED`, the inactive launch templates, the
  catalog tests (four `read_write`, eight `os_only`), `make setup-confined`
  (five apps), the card, the safety list and the docs follow. WordCraft no
  longer needs `--acknowledge-unconfined`.
- Existing installs: the registration `setup` writes changes, so run
  `setup --app wordcraft --upgrade --replace` (or `--all --upgrade --replace`);
  without `--replace`, `setup` reports the differing registration and leaves
  it alone. README, operations and the card say so.
- Local binary acceptance for the flag change: `preflight` and the
  official-SDK `probe` ran the pinned WordCraft 0.6.1 on the maintainer's Mac
  with the new arguments (`files confined` announced, 16 tools,
  `inspect_document` answered); then `setup --app wordcraft --upgrade
  --replace` on that Mac moved the binary to 0.7.0 and replaced both host
  registrations with the root-flag launch. Denial of outside paths was not
  tested, and the three-OS verify matrix runs the new launch on the
  workflow's next run.

## 1.4.1 — 2026-10-14

Documentation and pin release; no code change.

- The daily workflow's first run with the fixed pull-request lookup (run
  38583930461) moved eight pins (DeckCraft 0.6.1, DesignCraft 0.8.0,
  EffectCraft 0.9.2, FigCraft 0.6.0, FilmCraft 0.7.2, LightCraft 0.7.1,
  PhotoCraft 0.8.2, WordCraft 0.7.0), signed all 39 archives and ran the real
  `setup` on the Linux, Windows and macOS runners; pull request #2 merged it.
  FigCraft 0.6.0 answered its `inspect_document` smoke call on all three
  runners, its first execution anywhere.
- All eight moved apps' cards were rechecked at the new tags: no `mcp` launch
  flag changed, no tool was renamed or removed, and PhotoCraft lists four new
  document tools. Cards updated for FilmCraft's `offlineMedia`, LightCraft's
  Apple Photos export hook, `onDeleted` default and `denoise-serve` listener,
  PhotoCraft's batch and mask semantics, WordCraft's property objects and the
  root flags its CLI has shipped since 0.6.1 (not yet used by the catalog),
  DesignCraft's `spread` and EffectCraft's string ids. The source ledger
  records the findings; the verification report records the runner evidence
  and the limits that remain.

## 1.4.0 — 2026-10-14

FigCraft, the ArtCraft team's interface-design and prototyping app, becomes
the thirteenth native stdio server. Same architecture: one more catalog entry,
card, scenario and release pin; no gateway, proxy or second agent.

- `config/apps.json` gains `figcraft` (`figcraft-cli mcp`, `os_only`): the
  released CLI parser accepts only `--attach PORT` and the global
  `--no-system-fonts`, so FigCraft is installed and registered with
  `--acknowledge-unconfined` like the other eight unconfined apps. The lock
  example, the inactive launch templates, `setup --all`, `doctor`, the Skill
  table, the checks and the tests now cover thirteen apps.
- New card `skills/craft/references/apps/figcraft.md` (headless session with
  one untitled document, never `--attach`, page-unit coordinates relative to
  the parent frame, one undo step per mutation, `.figcraft` save, PNG/JPG/
  SVG/WebP/PDF export only with `path`, experimental `.fig`, Display P3 to
  sRGB on SVG/PDF export), FigCraft in the safety list of OS-user-wide apps, a
  FigCraft handoff in the cross-app workflow and a fifteenth acceptance
  scenario.
- `config/releases.json` pins FigCraft v0.5.1 (tag commit `c5830e46…`) on all
  three platforms with the hashes from the release's `SHA256SUMS.txt`
  (`reviewed` 2026-10-14). The three archives were downloaded, hash-checked
  and listed (each holds one `figcraft-cli`) and the macOS CLI was inspected
  with `codesign`/`spctl` (notarized, team `DJ6XS33FX8`) without being
  executed. No Sigstore bundle exists until the daily workflow's next run
  signs it, so a Linux or Windows `setup --app figcraft` needs that run first
  or `--trust-upstream-sums`; macOS verifies notarization as before.
- AGENTS.md and `.claude/CLAUDE.md` record the branch policy: work happens on
  `main` only (the workflow's `bot/releases` pull request is the exception),
  and upstream links point at each Craft repository's `main`, never a tag.
- Release workflow: `gh pr view bot/releases` also matches the merged pull
  request for that branch, so the 2026-10-14 run edited the merged #1 instead
  of opening a new one and the refreshed pins never reached `main`. The
  refresh and merge jobs now look up an *open* pull request for
  `bot/releases` (`gh pr list --state open`) and create one when none exists.
- Wording: the architecture and acceptance docs and the READMEs reject a
  "gateway" server where they used to say "thirteenth"; counts, the diagram,
  the app table (English, German, Turkish) and the GitHub description name
  thirteen apps. `docs/verification.md` records that FigCraft is
  source-reviewed and pinned but not executed; the twelve-app evidence from
  1.1.0 to 1.3.2 is unchanged.

## 1.3.2 — 2026-10-12

- Archived probe evidence gets a name that is never reused
  (`evidence/archive/<app>-<UTC stamp with microseconds>[-n].json`). The
  one-second stamp of 1.3.1 collided when `setup` ran twice within a second:
  Windows refused the rename and reported `promoted_unverified`, POSIX
  silently overwrote the earlier archive. Found by the 1.3.1 lifecycle tests
  on the Windows CI runners; no other behavior changes.

## 1.3.1 — 2026-10-12

Focused reliability and security hardening of the 1.3.0 lifecycle. No new
architecture: the same twelve stdio servers, Skill, SDK probe and
deterministic helpers.

- Interrupted promotion is now reconcilable. The recovery marker lives in
  `state/recovery/<app>.json`, outside staging, so the cleanup that follows a
  failure can no longer discard it. It records the candidate hash, the
  previous hash and pin, and is cleared only after the binary and the lock
  are seen to agree. The next run classifies the active binary as
  `consistent`, `completable` (lock rewritten from the marker), `reverted`
  (the replace never happened), `ambiguous` (matches neither; refused, nothing
  changed) or `corrupt` (marker unreadable; refused, marker kept), reports it
  under `recovery` and in `setup --list`, and `setup --remove` defers to that
  reconciliation first. Recovery never replaces the binary.
- Removal verifies the whole registration, not the command path: command,
  every argument, user scope and the host's own user-scope file
  (`config.toml` / `.claude.json`) must agree with what `setup` writes, the
  app must still be pinned, and the pinned binary must be owned or already
  gone. A same-name entry with other arguments or cwd/env, another scope, a
  text-only Claude entry whose arguments cannot be recovered, a missing pin or
  a modified binary keeps its registration, listed with the reason
  (`attention`, exit 1). A host CLI that is not on PATH is reported as not
  inspected, never guessed.
- `--replace` is recoverable. The old entry is removed only after it is known
  to be restorable exactly (user scope, structured arguments, no cwd/env);
  if adding the new one fails, the old one is re-added and verified. A
  restoration that also fails is reported as `registration_lost` with the
  exact `mcp add` command to run by hand. Entries that cannot be restored are
  refused before anything is removed.
- Evidence names the launch it describes. The staged probe writes
  `evidence/<app>-candidate.json` and that file is never renamed; after
  promotion the active launch is preflighted and probed again, and only that
  report becomes `evidence/<app>.json`, so `configure`'s fingerprint check
  compares like with like. A binary that passes as a candidate but fails at
  its active path is reported as `promoted_unverified` and not registered.
- The daily release workflow verifies strictly: `scripts/check_bundles.py`
  requires a Sigstore bundle for every pinned archive before the Linux,
  Windows and macOS runners run `setup` without `--trust-upstream-sums`.
  `make check` enforces that order and the absence of the flag.

## 1.3.0 — 2026-10-12

Reliability and safety fixes for `setup`, the signature store and `doctor`.
No new architecture: the same twelve stdio servers, Skill, SDK probe and
deterministic helpers.

- `setup --remove --dry-run` previously ignored `--dry-run` and removed for
  real. It is now a read-only preview (`would unregister`, `would delete`,
  `would drop`, `would archive`), and contradictory flag combinations
  (`--remove` with `--upgrade`/`--replace`/`--skip-probe`/
  `--trust-upstream-sums`/`--acknowledge-unconfined`, `--list` with anything)
  are refused before any side effect.
- Removal proves ownership first: a binary is deleted only when it is a plain,
  unlinked file at the managed path whose SHA-256 equals the lock entry; a
  registration is unregistered only when its command is that managed path.
  Anything else is kept and reported with its reason (report `attention`,
  exit 1). There is no force flag.
- Upgrades are staged: download, checksum, provenance, preflight and the
  official-SDK probe all run against a candidate in
  `state/staging/<app>/`; promotion (atomic replace), the lock rewrite and
  registration happen only after they pass, so a failed upgrade leaves the
  previous binary, pin, evidence and registrations untouched. A marker makes
  the window between replace and lock rewrite recoverable on the next run.
  Identical bytes at a new commit only move the pin. A file at the install
  path the lock cannot vouch for is never overwritten, even with `--upgrade`.
  Apps without file roots need `--acknowledge-unconfined` before anything is
  downloaded (the candidate cannot be probed without it).
- Host registration is reported per host: a failing host no longer hides the
  others' results (`partially_registered`).
- Claude Code registrations: `claude mcp get` prints `Args:` joined by spaces,
  so argument boundaries cannot be recovered from text. For user scope the
  structured entry in `.claude.json` is used; otherwise the whole `Args:` line
  is compared, never split. Output that names no command marks the
  registration as present but unreadable, and it is never modified. Codex
  JSON that fails to parse is treated the same way.
- `doctor` now also reads the Claude Code user scope
  (`$CLAUDE_CONFIG_DIR/.claude.json`, the scope `setup` writes), reports each
  scope's command only, and lists the scopes it inspected.
- Signature rotation: the daily job loaded the previous store with the strict
  runtime validator, so the first manifest advance after bundles existed on
  `main` would have failed before pruning. The previous store is now shape-
  and signer-checked, stale entries (unpinned archives, moved hashes) are
  dropped, missing ones are signed, and the complete store is strictly
  validated and published by atomic replace; any failure leaves the old file
  untouched. Malformed bundles and signer drift still fail.
- Tests: 194 offline tests, including removal previews and ownership refusals,
  failed-upgrade preservation, interrupted-promotion recovery, Claude
  parsing with paths containing spaces, doctor scopes and collisions, and
  signature rotation with injected downloads and a fake signer.

## 1.2.2 — 2026-10-12

Documentation release; no code change.

- German and Turkish READMEs (`README.DE.md`, `README.TR.md`), linked from the
  English one and checked by `make check`; English stays canonical.
- README: the two-step update (plugin, then `setup --list` /
  `setup --all --upgrade`), the remove order (`setup --remove --all` before
  `plugin uninstall`), the verified plugin cache path, and a "Where things
  live" table for the plugin, CLIs, private state, workspace and host
  registrations on macOS/Linux and Windows.
- `make github-push` pulls with rebase onto `origin/main` and re-checks the
  generated plugin before pushing, because the daily workflow merges into
  `main` on its own; `make github-pull` rebases instead of refusing.
- Verification report: first local Sigstore verification with cosign.

## 1.2.1 — 2026-10-12

Fixes the first run of the daily release workflow, which failed in its test
step, and the main CI matrix on Linux and Windows.

- The archive member `setup` extracts is now named for the archive's platform
  (`<app>-cli.exe` only inside Windows zips) while the installed file is named
  for the running OS; the tests that simulate other platforms relied on that
  distinction and failed on Windows runners. No change for real installs.
- Tests: the CLI dry-run test accepted only macOS; doctor and setup tests
  created `<app>-cli` without `.exe`, compared paths without it and read
  recorded state from `~/.local` on Windows.
- A doctor test hard-coded CADCraft's manifest tag, so the first genuine
  upstream release (CADCraft 0.6.2) failed the workflow's test step right
  after the refresh; tests now read expected versions from the manifest.
- Documentation pass: README, operations, security, architecture, contributing
  and the plugin README now describe install, update (`setup --list`,
  `--upgrade`), re-registration (`--replace`) and removal (`--remove`) as the
  code behaves, say that all twelve apps have been verified on three OSes, and
  point at `config/releases.json` instead of a release table that went stale.
- Documented the three repository settings the daily workflow needs to run
  hands-off (Actions may open pull requests, approval policy for new-to-GitHub
  accounts only, `STORYTOLD_AUTO_MERGE`); PR creation is now non-fatal.
- The workflow's first run had already refreshed the manifest (WordCraft
  0.6.1) and signed all 36 archives keyless before the test step stopped it,
  so extraction against the real macOS, Linux and Windows archives is
  confirmed; that run's signatures were discarded with the runner and are
  regenerated on the next run.

## 1.2.0 — 2026-10-12

`setup` now covers Linux x86_64 and Windows x64, and the release pins refresh
themselves daily.

- Platform support: the manifest pins one archive per platform (macOS CLI zip,
  Linux tarball, Windows portable zip); `setup` extracts exactly the one
  `<app>-cli` from zip or tar.gz, uses per-OS paths
  (`%LOCALAPPDATA%\Storytold` on Windows, `$XDG_STATE_HOME` on Linux), the
  venv's `Scripts\python.exe`, and runs `.cmd` host shims through `cmd.exe`.
- Provenance: upstream does not code-sign Linux or Windows builds, so the new
  daily workflow signs every pinned CLI keyless with Sigstore cosign under its
  own GitHub OIDC identity and commits the bundles to `config/signatures.json`;
  on Linux and Windows `setup` requires that bundle and `cosign verify-blob`
  (`--trust-upstream-sums` to proceed on the manifest and `SHA256SUMS.txt`
  alone, recorded in the lock); macOS keeps Apple notarization and verifies the
  bundle too when cosign is present.
- `.github/workflows/releases.yml`: daily `refresh_releases.py` +
  `sign_releases.py`, plugin rebuild, checks, tests, a real `setup` on Linux,
  Windows and macOS runners, and one pull request on `bot/releases`; optional
  auto-merge via the `STORYTOLD_AUTO_MERGE` repository variable. Actions are
  commit-pinned, credentials are not persisted, only `github.token` is used.
- Manifest schema 2 with a `signers` block (Apple team, Sigstore identity and
  issuer); `make check` validates the manifest, the signature store and the
  workflow's permission rules.
- Refreshed pins: VectorCraft 0.10.0, PdfCraft 0.7.1, SoundCraft 0.6.1.
- Tests: 169 offline tests, including the setup flow on three simulated
  platforms.

## 1.1.0 — 2026-10-12

One command now takes a plugin user from "tools aren't connected" to twelve
registered native servers on macOS.

- `storytold.py setup --app <app> | --all [--acknowledge-unconfined]`: downloads
  the CLI release pinned in the new reviewed manifest `config/releases.json`,
  verifies the archive against the manifest and the release's `SHA256SUMS.txt`,
  requires Apple notarization by the ArtCraft team, installs to
  `~/.local/opt/craft/bin`, pins the hash in the private lock, runs `preflight`
  and the official-SDK probe (initialize, tools/list, one read-only call), and
  registers the server with `codex mcp add` / `claude mcp add --scope user`.
  Downloads are limited to GitHub release hosts; one registration per name;
  `--dry-run`, `--list`, `--upgrade`, `--replace`, `--skip-probe`, `--remove`.
  macOS only in this release; Windows/Linux installers already ship the CLI.
- Apps without file roots are installed but registered only with
  `--acknowledge-unconfined`, matching the existing preflight policy.
- `config/releases.json` pins all twelve latest releases (tag, commit, zip
  hash, size, smoke tool); `make refresh-releases` regenerates it for review
  and `make check` enforces its shape. Chosen paths are recorded in
  `~/.local/state/storytold/setup.json`, so `preflight`, `probe`, `configure`
  and `doctor` need no exported variables afterwards.
- `doctor` prints the exact `setup` command per missing app plus manifest and
  pinned versions; the `craft` Skill proposes that command, runs it only after
  the user agrees in chat, and never installs anything unasked.
- `storytold.py` explains the Python 3.11 requirement instead of failing with
  a syntax error on macOS system Python.
- Tests: 159 offline tests (setup flow with injected network, macOS tools and
  host CLIs; manifest rules; recorded state).

## 1.0.1 — 2026-10-12

Fixes "PhotoCraft's native tools aren't connected / `photocraft-cli` isn't on
PATH" after installing the plugin and the desktop apps.

- Root cause, now documented: each MCP server is the app's `<app>-cli`, and on
  macOS the ArtCraft Launcher and `.dmg` install only the `.app`. The CLI is the
  separate `<app>-cli-<version>-macos-universal.zip` release asset (Windows
  MSI/portable ZIP and Linux `.deb`/`.rpm` include it), and it must also be
  registered with the host. Operations section 0 lists the asset and tag commit
  for all twelve apps' latest releases, with download, checksum, notarization
  and install steps; the README setup steps start there.
- All twelve app cards were rechecked against each app's latest release tag
  (CLI parser, MCP docs, packaging) and now link docs pinned to that tag.
  Corrections include: GridCraft refuses legacy `.xls` (XLSB/ODS import values
  only); FilmCraft 0.6.0 renders offline media silently as a slate and reports
  success; DeckCraft 0.5.0 now exposes PDF export options; CADCraft
  `inspect_drawing` returns up to 200 entities unless `entities` is false;
  VectorCraft batch steps undo individually; SoundCraft 0.5.0 ignores unknown
  `mcp` flags; PdfCraft in-place saves are incremental except after redaction.
  Each card lists its release's main MCP tools.
- WordCraft keeps no root flags in the catalog: upstream `main` adds
  `--automation-read-root`/`--automation-write-root`, but the 0.5.0 CLI rejects
  them. All other catalog launch flags are accepted by the released CLIs.
- The `craft` Skill's missing-server report now names the fix (install the CLI
  asset, register it, start a new session) instead of only stating the gap.
- All twelve app cards state where the CLI comes from.
- `storytold.py doctor` adds a read-only `connections` report: per app, the
  desktop app, a CLI in `CRAFT_BIN_DIR`/PATH, Codex (`$CODEX_HOME`, `./.codex`)
  and Claude project registrations, whether the registered command exists, and
  the next step. Nothing is executed or edited.
- Codex registration guidance covers `~/.codex/config.toml` as well as a
  trusted project's `.codex/config.toml`, with backup and new-session steps.
- First native evidence: PhotoCraft 0.7.0 passed initialize, discovery and a
  read-only `doc_inspect` smoke call on macOS arm64; see `docs/verification.md`.

## 1.0.0 — 2026-10-12

First public release of devsolux/storytold, installable from GitHub as
`storytold@devsolux-storytold` in Claude Code and Codex. Released under the MIT
License.

- One `craft` Skill (`/storytold:craft`), twelve source-linked app cards, and
  single-app and file-handoff playbooks.
- Deterministic helpers: binary inventory and preflight without execution,
  private working-copy staging, limited artifact checks, an optional official
  MCP SDK 2.3.0 probe, and evidence-bound local Claude/Codex config generation.
- Guarded, reproducible plugin and source packaging with marketplace identity,
  install-command and generated-file ownership checks.
- One portable root `plugin.json` carries the OpenAI/Codex metadata under
  `extensions.com.openai`; Claude Code reads `.claude-plugin/plugin.json`. No
  `.codex-plugin` compatibility overlay is shipped.
- File hashing reads raw bytes on every OS (binary mode on Windows); corrupt
  containers, including damaged compressed OOXML members, fail as validation
  errors rather than tracebacks.

The default runtime has inactive launch templates only; it never starts Craft
apps by itself. Native app and host acceptance gates (M0–M4) remain operator
steps; see `docs/verification.md` for what this release actually ran.
