# File safety and authority

Use a dedicated private working directory with inputs/, outputs/ and receipts/.
The deterministic workspace initializer refuses to adopt an existing directory;
staging writes a new read-only copy and records the source/copy hash. POSIX file
modes deter mistakes but are not immutable against the owning user. Windows
requires a reviewed ACL. No script in this plugin claims to create an OS sandbox.

PhotoCraft, VectorCraft, EffectCraft and WordCraft have source-documented distinct
read/write roots. PdfCraft has one root that includes both input and output paths.
FilmCraft, LightCraft, DesignCraft, GridCraft, DeckCraft, CADCraft, SoundCraft and
FigCraft must be treated as OS-user-wide unless the pinned binary proves otherwise.
External OS isolation is required when confidential data or strong confinement
matters. Other host shell/file tools are not restricted by native MCP roots.

Do not enable control ports, --connect, --bridge, --attach, scripts, macros, move-import or
unrelated-target replacement automatically. Keep one writer per artifact/library.
Do not remove lock files or bypass host approvals. The default Skill has no
allowed-tools grant, hooks, automatic host enablement or hidden execution step.
The explicit `storytold.py setup` command is the only helper that downloads a
binary or writes a host registration; it does so through the host's own CLI,
only when an operator runs it, and the Skill may propose it but never run it unasked.

After a mutating timeout, state is unknown. Preserve files and inspect using
native state/job APIs. An existing output may be partial. A batch may have applied
some earlier steps. No retry is safe merely because a client did not receive a
response. Stop at the last verified checkpoint rather than retrying silently.

Verify actual output bytes and reopen in the app or an independent parser. Native
warnings, including offline media, missing fonts, overset text and unsupported
formats, must remain visible. A rendered black PDF rectangle does not establish
redaction. A hash establishes byte equality, not truth, review, safe active content
or visual quality. Inspect all relevant pages/slides/frames, not only a thumbnail.

Source basis: the supplied Native MCP Project Plan, sections 7–8, and the supplied
CLI/MCP Integration Reference, app-specific security notes. The repository's
[online source ledger](../../../docs/source-ledger.md) distinguishes fresh review
from inherited documentation. Validate all claims against local pinned binaries.
