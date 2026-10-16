# Offline defaults; explicit operator targets for setup and installation.
SHELL := /bin/sh
.SHELLFLAGS := -eu -c
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= $(if $(wildcard .venv/bin/python),$(CURDIR)/.venv/bin/python,python3)
export PYTHONDONTWRITEBYTECODE := 1
PLUGIN := storytold@devsolux-storytold
REPOSITORY := devsolux/storytold

.PHONY: help setup setup-probe doctor refresh-releases sign-releases setup-confined check lint test test-sdk build verify-build publish-check package source release clean host-validate install-claude install-codex install-claude-local install-codex-local

help: ## Show maintenance targets; no tools installed or started
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-23s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Explicitly create a local .venv (core has no third-party dependencies)
	@if [ -L .venv ] || { [ -e .venv ] && [ ! -f .venv/pyvenv.cfg ]; }; then \
		echo 'Refusing to adopt an unrecognized or symlinked .venv' >&2; exit 1; fi
	python3 -m venv .venv

setup-probe: setup ## Explicit network opt-in: install the reviewed optional MCP client SDK
	.venv/bin/python -m pip install -r requirements-probe.txt

doctor: ## Report installed capabilities without starting hosts or native apps
	"$(PYTHON)" storytold.py doctor

refresh-releases: ## Maintainer network step: rewrite config/releases.json from the latest GitHub releases, then review the diff
	"$(PYTHON)" scripts/refresh_releases.py

sign-releases: ## Workflow step: download pinned CLIs and sign them keyless with cosign into config/signatures.json
	@command -v cosign >/dev/null || { echo "cosign is required (https://docs.sigstore.dev/cosign/system_config/installation/)" >&2; exit 1; }
	"$(PYTHON)" scripts/sign_releases.py

setup-confined: ## Explicit host/app-state change: install, pin, probe and register the six root-confined apps
	"$(PYTHON)" storytold.py setup --app photocraft --app vectorcraft --app effectcraft --app wordcraft --app soundcraft --app pdfcraft

check: ## Validate source, links, identities, catalog, examples and inactive packaging
	"$(PYTHON)" scripts/check.py

lint: check ## Alias for the offline source checks

test: ## Run all core tests in an isolated source copy; no network/native binaries
	"$(PYTHON)" scripts/test.py

test-sdk: ## Explicit optional-SDK test with synthetic stdio fixture, not Craft apps
	"$(PYTHON)" scripts/test_sdk.py

build: ## Generate the shared plugin from allowlisted canonical files
	"$(PYTHON)" scripts/build.py build

verify-build: ## Read-only generated-runtime drift check
	"$(PYTHON)" scripts/build.py check

publish-check: ## Offline gate before any push: source checks and committed-plugin drift
	"$(PYTHON)" scripts/check.py >/dev/null
	"$(PYTHON)" scripts/build.py check >/dev/null

package: check build ## Create deterministic plugin ZIP and checksum
	"$(PYTHON)" scripts/build.py plugin

source: check build ## Create complete source ZIP with generated plugin and checksum
	"$(PYTHON)" scripts/build.py source

release: ## Ordered core verification and packages; no publish/native acceptance claim
	$(MAKE) check
	$(MAKE) test
	$(MAKE) build
	$(MAKE) verify-build
	"$(PYTHON)" scripts/build.py plugin
	"$(PYTHON)" scripts/build.py source

clean: ## Remove only marked .build/ and dist/; preserve workspaces and .venv
	"$(PYTHON)" scripts/build.py clean

host-validate: build ## Explicit installed-Claude manifest validation (no app binaries)
	@command -v claude >/dev/null || { echo "Claude CLI is required" >&2; exit 1; }
	claude plugin validate --strict .
	claude plugin validate --strict ./plugins/storytold

