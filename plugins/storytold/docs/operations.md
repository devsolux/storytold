# Local setup, operation and rollback

These are operator steps, not actions performed by installing the plugin. Use
non-sensitive fixtures until [acceptance](acceptance.md) passes. The release was
checked with Claude Code, Codex and the optional SDK; one native binary
(PhotoCraft 0.7.0) has passed the discovery probe. See [verification](verification.md).

## 0. Get each app's CLI, not only the desktop app

Every MCP server is an app's command-line tool, `<app>-cli` (for example
`photocraft-cli mcp`). On macOS the `.dmg` and the ArtCraft Launcher install the
GUI only: `PhotoCraft.app` contains no `photocraft-cli`, so a host has nothing to
connect to. Every Craft app publishes the macOS CLI as a separate signed and
notarized release asset, `<app>-cli-<version>-macos-universal.zip`, listed in
that release's `SHA256SUMS.txt`. On Windows the MSI and portable ZIP install
`<app>-cli.exe` next to the app (not on PATH); on Linux the `.deb`/`.rpm` install
`/usr/bin/<app>-cli`. Pin whichever copy you use, preferably the version that
matches your desktop app.

Latest releases on 2026-10-12 (newer ones may exist; re-check the tag commit):

| App | Release | macOS CLI asset | Tag commit (lock `revision`) | File roots in this release |
|---|---|---|---|---|
| PhotoCraft | v0.7.0 | `photocraft-cli-0.7.0-macos-universal.zip` | `79261615956ab21334e49ca1d384390272e647da` | separate read/write |
| VectorCraft | v0.9.0 | `vectorcraft-cli-0.9.0-macos-universal.zip` | `10f1c56a861869936af0027cef14b1cf5d8cf515` | separate read/write |
| FilmCraft | v0.6.0 | `filmcraft-cli-0.6.0-macos-universal.zip` | `2ff3f5e266838700c292a35aaf762e3d4dcef980` | none |
| LightCraft | v0.6.0 | `lightcraft-cli-0.6.0-macos-universal.zip` | `9e6c4c6fc9c7a7f192ce846c00ceb531e0f64dda` | none |
| PdfCraft | v0.6.0 | `pdfcraft-cli-0.6.0-macos-universal.zip` | `53a5880386789fc3531e54f6e6ffdef9a8e41f1a` | one root |
| EffectCraft | v0.8.0 | `effectcraft-cli-0.8.0-macos-universal.zip` | `f953cd2855bf36beffa6a4d608e9bf4b226e9442` | separate read/write |
| DesignCraft | v0.6.0 | `designcraft-cli-0.6.0-macos-universal.zip` | `a9124a0517594ce9872f73637e7b841a4967bcf9` | none |
| GridCraft | v0.5.0 | `gridcraft-cli-0.5.0-macos-universal.zip` | `9f896c1249f40d18bf182199dc03042959be5f3f` | none |
| WordCraft | v0.5.0 | `wordcraft-cli-0.5.0-macos-universal.zip` | `e4b7d155f15a7784197ba34eeea0b54490d70eb2` | none (upstream `main` adds read/write) |
| DeckCraft | v0.5.0 | `deckcraft-cli-0.5.0-macos-universal.zip` | `a98df49b21632d69a3da994d35df1ea91dab41af` | none |
| CADCraft | v0.5.0 | `cadcraft-cli-0.5.0-macos-universal.zip` | `315751e3ec98e708bcc831dd7f80ca0433a2e3d0` | none |
| SoundCraft | v0.5.0 | `soundcraft-cli-0.5.0-macos-universal.zip` | `4410486fc21561a9db0dc33961a2017469127e0d` | none |

On macOS, install one app at a time; set `APP` and `VER` from a table row:

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
download both files from the release page. Storytold never downloads or installs
apps. Apps without file roots can read and write anywhere your user can; see
section 2 before registering them.

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
root. Select only available apps; omission of `--app` means all twelve. Multiple
`--app` flags are allowed for preflight/configure, but a probe targets one app.

FilmCraft, LightCraft, DesignCraft, GridCraft, WordCraft, DeckCraft, CADCraft and
SoundCraft require tested external isolation for sensitive work. For an explicitly
non-sensitive test, `--acknowledge-unconfined` records your decision to proceed;
it does **not** claim isolation. PdfCraft's single root does not make inputs
read-only. Native hash/root checks do not restrict the host's other tools.

## 3. Install the optional conformance client

```bash
cd "$STORYTOLD"
make setup-probe
make test-sdk
```

Only this setup target accesses a package index. Core maintenance is offline.
`requirements-probe.txt` pins the reviewed direct SDK version, not its complete
transitive graph. Capture `pip freeze` after your actual acceptance run and review
updates separately. An unavailable dependency makes the SDK gate fail explicitly;
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
| `desktop_app_only` | Install the CLI release asset (section 0). |
| `cli_not_registered` | Sections 1–5: lock, preflight, probe, configure, register. |
| `registered_command_missing` | The binary moved or was removed; reinstall it, re-run preflight and the probe, regenerate config. |
| `registered` | Start a new host session; check `codex mcp get <app>` or `claude mcp get <app>` and approve the server. |

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

The helpers check paths before operations but do not defeat concurrent malicious
same-user file replacement. Use trusted private parents and OS-enforced isolation.
No launch wrapper continuously enforces hashes after configuration. Preflight
must be repeated before sessions, and read-only executable deployment is advised.
