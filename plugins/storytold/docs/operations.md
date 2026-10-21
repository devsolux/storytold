# Local setup, operation and rollback

These are operator steps, not actions performed by installing the plugin. Use
non-sensitive fixtures until [acceptance](acceptance.md) passes. `setup` has
installed, probed and Sigstore-verified all thirteen CLIs on macOS, Linux and
Windows runners, twelve of them on a developer Mac as well; that is M0-level
evidence, not the M1–M3 gates. See [verification](verification.md).

## One-command setup (macOS, Linux x86_64, Windows x64)

```bash
python3 "$STORYTOLD/storytold.py" setup --app photocraft
python3 "$STORYTOLD/storytold.py" setup --all --acknowledge-unconfined
```

`setup` performs sections 0–5 below for each selected app, in order, stopping
at the first failure, and prints a JSON report:

1. Paths: `~/.local/opt/craft/bin` (binaries; Windows:
   `%LOCALAPPDATA%\Storytold\craft\bin`), `~/craft-work-storytold` (workspace,
   created with `workspace-init` if absent), and `~/.local/state/storytold/`
   (Linux honours `$XDG_STATE_HOME`; Windows: `%LOCALAPPDATA%\Storytold\state`)
   for the lock, evidence, probe venv and `setup.json`. `CRAFT_*` variables or
   `--bin-dir/--work-root/--lock/--evidence-dir` override them; later commands
   read `setup.json`, so no exports are needed.
2. Download of the archive pinned for your platform in `config/releases.json`
   (macOS: `<app>-cli-<v>-macos-universal.zip`; Linux: the `-linux-x86_64.tar.gz`
   tarball, standalone CLI when upstream publishes one; Windows:
   `<app>-<v>-windows-x64-portable.zip`) and that release's `SHA256SUMS.txt`,
   HTTPS to GitHub release hosts only (redirects elsewhere are refused, 512 MiB
   cap). The archive hash must match the manifest **and** the published sums; a
   disagreement stops with a message naming the source.
3. Exactly one `<app>-cli` (`.exe` on Windows) is taken from the archive; the
   desktop binary and everything else in a full-application archive are
   ignored, links and traversal are refused. Provenance per platform:
   - macOS: `spctl` must report *Notarized Developer ID* and `codesign` the
     manifest's Apple team, otherwise the file is discarded.
   - Linux and Windows: upstream publishes no code signature, so `setup`
     requires the Sigstore bundle that the daily workflow produced for this
     exact archive (`config/signatures.json`): the extracted binary's SHA-256
     must equal the signed one, then `cosign verify-blob --bundle … 
     --certificate-identity-regexp <manifest signers> --certificate-oidc-issuer
     https://token.actions.githubusercontent.com` must pass. Install cosign
     first (Linux: the release binary or distro package; Windows:
     `winget install sigstore.cosign`; macOS: `brew install cosign`). Without a
     bundle or cosign, `--trust-upstream-sums` proceeds on the manifest and
     `SHA256SUMS.txt` alone and records "upstream sums only" in the lock.
   - macOS also verifies the bundle when cosign is present.
4. The verified file is staged beside the active installation
   (`~/.local/state/storytold/staging/<app>/`) with its own one-app lock. An
   installed binary whose lock entry already matches the manifest commit is
   skipped without a download, so re-runs resume and are idempotent; one with
   a different pin needs `--upgrade`; a file at the install path that the lock
   does not prove Storytold wrote (no entry, different bytes, a link) is never
   touched, with or without `--upgrade`: move it aside first.
5. `preflight`, then the native probe (initialize, `tools/list`, one read-only
   `smoke_tool` call from the manifest) run against the **staged candidate**
   through the official SDK in `~/.local/state/storytold/venv` (created once
   from PyPI), writing `evidence/<app>-candidate.json`. `--skip-probe`
   promotes an unexercised binary and says so. Apps without file roots need
   `--acknowledge-unconfined` before anything is downloaded, because
   preflight, and so the probe, cannot run without it.