install-claude: ## Explicit host-state change: install the published Git marketplace
	@command -v claude >/dev/null || { echo "Claude CLI is required" >&2; exit 1; }
	claude plugin marketplace add https://github.com/$(REPOSITORY)
	claude plugin install $(PLUGIN)

install-codex: ## Explicit host-state change: install the published Git marketplace
	@command -v codex >/dev/null || { echo "Codex CLI is required" >&2; exit 1; }
	codex plugin marketplace add $(REPOSITORY)
	codex plugin add $(PLUGIN)

install-claude-local: build ## Explicit host-state change: install the local marketplace
	@command -v claude >/dev/null || { echo "Claude CLI is required" >&2; exit 1; }
	claude plugin marketplace add "$(CURDIR)"
	claude plugin install $(PLUGIN)

install-codex-local: build ## Explicit host-state change: install the local marketplace
	@command -v codex >/dev/null || { echo "Codex CLI is required" >&2; exit 1; }
	codex plugin marketplace add "$(CURDIR)"
	codex plugin add $(PLUGIN)


# -----------------------------------------------------------------------------
# GitHub — CLI auth, local repo init, gh repo create, push (override as needed)
# These maintainer targets contact GitHub or change git state. They run only when
# invoked by name; help, check, build, verify-build, package and release never
# call them. github-push and github-bootstrap run publish-check first so a stale
# or invalid marketplace is never pushed.
# Existing private repo: gh repo edit devsolux/storytold --visibility public --accept-visibility-change-consequences
# -----------------------------------------------------------------------------

# Must match project.json "repository"; the marketplace installs from this repo.
GITHUB_ORG  ?= devsolux
GITHUB_REPO ?= storytold
GITHUB_FULL ?= $(GITHUB_ORG)/$(GITHUB_REPO)
# Public, so `claude/codex plugin marketplace add devsolux/storytold` works without credentials.
GITHUB_VISIBILITY ?= public
GITHUB_DESCRIPTION ?= Claude Code & Codex plugin for the open-source ArtCraft Craft App Suite: one craft Skill drives 13 local, headless Craft MCP apps (photo, vector, video, RAW, PDF, layout, sheets, docs, slides, CAD, audio, motion, interface design) with staged copies and verified exports.
# Comma-separated; GitHub allows at most 20 lowercase topics.
GITHUB_TOPICS ?= claude-code,claude-code-plugin,codex,codex-plugin,mcp,model-context-protocol,agent-skills,ai-agents,artcraft,craft-apps,creative-tools,local-first,headless,plugin-marketplace,python,image-editing,video-editing,pdf,cad,audio
# Fallback if you add origin by hand instead of gh repo create:
GIT_REMOTE_SSH ?= git@github.com:$(GITHUB_FULL).git

.PHONY: git-check github-check github-auth git-init git-main github-initial-commit \
	github-repo-create github-metadata github-remote-ssh github-verify github-pull github-push github-bootstrap \
	github-allow-action github-run-workflow

git-check:
	@command -v git >/dev/null 2>&1 || { echo "error: git is required"; exit 1; }

github-check: git-check
	@command -v gh >/dev/null 2>&1 || { echo "error: GitHub CLI (gh) is required — https://cli.github.com"; exit 1; }

github-auth: github-check ## Interactive: authenticate gh with GitHub (once per machine)
	gh auth login

git-init: ## Local git state: initialize a repository on branch main if none exists
	@if test -d .git; then \
		echo "Git repository already initialized (.git exists)."; \
	else \
		git init -b main; \
		echo "Initialized empty Git repository (branch: main)."; \
	fi

# Ensure current branch is named main (no-op if already main)
git-main:
	@git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repository (run: make git-init)"; exit 1; }
	@BRANCH=$$(git symbolic-ref --short HEAD 2>/dev/null || true); \
	if [ -z "$$BRANCH" ]; then \
		git symbolic-ref HEAD refs/heads/main && echo "Default branch set to main (no commits yet)."; \
	elif [ "$$BRANCH" != "main" ]; then \
		git branch -M main && echo "Renamed branch to main."; \
	else \
		echo "Already on branch main."; \
	fi

