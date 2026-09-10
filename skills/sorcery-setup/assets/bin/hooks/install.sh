#!/bin/sh
# Enable this clone's wiki git hooks.
#
# The hooks live in a version-controlled directory (wiki/bin/hooks/), but git only uses them when
# this clone's local config points at them. core.hooksPath lives in .git/config, which is NOT
# version-controlled — so every clone must run this once, or git silently falls back to
# .git/hooks and none of the wiki gates fire.
#
# Usage:  sh wiki/bin/hooks/install.sh
# Verify: git hook run pre-commit      (or: git config --get core.hooksPath)
set -eu

HOOKS_REL="${1:-wiki/bin/hooks}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "install.sh: not inside a git repository" >&2
  exit 1
}
cd "$ROOT"

if [ ! -d "$HOOKS_REL" ]; then
  echo "install.sh: $HOOKS_REL not found under $ROOT" >&2
  exit 1
fi

git config core.hooksPath "$HOOKS_REL"
chmod +x "$HOOKS_REL"/* 2>/dev/null || true

echo "wiki hooks enabled"
echo "  repo           : $ROOT"
echo "  core.hooksPath : $(git config --get core.hooksPath)"
echo "  hooks          : $(ls "$HOOKS_REL" | tr '\n' ' ')"
echo
echo "verify with: git hook run pre-commit"
