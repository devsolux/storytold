# Repository work

Read ../AGENTS.md for engineering constraints. The canonical runtime guidance is
../skills/craft/SKILL.md; generated plugins/storytold must not be edited by hand.
Work on the main branch only: no feature branches or worktrees for repository
changes, and upstream Craft links point at main, never at a release tag.
No native process or permission grant is implied by opening this repository.

Pull before anything else (`git pull --ff-only origin main`, or `make
github-pull` when local commits are not pushed yet): the daily release workflow
merges its bot/releases pull request into main on its own. Commits go
on main; push main, the `v<version>` tag and the GitHub release happen only on
the operator's explicit request in the current session. Gates before a commit:
make check, make test, make build and make verify-build; a release adds make
release, make test-sdk and make host-validate. After a pin move, recheck the
moved apps' cards at their new tags as AGENTS.md describes.
