#!/usr/bin/env bash
# Safe commit + push workflow — pushes ONLY to `origin` (your fork).
#
# Usage:
#   scripts/git-commit-push.sh "feat(agent): add new tool"
#   scripts/git-commit-push.sh               # interactive message
#   scripts/git-commit-push.sh -n "..."      # no-lint (skip ruff/eslint)
#   scripts/git-commit-push.sh -b feat/foo   # create+switch to branch first
#
# Safety:
#   - Refuses to run if `origin` points at infiniflow/ragflow.
#   - Refuses to push any remote other than `origin` (enforced by pre-push hook).
#   - Refuses to commit secrets (.env, *.pem, credentials.*).

set -eu

RED='\033[1;31m'; GRN='\033[1;32m'; YLW='\033[1;33m'; NC='\033[0m'
err() { printf "${RED}[error]${NC} %s\n" "$*" >&2; }
info() { printf "${GRN}[info]${NC} %s\n" "$*"; }
warn() { printf "${YLW}[warn]${NC} %s\n" "$*"; }

# ---------- parse args ----------
skip_lint=0
new_branch=""
message=""
while [ $# -gt 0 ]; do
  case "$1" in
    -n|--no-lint) skip_lint=1; shift ;;
    -b|--branch) new_branch="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,15p' "$0"; exit 0 ;;
    *) message="$1"; shift ;;
  esac
done

# ---------- verify origin ----------
origin_url="$(git remote get-url origin 2>/dev/null || true)"
if [ -z "$origin_url" ]; then
  err "remote 'origin' not configured"; exit 1
fi
case "$origin_url" in
  *infiniflow/ragflow*|*infiniflow/RAGFlow*)
    err "origin points to upstream (infiniflow/ragflow). Fix your remote first:"
    err "  git remote set-url origin https://github.com/<your-fork>/ragflow.git"
    exit 1
    ;;
esac
info "origin → $origin_url"

# ---------- optional: switch to new branch ----------
if [ -n "$new_branch" ]; then
  info "switching to new branch: $new_branch"
  git checkout -b "$new_branch"
fi

current_branch="$(git rev-parse --abbrev-ref HEAD)"
info "current branch: $current_branch"

# ---------- secret scan on staged+unstaged ----------
risky_pattern='(^|/)(\.env($|\.local|\.production)|.*\.pem$|credentials\.[a-z]+$|id_rsa$|id_ed25519$)'
risky_files="$(git status --porcelain | awk '{print $2}' | grep -E "$risky_pattern" || true)"
if [ -n "$risky_files" ]; then
  err "Potential secrets in working tree:"
  printf '%s\n' "$risky_files" >&2
  err "Remove or add to .gitignore before committing."
  exit 1
fi

# ---------- lint (best-effort, non-fatal if tools missing) ----------
if [ "$skip_lint" -eq 0 ]; then
  staged_py="$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)"
  staged_ts="$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx|js|jsx)$' || true)"
  if [ -n "$staged_py" ] && command -v ruff >/dev/null 2>&1; then
    info "ruff check (Python)"
    ruff check $staged_py || { err "ruff failed. Fix errors or rerun with -n"; exit 1; }
  fi
  if [ -n "$staged_ts" ] && [ -f web/package.json ]; then
    info "eslint (web) — skipping in pre-commit; run 'cd web && npm run lint' manually if needed"
  fi
fi

# ---------- stage if nothing staged yet ----------
if git diff --cached --quiet; then
  warn "No staged changes. Staging all modified tracked files (git add -u)."
  git add -u
fi

if git diff --cached --quiet; then
  err "Nothing to commit."
  exit 1
fi

# ---------- commit ----------
if [ -z "$message" ]; then
  printf "Commit message (conventional, e.g. 'fix(api): null guard'): "
  read -r message
fi
if [ -z "$message" ]; then
  err "Empty commit message."; exit 1
fi

info "committing..."
git commit -m "$message"

# ---------- push to origin only ----------
info "pushing to origin/$current_branch ..."
if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  git push origin "HEAD:$current_branch"
else
  git push -u origin "HEAD:$current_branch"
fi

info "done. https://github.com/$(echo "$origin_url" | sed -E 's#.*[:/]([^/]+/[^/.]+)(\.git)?$#\1#')/tree/$current_branch"