# First commit only when there is no history yet
github-initial-commit:
	@git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repository (run: make git-init)"; exit 1; }
	@if git rev-parse HEAD >/dev/null 2>&1; then \
		echo "Repository already has commits; skipping initial commit."; \
	else \
		git add -A && \
		if git diff --cached --quiet; then \
			echo "Nothing staged to commit; add files or adjust .gitignore, then commit manually."; \
			exit 1; \
		fi && \
		git commit -m "Initial commit" && \
		echo "Created initial commit."; \
	fi

# Skips creation when origin already exists.
github-repo-create: github-check ## Publishes: create the public GitHub repo, set origin and push main
	@if git remote get-url origin >/dev/null 2>&1; then \
		echo "Remote origin already exists:"; \
		git remote -v; \
		echo "Skipping gh repo create. Run: make github-push"; \
	else \
		gh repo create $(GITHUB_FULL) --$(GITHUB_VISIBILITY) --description "$(GITHUB_DESCRIPTION)" \
			--source=. --remote=origin --push && \
		$(MAKE) github-metadata; \
	fi

github-metadata: github-check ## Publishes: set the GitHub description and topics on the existing repo
	gh repo edit $(GITHUB_FULL) --description "$(GITHUB_DESCRIPTION)" --add-topic "$(GITHUB_TOPICS)"

# Optional: add SSH remote by hand (only if origin is missing)
github-remote-ssh: github-check
	@if git remote get-url origin >/dev/null 2>&1; then \
		echo "Remote origin already set:"; git remote -v; exit 1; \
	fi
	git remote add origin "$(GIT_REMOTE_SSH)"
	@echo "Added origin $(GIT_REMOTE_SSH) — run: git push -u origin main"

github-verify: ## Show git remotes and branches
	@echo "=== git remote -v ==="
	@git remote -v
	@echo ""
	@echo "=== git branch ==="
	@git branch -a

# Fetch origin/main and update the local main branch only when GitHub has a newer commit.
# - Same commit: no-op.
# - Local commits ahead of origin/main: no-op; use github-push when ready.
# - Remote commits ahead of local main: fast-forward only.
# - Diverged history or a dirty worktree during an update: stop without changing files.
# The daily release workflow merges into main on its own, so local and remote
# main diverge routinely; the fix is always a rebase of the local commits.
REBASE_HELP := "error: rebase stopped on a conflict. If it is plugins/storytold/.storytold-build.json: run make build, git add plugins/storytold, git rebase --continue; otherwise resolve, git add, git rebase --continue. Then rerun this target. To abandon: git rebase --abort"