6. Only after that the candidate is promoted: an atomic replace inside the
   bin directory (identical bytes are left in place and only the pin moves),
   then the lock is rewritten. The binary replace and the lock rewrite are two
   writes, so a recovery marker (`~/.local/state/storytold/recovery/<app>.json`,
   outside staging, recording the candidate hash and the previous hash and
   pin) is written first and cleared last, only after the binary and the lock
   are seen to agree. The candidate evidence stays
   `evidence/<app>-candidate.json`; the staging directory is removed.
7. The active launch is verified on its own: `preflight` against the bin
   directory and the real lock, then the probe again at the installed path,
   writing `evidence/<app>.json` (the previous one is archived). That report,
   not the candidate's, is what `configure` later matches against the launch
   fingerprint. A binary that passed as a candidate but fails here is
   reported as `promoted_unverified`, stays installed and pinned, and is not
   registered; re-run `setup` to probe again or `setup --remove --app <app>`.
8. Registration through the host's own CLI, user scope, absolute command and the
   exact catalog args: `codex mcp add` and/or `claude mcp add --scope user`,
   for every host CLI on PATH (`--host` limits). A registration that already
   matches is kept; a same-name registration with a different command is
   refused unless `--replace`; one whose command the host CLI does not print
   is never modified. With `--replace` the old entry is removed only once it
   is known to be restorable exactly (user scope, structured arguments, no
   cwd/env); if adding the new one fails, the old one is re-added and that
   restoration is verified. If the restoration fails too, the host row says
   `registration_lost` and gives the exact `mcp add` command to run by hand.
   Each host is reported separately: if one fails, the binary and pin are
   already current and the report says `partially_registered`. Nothing else
   in the host configuration is touched. Start a new session afterwards.

A candidate that fails at any step up to promotion leaves the previous
binary, its pin, its evidence and every registration exactly as they were;
only `evidence/<app>-candidate.json` records the failed attempt. A failure
between the replace and the end of step 6 leaves the marker in place; the
next `setup` run (or `--list`) classifies it before anything else happens:
`consistent` (binary and lock already agree: marker cleared),
`completable` (the binary is the verified candidate, the lock still names the
previous one: the lock is rewritten from the marker, never the binary),
`reverted` (the binary is still the previous one: marker cleared, the
upgrade is simply retried), `ambiguous` (the binary matches neither: refused,
nothing changed, the marker stays until you move the file aside or restore a
known binary and delete it) or `corrupt` (the marker is unreadable: refused,
marker kept). `setup --remove` defers to the same reconciliation and keeps
everything for an app whose marker is still present.

