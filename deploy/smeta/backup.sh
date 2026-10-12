#!/usr/bin/env bash
# Бэкап базы, логотипов и ключей в /root/smeta-backups. Восстановить: распаковать архив в папку бота.
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST=/root/smeta-backups
mkdir -p "$DEST"
STAMP="$(date +%Y-%m-%d_%H%M)"
cd "$APP_DIR"
FILES=".env"
[ -f data/smeta.db ] && { sqlite3 data/smeta.db ".backup data/smeta.backup.db" 2>/dev/null || cp data/smeta.db data/smeta.backup.db; FILES="$FILES data/smeta.backup.db"; }
[ -d data/logos ] && FILES="$FILES data/logos"
tar -czf "$DEST/smeta_$STAMP.tar.gz" $FILES
rm -f data/smeta.backup.db
ls -1t "$DEST"/smeta_*.tar.gz | tail -n +15 | xargs -r rm -f
echo "✔ $DEST/smeta_$STAMP.tar.gz"
