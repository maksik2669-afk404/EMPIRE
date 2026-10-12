#!/usr/bin/env bash
# Собирает самодостаточную папку для сервера: smeta-server/ (и smeta-server.zip) в корне репозитория.
# Не правьте smeta-server/ руками — правьте smeta/, data/ и deploy/smeta/, потом запустите этот скрипт.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/smeta-server"
rm -rf "$OUT"
mkdir -p "$OUT/data"
cp -r "$ROOT/smeta" "$OUT/smeta"
find "$OUT/smeta" -name "__pycache__" -type d -prune -exec rm -rf {} +
for dir in rates suppliers tax templates materials audit billing; do
  cp -r "$ROOT/data/$dir" "$OUT/data/$dir"
done
cp "$ROOT/deploy/smeta/"{install.sh,update.sh,backup.sh,requirements.txt,env.example,README.md} "$OUT/"
chmod +x "$OUT/"*.sh
printf '%s\n' ".env" ".venv/" "data/smeta.db*" "data/export/" "data/logos/" "data/import/" "__pycache__/" > "$OUT/.gitignore"
(cd "$ROOT" && rm -f smeta-server.zip && python3 -c "
import shutil; shutil.make_archive('smeta-server', 'zip', '.', 'smeta-server')")
echo "Готово: $OUT и $ROOT/smeta-server.zip"