Apps without root flags are neither downloaded, upgraded nor registered without
`--acknowledge-unconfined` (one already installed at its manifest pin is reported
`installed_not_registered`); the flag records your decision for non-sensitive
work and is not isolation. Without it such an app is reported
`needs_acknowledgement` and skipped whatever its install path holds (the message
also names a stale pin or a foreign file you would meet next), the other selected
apps are still processed, and the run exits non-zero. `--all` and `--app` cannot
be combined, and `--timeout` (the probe's limit) accepts at most 120 seconds.
`--host` names the hosts to register with: a named host whose CLI is not on PATH
is warned about and fails the run, while the other named hosts are still
registered.

One changing run at a time: `setup` and `setup --remove` hold an OS advisory lock
on `setup.lock` in the state directory for the whole run, so a second one stops
at once ("another setup run … is using …") and changes nothing. The operating
system releases that lock when its process ends, however it ends (Windows may
take a moment), so a crash leaves nothing to delete; a filesystem without file
locks is named as such instead. `--dry-run` and `--list` take no lock. Each
rewrite of the installation lock is additionally guarded by a sibling
`<lock>.writing` marker. Before anything is created or downloaded, `setup`
refuses a leftover marker, a state or evidence directory that is not
owner-only, a bin directory that group or others can write and a work root that
is not a Storytold workspace; `setup --remove` refuses the leftover marker the
same way, before any binary is deleted. Delete a leftover marker once no setup
is running. After the first failure the run stops, and the apps it never
attempted are listed as `not_reached`.

`--dry-run` makes the per-app decision a real run makes, from read-only checks,
and reports it. `binary` is `keep` (installed and pinned at this release, no
download), `install`, `upgrade`, `skip` (not acknowledged) or `refuse`, with a
`reason` (a foreign file at the install path, a pin that needs `--upgrade`, an
unresolved recovery marker). `download` is set only when one is needed.
On Linux and Windows a download without a published Sigstore bundle, or
without cosign on PATH, is predicted to fail at provenance unless
`--trust-upstream-sums` is given. `registrations` says per host whether the
entry would be added (`add`), kept (`already_registered`) or replaced
(`replace`), or why not: `refuse: …` without `--replace`, or for an entry with
env, cwd or other settings `mcp add` could not restore, and `unknown: …` when
the host's user-scope file cannot be read. `predicted_status` is the status the
real run would report (`not_reached` after the first failure, because the real
run stops there), and `would_pass` sums it up together with warnings such as a
missing named host or a layout problem from the list above. A dry run exits 0
only when `would_pass` is true, like `--remove --dry-run`, which exits 1 on
`attention`. Downloads, notarization, Sigstore verification and probes are not
attempted, so a passing preview is not a promise. `--list` shows manifest,
installed, pinned and registered state.

`--remove --app X` takes two separate decisions. The binary is deleted only when
it is a plain, unlinked file whose SHA-256 equals the lock entry and no
registration that may still launch it remains on any host; then that pin is
dropped and its evidence archived. A registration is unregistered only when
it is, in full, the user-scope entry `setup` writes: the command is the
managed path, every argument is the catalog launch, the host reports user
scope, the host's own user-scope file (`$CODEX_HOME/config.toml`,
`$CLAUDE_CONFIG_DIR/.claude.json`) carries the same entry with nothing but
command, arguments and an empty env (no cwd, no tool or timeout settings), the
app is still pinned, and the pinned binary is either owned or already gone. A same-name registration that points elsewhere or carries other
arguments, one in another scope, one the host CLI cannot describe (or whose
arguments only appear as joined text), one for an app without a pin, or one
whose binary was modified is kept and listed with its reason (exit status 1,
report `attention`). Every host gets a row. A host whose CLI is not run, because
it is not on PATH or `--host` left it out, has nothing unregistered, but its
user-scope file is still read: while it registers the app at the managed binary
(or cannot be read), the binary, its pin and its evidence stay, so no host is
left with a dangling server. A registration that could not be inspected, or
whose `mcp remove` failed, or whose command the host does not show, is kept the
same way, and an `mcp remove` that reports success is trusted only once the
user-scope file no longer lists the entry. Before deleting, both hosts' files
are also searched for any other registration that starts the binary: another
server name, another spelling or link of the path, or a Claude Code
local-scope entry; `references` lists them by host, scope and name (never a
project path), and the binary stays until they are gone. The run goes on with
the other hosts and apps, and an app that fails unexpectedly becomes a report
row instead of ending the run. The pin stays as long as any such registration
does, because it is what lets a later `--remove` prove the entry is
Storytold's. Reports never quote host-file contents: an unreadable file is
named, not excerpted, and only text commands are shown. `--remove --dry-run`
prints the same report with `would …` actions and changes nothing on disk;
note that `claude mcp get`, which `--remove`, its dry run, `--list` and
registration all use, starts the registered server for its health check, as a
Claude Code session does. The workspace is never touched.
Maintainers refresh the manifest with `make refresh-releases` and review the
diff; `python scripts/refresh_releases.py --accept <app>` lets one app through
the downgrade/re-publish guard after its upstream change was reviewed by hand
(the workflow never passes it). `make sign-releases` (cosign required)
downloads and signs CLIs that have no current bundle. Each of the refresh's 39
small metadata requests, each download and each signing is tried up to three
times (15 s, then 45 s apart) on a dropped connection, a 5xx or a 429, every
signing in a fresh cosign process with a new ephemeral key, so a transient
GitHub, Fulcio or Rekor fault, including a Rekor `409 createLogEntryConflict`
after cosign's own HTTP retry, does not fail the run. Any other HTTP error (a
release without SHA256SUMS.txt, a missing asset) and a size-limit or hash
refusal are final: they are findings about the release, not hiccups.
In the repository this runs daily: the
[release workflow](https://github.com/devsolux/storytold/blob/main/.github/workflows/releases.yml) refreshes, signs keyless
with its GitHub OIDC identity (`id-token: write`) and rebuilds the plugin in a
job that holds no write token, hands the changed files to a `publish` job that
runs only `git` and `gh` (the one holding `contents: write`) to commit them,
and runs `scripts/build.py check` (the published plugin matches its sources),
the checks, `scripts/check_bundles.py` (every pinned archive must have a
bundle) and a real `setup --all --acknowledge-unconfined` that verifies each
bundle with cosign, never `--trust-upstream-sums`, on Linux, Windows and macOS
runners, and opens one pull request on
`bot/releases` (an open one is updated, title and body). The run's summary page
shows the refresh and signing reports and the changed files, so a day's result
is readable without the logs; a run takes about four minutes, most of it the
three-OS verify downloading and probing all thirteen CLIs. Review the pull
request (a changed app needs its card and smoke tool rechecked
at the new tag) or set the repository variable `STORYTOLD_AUTO_MERGE=true` to
merge green runs. The verify jobs check out the exact commit the refresh job
pushed, and the merge job merges only that commit (`--match-head-commit`) of a
same-repository pull request; it fails, rather than ending green, when no such
pull request is open. The refresh stops the run instead of pinning when an
app's latest release is older than its pin, when a pinned tag now points at
another commit, or when an asset was re-published under an unchanged tag and
name; review those by hand. The `reviewed` date moves only with a pin, so a day
without upstream changes opens no pull request. Signing identity, issuer and
Apple team are data in the manifest's `signers`, and `make check` pins them to
this repository's release workflow on `main` and the Apple team; the
signature store names the archive it was made for.

Three repository settings make the automation hands-off; `devsolux/storytold`
has all three:

| Setting | Why |
|---|---|
| Actions › General › *Allow GitHub Actions to create and approve pull requests* | lets the workflow open `bot/releases` pull requests with `github.token`; without it the branch is still pushed and a warning gives the compare URL. |
| Actions › General › approval policy *first-time contributors who are new to GitHub* | the pull request author is `github-actions[bot]`; the stricter default holds its CI runs "awaiting approval" until a maintainer clicks. Observed on pull requests #1 to #5: the offline-checks run on the bot's pull request still never started a job and turned to failure when the merge deleted the branch. Since 1.5.2 `ci.yml` ignores pull requests that change only `config/releases.json`, `config/signatures.json` and `plugins/storytold/**`, so no such run is created; the release workflow's own `check`, `test` and three-OS verify jobs are the gate. |
| Repository variable `STORYTOLD_AUTO_MERGE=true` | the `merge` job squash-merges the pull request once the three-OS verify matrix is green. Delete the variable to go back to manual review. |

## 0. Manual path: get each app's CLI yourself

Use this on other platforms, on air-gapped machines, or for custom pins;
`setup` does all of it on macOS, Linux x86_64 and Windows x64.

Every MCP server is an app's command-line tool, `<app>-cli` (for example
`photocraft-cli mcp`). On macOS the `.dmg` and the ArtCraft Launcher install the
GUI only: `PhotoCraft.app` contains no `photocraft-cli`, so a host has nothing to
connect to. Every Craft app publishes the macOS CLI as a separate signed and
notarized release asset, `<app>-cli-<version>-macos-universal.zip`, listed in
that release's `SHA256SUMS.txt`. On Windows the MSI and portable ZIP install
`<app>-cli.exe` next to the app (not on PATH); on Linux the `.deb`/`.rpm` install
`/usr/bin/<app>-cli`. Pin whichever copy you use, preferably the version that
matches your desktop app.

