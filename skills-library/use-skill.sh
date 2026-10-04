#!/usr/bin/env bash
# Подключает навыки из библиотеки в .claude/skills проекта (Claude Code подхватит их в следующей сессии).
#   skills-library/use-skill.sh prd funnel-analysis   — подключить (русская версия)
#   skills-library/use-skill.sh --en prd              — подключить английскую версию
#   skills-library/use-skill.sh --remove prd          — отключить
#   skills-library/use-skill.sh --list                — что подключено сейчас
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIB="$ROOT/skills-library/pdm/skills"
DEST="$ROOT/.claude/skills"
FILE="SKILL.md"
case "${1:-}" in
  ""|-h|--help) sed -n '2,6p' "$0"; exit 0 ;;
  --list) ls -1 "$DEST" 2>/dev/null || echo "(ничего не подключено)"; exit 0 ;;
  --remove) shift; for n in "$@"; do rm -rf "${DEST:?}/$n"; echo "отключён: $n"; done; exit 0 ;;
  --en) FILE="SKILL.en.md"; shift ;;
esac
for n in "$@"; do
  src="$LIB/$n/$FILE"
  [ -f "$src" ] || { echo "нет навыка «$n» — список в skills-library/pdm/INDEX.md" >&2; exit 1; }
  mkdir -p "$DEST/$n"
  cp "$src" "$DEST/$n/SKILL.md"
  echo "подключён: $n"
done
