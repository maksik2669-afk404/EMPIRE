#!/usr/bin/env bash
# Обновление после замены файлов: зависимости + перезапуск. База, ключи и логотипы не трогаются.
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$APP_DIR/backup.sh"
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
systemctl restart smeta-bot
sleep 3
systemctl is-active --quiet smeta-bot && echo "✔ Обновлено и запущено" || journalctl -u smeta-bot -n 30 --no-pager
