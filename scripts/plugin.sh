#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
PYTHON="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON" ]] || { echo "Python 3이 필요합니다." >&2; exit 1; }
PLUGIN_ID="$($PYTHON -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$ROOT/plugin.json")"
VERSION_MANAGER="$(find "$ROOT/skills" -path '*-skill-versioning/scripts/skill_versions.py' -print -quit)"
SKIP_CODEX=0
SKIP_CLAUDE=0
SKIP_ANTIGRAVITY=0

usage() {
  cat <<EOF
Usage: bash scripts/plugin.sh <install|setup|update|repair|test|status> [options]

감지된 Codex, Claude Code, Antigravity에 $PLUGIN_ID 플러그인을 관리합니다.
Options: --skip-codex --skip-claude --skip-antigravity
EOF
}

parse_options() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-codex) SKIP_CODEX=1 ;;
      --skip-claude) SKIP_CLAUDE=1 ;;
      --skip-antigravity) SKIP_ANTIGRAVITY=1 ;;
      *) echo "알 수 없는 옵션입니다: $1" >&2; exit 2 ;;
    esac
    shift
  done
}

sync_agents() {
  local detected=0
  if [[ "$SKIP_CODEX" -eq 0 ]] && command -v codex >/dev/null 2>&1; then
    detected=1
    codex plugin marketplace add "$ROOT" --json || codex plugin marketplace upgrade "$PLUGIN_ID"
    codex plugin add "$PLUGIN_ID@$PLUGIN_ID" --json
  fi
  if [[ "$SKIP_CLAUDE" -eq 0 ]] && command -v claude >/dev/null 2>&1; then
    detected=1
    claude plugin marketplace add "$ROOT" --scope user || claude plugin marketplace update "$PLUGIN_ID"
    claude plugin install "$PLUGIN_ID@$PLUGIN_ID" --scope user --json -y || claude plugin update "$PLUGIN_ID@$PLUGIN_ID" --scope user --json -y
  fi
  if [[ "$SKIP_ANTIGRAVITY" -eq 0 ]] && command -v agy >/dev/null 2>&1; then
    detected=1
    "$PYTHON" "$ROOT/scripts/build_antigravity_plugin.py"
    agy plugin install "$ROOT/.build/antigravity/$PLUGIN_ID"
  fi
  [[ "$detected" -eq 1 ]] || echo "설치 가능한 에이전트를 찾지 못했습니다. 필요한 CLI를 설치한 뒤 repair를 실행하세요."
}

run_test() {
  bash -n "$ROOT/scripts/plugin.sh"
  "$PYTHON" "$VERSION_MANAGER" check --root "$ROOT"
  "$PYTHON" "$ROOT/scripts/build_antigravity_plugin.py"
  "$PYTHON" -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
  if command -v claude >/dev/null 2>&1; then claude plugin validate "$ROOT"; fi
  git -C "$ROOT" diff --check
}

show_status() {
  echo "$PLUGIN_ID"
  git -C "$ROOT" status --short --branch
  for agent in codex claude agy; do
    if command -v "$agent" >/dev/null 2>&1; then echo "$agent: 사용 가능"; else echo "$agent: 설치되지 않음"; fi
  done
}

command_name="${1:-}"
if [[ -z "$command_name" || "$command_name" == "-h" || "$command_name" == "--help" ]]; then usage; exit 0; fi
shift
case "$command_name" in
  install|setup|repair) parse_options "$@"; sync_agents ;;
  update) parse_options "$@"; git -C "$ROOT" pull --ff-only; sync_agents ;;
  test) [[ $# -eq 0 ]] || { echo "test는 옵션을 받지 않습니다." >&2; exit 2; }; run_test ;;
  status) [[ $# -eq 0 ]] || { echo "status는 옵션을 받지 않습니다." >&2; exit 2; }; show_status ;;
  *) echo "알 수 없는 명령입니다: $command_name" >&2; usage >&2; exit 2 ;;
esac