github-pull: git-check ## Bring main up to date with origin/main (fast-forward, or rebase local commits onto it)
	@git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repository"; exit 1; }
	@git remote get-url origin >/dev/null 2>&1 || { echo "error: no origin remote (run: make github-repo-create or github-remote-ssh)"; exit 1; }
	@BRANCH=$$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true); \
	if [ "$$BRANCH" != "main" ]; then \
		echo "error: github-pull expects branch main (current: $${BRANCH:-detached})"; \
		exit 1; \
	fi
	@# Never break a lock that a running git process may still own.
	@if test -f .git/index.lock; then \
		echo "error: .git/index.lock exists; finish or stop the other git process, then remove a verified stale lock yourself"; \
		exit 1; \
	fi
	@git fetch origin main
	@REMOTE=$$(git rev-parse --verify refs/remotes/origin/main 2>/dev/null || true); \
	LOCAL=$$(git rev-parse --verify HEAD 2>/dev/null || true); \
	if [ -z "$$REMOTE" ]; then \
		echo "No commit found on origin/main; nothing to pull."; \
	elif [ -z "$$LOCAL" ]; then \
		if [ -n "$$(git status --porcelain)" ]; then \
			echo "error: local repository has no commit and the worktree is not clean; refusing to overwrite files"; \
			exit 1; \
		fi; \
		git checkout -B main origin/main && \
		echo "Updated main to remote commit $$REMOTE."; \
	elif [ "$$LOCAL" = "$$REMOTE" ]; then \
		echo "Already up to date ($$LOCAL); no committed change on GitHub."; \
	elif git merge-base --is-ancestor "$$REMOTE" "$$LOCAL"; then \
		echo "Local main contains origin/main and has committed changes; nothing to pull."; \
	elif git merge-base --is-ancestor "$$LOCAL" "$$REMOTE"; then \
		if [ -n "$$(git status --porcelain)" ]; then \
			echo "error: origin/main has a newer commit, but the worktree is not clean; commit or stash local changes first"; \
			exit 1; \
		fi; \
		git merge --ff-only origin/main && \
		echo "Updated main: $$LOCAL -> $$REMOTE"; \
	else \
		if [ -n "$$(git status --porcelain)" ]; then \
			echo "error: local main and origin/main have diverged and the worktree is not clean; commit or stash local changes first"; \
			exit 1; \
		fi; \
		git rebase origin/main || { echo $(REBASE_HELP); exit 1; }; \
		echo "Rebased local commits onto origin/main ($$REMOTE)."; \
	fi

# Stages all changes, commits with message = short local datetime (YYYYMMDD-HHMMSS) if needed, then pushes.
# Custom message: make github-push GITHUB_COMMIT_MSG='wip'
GITHUB_COMMIT_MSG ?=

# Refuses to push a stale committed marketplace, which would break public installs.
# Order: commit local changes → pull --rebase onto origin/main → re-check the
# generated plugin → push. Equivalent to: git pull --rebase origin main && git push origin main
github-push: github-check publish-check ## Publishes: commit all changes (timestamp message), pull --rebase onto origin/main, push main
	@git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repository"; exit 1; }
	@git remote get-url origin >/dev/null 2>&1 || { echo "error: no origin remote (run: make github-repo-create or github-remote-ssh)"; exit 1; }
	@# Never break a lock that a running git process may still own.
	@if test -f .git/index.lock; then \
		echo "error: .git/index.lock exists; finish or stop the other git process, then remove a verified stale lock yourself"; \
		exit 1; \
	fi
	@STAMP=$$(date +%Y%m%d-%H%M%S); \
	git add -A; \
	if git diff --cached --quiet; then \
		echo "No changes to commit; pushing."; \
	else \
		if [ -n "$(GITHUB_COMMIT_MSG)" ]; then \
			git commit -m "$(GITHUB_COMMIT_MSG)" && echo "Committed (custom message)."; \
		else \
			git commit -m "$$STAMP" && echo "Committed: $$STAMP"; \
		fi; \
	fi
	@git pull --rebase origin main || { echo $(REBASE_HELP); exit 1; }
	@"$(PYTHON)" scripts/build.py check >/dev/null || { echo "error: the rebase changed generated plugin inputs; run make build, commit, then make github-push again"; exit 1; }
	git push -u origin main

# Full flow (sequential — safe with make -j): check → init → main → commit → gh create → verify
github-bootstrap: ## Publishes: validate, git init, first commit, create public repo, push
	@$(MAKE) github-check
	@$(MAKE) publish-check
	@$(MAKE) git-init
	@$(MAKE) git-main
	@$(MAKE) github-initial-commit
	@$(MAKE) github-repo-create
	@$(MAKE) github-verify

github-allow-action: github-check ## Repo setting: let the daily workflow open pull requests with github.token
	gh api -X PUT repos/$(GITHUB_FULL)/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true

github-run-workflow: github-check ## Trigger the daily release refresh now (refresh, sign, three-OS verify, PR, auto-merge if enabled)
	gh workflow run releases.yml --repo $(GITHUB_FULL)