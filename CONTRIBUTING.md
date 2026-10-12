# Contributing

Read AGENTS.md and docs/architecture.md first. Keep the native plan authoritative.
Do not add a gateway, secondary model, GUI automation, auto-grants or command
registry. Changes to native flags require source review and new local binary
acceptance, not just a matching unit test.

Run make check, make test, make build, make verify-build, make package and make
source. Every core test is discovered automatically in an isolated source copy.
No native app, host install, live model or network call belongs in the core suite.
The separate make test-sdk gate needs the pinned optional SDK and exercises a
synthetic stdio fixture. Actual app/host gates remain in docs/acceptance.md.

Register new canonical files in packaging/files.json deliberately; the build does
not sweep arbitrary working directories into a release. Edit source, not the
generated plugins/storytold directory. An ownership mismatch means preserve and
review the local edits; never weaken the check or delete them automatically.

A version change belongs in packaging/project.json. Update the changelog,
verification report and source ledger; keep original source documents unchanged.
Then run make release and, with the Claude CLI installed, make host-validate.

Builds and tests never commit, push or install. Publishing is explicit: the
make github-* targets (make help lists them) commit and push only when invoked
by name, after make publish-check confirms the committed plugin matches source.
Public installs read plugins/storytold from the default branch, so push the
regenerated plugin together with the source change that produced it.