The reviewed pins live in `config/releases.json`, which the daily workflow
keeps current: per app the release tag, its commit (the lock's `revision`),
and per platform the archive name, size and SHA-256 from upstream's
`SHA256SUMS.txt`. Print them instead of copying from a document that would go
stale:

```bash
python3 -c "import json;m=json.load(open('config/releases.json'));[print(a,r['tag'],r['commit'],r['assets']['macos']['name']) for a,r in m['apps'].items()]"
```

Which apps have native file roots is recorded in `config/apps.json`
(`confinement`) and on each app card.

On macOS, install one app at a time; set `APP` and `VER` from the manifest:

```bash
APP=photocraft VER=0.7.0
ZIP="$APP-cli-$VER-macos-universal.zip"
mkdir -p "$HOME/Downloads/$APP-cli-$VER" && cd "$HOME/Downloads/$APP-cli-$VER"
gh release download "v$VER" --repo "storytold/$APP" --pattern "$ZIP" --pattern SHA256SUMS.txt
grep " $ZIP\$" SHA256SUMS.txt | shasum -a 256 -c -
ditto -x -k "$ZIP" .
BIN=$(find . -type f -name "$APP-cli" | head -n 1)
spctl --assess --type install -vv "$BIN"
mkdir -p "$HOME/.local/opt/craft/bin" && chmod 0755 "$HOME/.local/opt/craft/bin"
install -m 0755 "$BIN" "$HOME/.local/opt/craft/bin/"
gh api "repos/storytold/$APP/commits/v$VER" --jq .sha
```

`spctl` must report `source=Notarized Developer ID` with the same team as the
desktop app (for example `codesign -dv /Applications/PhotoCraft.app`). The last
command prints the tag's full commit for the lock's `revision`. Without `gh`,
download both files from the release page. Nothing in Storytold downloads or
installs apps except the explicit `setup` command. Apps without file roots can
read and write anywhere your user can; see section 2 before registering them.

## 1. Establish paths and native provenance

In the source repository (POSIX example):

```bash
export STORYTOLD="$PWD"
export CRAFT_BIN_DIR="$HOME/.local/opt/craft/bin"
export CRAFT_WORK_ROOT="$HOME/craft-work-storytold"
export CRAFT_OUTPUT_ROOT="$CRAFT_WORK_ROOT/outputs"
python3 "$STORYTOLD/storytold.py" workspace-init --root "$CRAFT_WORK_ROOT"
```

The binary directory must already contain separately installed, reviewed apps.
The new workspace's parent must exist; the initializer never adopts an existing
folder. Use real absolute paths, not symlinks, traversal, UNC shares, home or disk
root. On Windows set equivalent `$env:...` values; executables must be `*-cli.exe`.
Inspect ACLs and native behavior on Windows. Do not treat POSIX chmod as an ACL.

```bash
python3 "$STORYTOLD/storytold.py" inventory --app photocraft
```

Inventory reads/hashes, never executes. It does not know release versions or prove
origin. Independently verify published checksums/provenance or your own pinned
build process. Copy `config/installations.lock.example.json` to a private location,
fill real `platform.system`/`platform.machine`, and include only the apps you have
actually installed and pinned. Each entry needs a full immutable source revision,
a reviewed version/build label and the actual trusted SHA-256. Nulls/placeholders,
mutable branch names, mismatched platforms and unknown app names are rejected.
Never relabel an observed untrusted hash as an authenticated release check.

Keep the lock **outside the native read/write workspace**, along with private
probe evidence. For example, create an owner-only `$HOME/.local/state/storytold`
directory and set `CRAFT_LOCK` and `CRAFT_EVIDENCE_DIR` to real paths there.
This protects accidental engine access only when OS permissions actually enforce
it; unconfined apps have the same user authority unless separately isolated.

## 2. Inspect local readiness without executing binaries

```bash
python3 "$STORYTOLD/storytold.py" preflight \
  --lock "$CRAFT_LOCK" --app photocraft
```

Preflight validates all supplied lock entries, selected binaries and exact output
root. Select only available apps; omission of `--app` means all thirteen. Multiple
`--app` flags are allowed for preflight/configure, but a probe targets one app.

FilmCraft, LightCraft, GridCraft and CADCraft
require tested external isolation for sensitive work.
For an explicitly non-sensitive test, `--acknowledge-unconfined` records your
decision to proceed;
it does **not** claim isolation. PdfCraft's write root now keeps it out of
`inputs/`, but the workspace's read-only copies are still only POSIX modes. Native hash/root checks do not restrict the host's other tools.

## 3. Install the optional conformance client

```bash
cd "$STORYTOLD"
make setup-probe
make test-sdk
```

Only this setup target accesses a package index. Core maintenance is offline.
`requirements-probe.txt` pins the reviewed direct SDK version and
`requirements-probe.lock` its complete graph for every platform (Python 3.11 and
later), each wheel with its SHA-256. `make setup-probe`, `setup`'s probe venv and
the CI SDK job install only from that lock with `--isolated --require-hashes
--only-binary=:all:`: no source builds, and no `PIP_*` variable or pip
configuration file can redirect the index. `make lock-probe` (uv, network)
re-resolves it; review that diff like any dependency update. An unavailable dependency makes the SDK gate fail explicitly;
no successful stub result is substituted for it.

## 4. Probe one trusted app, then an approved fixture call

```bash
"$STORYTOLD/.venv/bin/python" "$STORYTOLD/storytold.py" probe \
  --lock "$CRAFT_LOCK" --app photocraft --confirm-execution \
  --output "$CRAFT_EVIDENCE_DIR/photocraft-discovery.json"
```

This starts the pinned app in the dedicated workspace, negotiates the initialize
handshake through the official SDK (its `legacy` mode), follows bounded tools/list
pagination, and closes the SDK context. Review the discovered schemas. Create a
private JSON file with exactly `name` and `arguments` for a representative
**read-only, non-sensitive fixture inspection** supported by this actual binary.
Do not copy invented tool names from an example. Then:

```bash
"$STORYTOLD/.venv/bin/python" "$STORYTOLD/storytold.py" probe \
  --lock "$CRAFT_LOCK" --app photocraft --confirm-execution \
  --call-json "$CRAFT_EVIDENCE_DIR/photocraft-inspect-call.json" --approve-call \
  --output "$CRAFT_EVIDENCE_DIR/photocraft.json"
```

A new file is required each time. Preserve failed runs; deliberately archive an
old canonical receipt before selecting a new one. An SDK context exit is **not**
proof of graceful native EOF exit, stdout purity or absence of live GUI attachment.
Those have separate native acceptance checks. Inspect native --help/MCP help and
version output manually after pinning; some apps use different version commands.

The probe allows only one explicitly authorized discovered tool call. It does not
infer read-only status from annotations. Do not use it as a task executor or feed
unreviewed scripts/macros to it. A timeout after starting a call is indeterminate;
there is no retry. Native result blocks retain typed content and `isError`.

## 5. Generate local configuration without overwriting other settings

`setup` registers servers through `codex mcp add` and `claude mcp add --scope
user` instead; the generated files below are the manual, project-scoped path.

Claude Code:

```bash
python3 "$STORYTOLD/storytold.py" configure \
  --lock "$CRAFT_LOCK" --app photocraft --host claude \
  --evidence-dir "$CRAFT_EVIDENCE_DIR" --output "$CRAFT_WORK_ROOT/.mcp.json"
cd "$CRAFT_WORK_ROOT"
claude mcp list
claude mcp get photocraft
claude
```

Keep this workspace as the Claude project's working directory. The generated
Claude config contains no undocumented cwd field; actual host launch-CWD
behavior must pass acceptance. Review/approve the project server in Claude's UI.
Load the installed Storytold plugin; Claude Code shows the Skill as `/storytold:craft`.
Do not also register the same app in user scope or a second plugin.

Local Codex:

```bash
python3 "$STORYTOLD/storytold.py" configure \
  --lock "$CRAFT_LOCK" --app photocraft --host codex \
  --evidence-dir "$CRAFT_EVIDENCE_DIR" --output "$CRAFT_EVIDENCE_DIR/codex-mcp.toml"
```

This emits a TOML fragment with concrete command/args/cwd. Review it, back up the
target, then append only its `[mcp_servers.<app>]` tables to one of:

- `~/.codex/config.toml` (or `$CODEX_HOME/config.toml`): every local Codex
  session, including Codex app chats;
- a trusted project's `.codex/config.toml`: only sessions opened in that project.

```bash
cp -p ~/.codex/config.toml ~/.codex/config.toml.bak
sed -n '/^\[mcp_servers\./,$p' "$CRAFT_EVIDENCE_DIR/codex-mcp.toml" >> ~/.codex/config.toml
codex mcp get photocraft
```

Keep unrelated settings and approvals; never register one app twice. The kit
itself never edits Codex files or assumes Claude's environment-variable expansion
works in TOML. Codex loads MCP servers when a session starts: open a **new**
chat/session, then check `/mcp`. Web/mobile execution is not implied. See current
host sources in [source ledger](source-ledger.md).

Add the remaining apps one at a time after evidence is captured. To expand an
existing `.mcp.json`, create a new reviewed config in a separate test workspace or
archive/move the previous file deliberately; the generator never overwrites it.
Moving the workspace or changing paths, binary, revision, platform or catalog
invalidates fingerprints and requires new evidence.

## 6. Stage and verify actual work

```bash
python3 "$STORYTOLD/storytold.py" stage --source /absolute/originals/brief.txt
# Native host tools perform the requested edit and export to outputs/.
python3 "$STORYTOLD/storytold.py" verify-inputs
python3 "$STORYTOLD/storytold.py" verify-artifact \
  --path outputs/result.json --format json
```

If staging cannot write its receipt, the copied file is preserved and the operation
fails rather than claiming success. Input verification checks that every remaining
staged input has exactly one receipt; missing/duplicate receipts fail. This local
ledger is not signed or protected against an owner deleting both copy and receipt.

The helper verifies only the declared check level. JSON parses; PCM WAV checks
frames; OOXML checks bounded ZIP/XML structure. XML inspection is UTF-8-only and
limited to 8 MiB per XML part; other encodings require a native/independent verifier. Text checks UTF-8. PNG/JPEG/PDF
checks are **signature-only**. SVG XML parsing neither renders nor sanitizes
active content. None establishes native reopen, visual quality, complete format
fidelity or business approval. Native/app-specific verification remains mandatory.
Staging/inspection is capped at 128 MiB; larger media needs a separately reviewed
OS-level staging process, not a silent limit bypass or writable original.

## Troubleshooting: "native tools aren't connected"

If the Skill reports that an app's native tools aren't connected, or that
`<app>-cli` isn't on PATH, the host has no MCP server for that app. Installing
the Storytold plugin or a desktop app never registers one. Run the read-only
diagnostic from the repository or the installed plugin:

```bash
python3 "$STORYTOLD/storytold.py" doctor
```

For each app, `connections.apps[]` shows the desktop app, a CLI in
`CRAFT_BIN_DIR` or on PATH, Codex (`~/.codex`, `./.codex`) and Claude
(`./.mcp.json`) registrations, a `status` and the `next` step:

| `status` | Fix |
|---|---|
| `not_installed` | Run the `setup` command doctor prints (macOS, Linux x86_64, Windows x64); elsewhere install the CLI (section 0). |
| `desktop_app_only` | Run the `setup` command doctor prints (macOS, Linux x86_64, Windows x64); elsewhere install the CLI (section 0). |
| `cli_not_registered` | The `setup` command; elsewhere sections 1–5: lock, preflight, probe, configure, register. |
| `registered_command_missing` | The binary moved or was removed; re-run `setup` (with `--upgrade` if a stale file remains) or reinstall and re-probe by hand. |
| `registration_unknown` | A host configuration (or the lock) could not be read; `host_config_errors` names it. Fix the file, or wait until the host stops writing it, and run `doctor` again before re-registering. |
| `registered` | Start a new host session; check `codex mcp get <app>` or `claude mcp get <app>` and approve the server. |

`doctor` reads the Codex user (`$CODEX_HOME/config.toml`) and project
(`./.codex/config.toml`) scopes and the Claude Code user
(`$CLAUDE_CONFIG_DIR/.claude.json`, the scope `setup` writes) and project
(`./.mcp.json`) scopes, and reports only each server's command, never other
settings in those files. `python3 storytold.py setup --list` adds, per app,
whether the installed binary matches its pin (`owned`), whether that pin is
still the manifest's commit, the status recorded in its probe evidence
(`probe_evidence`, `null` when there is none), the hosts that report it
(`registered`) and those whose `mcp get` failed for another reason than "no
such server" (`registration_unknown`), and the `recovery` state of any
interrupted upgrade (`none`, `consistent`, `completable`, `reverted`,
`ambiguous`, `corrupt`). `setup --remove` archives `<app>.json`,
`<app>-candidate.json` and `<app>-call.json` under `evidence/archive/` rather
than deleting any of them, and keeps the binary and its pin while a
registration it must keep (or could not inspect) still launches that binary.

PATH does not matter for the connection: hosts launch the absolute `command` from
their config. Claude user-scope servers are outside this static check; use
`claude mcp list`. Never let an agent work around a missing server by running
`<app>-cli` from a shell.

## Failures, update and rollback

Leave originals and last verified intermediates intact. Record native errors and
warnings. Do not delete library locks, silently switch to live/remote execution,
ignore missing media, auto-retry mutations or claim completion from tool success.
Keep a known-good native binary/lock outside writable areas. Upgrade one app at
a time: trusted revision/hash → preflight → discovery diff → acceptance. Review
catalog changes in code; the generator rejects ad-hoc executable/flag overrides.

With `setup`, an update is: update the plugin (new manifest), `setup --list`
to see which pins moved, then `setup --app <app> --upgrade` per app (or
`--all --upgrade`; unchanged apps are skipped). The binary is replaced only
after download, hash, provenance, preflight and the probe of the staged
candidate succeed, the lock entry is rewritten atomically, and the host
registration is left alone because the command path does not change; when a
release changes an app's launch arguments instead (WordCraft's root flags in
1.5.0, SoundCraft's in 1.5.2, DeckCraft's, DesignCraft's, FigCraft's and
PdfCraft's in 1.5.4), `setup` refuses the differing registration
until `--replace` is passed, then re-registers it and restores the old entry
if the new one cannot be added. SoundCraft before 0.7.0 silently ignores
unknown `mcp` flags, so `preflight` (and with it `setup`, `probe` and
`configure`) refuses a SoundCraft pin older than 0.7.0 or without a readable
version; `setup --app soundcraft --upgrade --replace` moves it. It refuses
DeckCraft before 0.8.0, DesignCraft before 0.9.0, FigCraft before 0.7.0 and
PdfCraft before 0.9.0 the same way, since those releases refuse the flags
and would not start. What a
failure leaves behind: download, checksum, provenance, preflight or probe
failure → nothing changed, `evidence/<app>-candidate.json` kept; failure during
the file replace → the old file (the replace is atomic) and a `reverted`
marker the next run clears; failure between the replace and the lock rewrite
→ `setup --list` shows `completable` and the next `setup` run rewrites the
lock from the marker; a binary that matches neither → `ambiguous`, refused
until you intervene; a failed active probe after promotion →
`promoted_unverified`, installed and pinned but not registered, re-run `setup`
to probe again; a failed registration → binary and pin current,
`partially_registered` in the report, re-run `setup` to register; a failed
`--replace` → the previous registration restored and verified, or
`registration_lost` with the command to re-add it. To roll back, `setup --remove --app <app>` and either install
the earlier release by hand (section 0, with its hash in the lock) or run
`setup --app <app> --upgrade` from a checkout of the Storytold commit whose
manifest pinned it. `setup --remove` never touches the workspace or outputs.

The helpers check paths before operations but do not defeat concurrent malicious
same-user file replacement. Use trusted private parents and OS-enforced isolation.
No launch wrapper continuously enforces hashes after configuration. Preflight
must be repeated before sessions, and read-only executable deployment is advised.
