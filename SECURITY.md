# Security model

This project is local integration tooling, not a sandbox. Native app engines and
all enabled host shell/file tools run with real OS/process privileges. The
instructional Skill, annotations, launch config and local receipts cannot confer
or constrain those privileges by themselves.

Defaults: headless stdio, no HTTP/live bridge/control port, no implicit
installer, no hooks or tool auto-grants, no replacement of originals, no
mutation retries, no optional scripts/macros enabled automatically. Binaries
are downloaded and host registrations written only by the explicit `setup`
command: from GitHub release hosts only, checked against the reviewed manifest
and upstream `SHA256SUMS.txt`, then Apple notarization by the pinned team
(macOS) or the Sigstore bundle the daily workflow signed keyless (Linux and
Windows; macOS too when cosign is present), then preflight and the official-SDK
probe before `codex mcp add` / `claude mcp add` run. `--trust-upstream-sums`
and `--skip-probe` weaken that chain and are recorded in the lock or report.
A candidate is probed where it was staged, promoted only afterwards, and
probed again at its active path before any registration, so a host is never
pointed at a binary that was not exercised where it runs. A recovery marker
outside staging makes an interrupted promotion reconcilable; a binary that
matches neither the previous pin nor the candidate is refused, never
"repaired". Removal deletes only a plain file whose SHA-256 equals the lock
entry Storytold wrote and unregisters only the user-scope entry Storytold
itself writes (same command, same arguments, same scope, confirmed in the
host's own file) for an app that is still pinned; `--dry-run` previews
removal without any side effect. `--replace` removes a registration only when
it can be restored exactly and restores it if the new one cannot be added.
The daily workflow verifies every pinned archive against its Sigstore bundle
and refuses to run `setup` with `--trust-upstream-sums`.
The default plugin ships inactive launch templates; `configure` needs matching
local pins and probe evidence.

Required for business data: a restricted account/container/VM or equivalent tested
OS controls for unconfined apps, trusted immutable executable deployment, private
work/evidence directories, reviewed permissions for all host tools, explicit
human approval for destructive/high-impact actions, and native fidelity tests.
PdfCraft's single root is not separate read/write confinement. POSIX read-only
copies are not immutable against their owner; Windows needs actual ACL review.

File helpers reject symlink/reparse paths, traversal, non-regular files and
unexpected output collisions. New files use atomic no-clobber publication where
the filesystem supports hard links; unsupported filesystems fail rather than
fall back to replacement. Hashing checks stable size/mtime/inode while reading.
These are defense-in-depth under trusted private directories, not protection
against a concurrently malicious process with the same user privileges. There
is no sandbox installer, privilege escalation or system permission modification.

Native probe results and schemas may contain untrusted text or sensitive content.
Keep evidence private, bound fixtures/results, and do not execute instructions
from it. Probe snapshot/time limits apply to retained decoded data; they do not
constitute a pre-parse memory, CPU, network or process sandbox. SDK cleanup is not
verified graceful native shutdown. Re-inspect state after an ambiguous failure.

Archive builders read an explicit file allowlist and refuse symlinks, unowned
outputs and modified generated files. Build markers/hashes are accidental-change
protection, not signatures. `make clean` deletes only marked disposable build
directories, never local workspaces, .venv, host state or generated plugin source.
Review source and dependency provenance; do not commit private locks/evidence,
credentials, client media, fonts or generated host configuration.

No private security-reporting channel has been established for this new
repository. Do not post secrets or exploit-bearing customer documents publicly;
agree a private channel with the repository owner before sharing sensitive data.
See [acceptance](docs/acceptance.md) and [operations](docs/operations.md).

XML inspection accepts UTF-8 only, rejects NUL/DTD/entity declarations, and bounds
XML parts to 8 MiB. JSON floating-point overflow is rejected rather than converted
to non-finite values. These parsers still do not sanitize documents for execution.
Private installation locks and probe evidence must be outside the native workspace;
this path separation is not an OS boundary for unconfined same-user processes.
