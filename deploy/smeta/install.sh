#!/usr/bin/env bash
# Установка Сметчика на Ubuntu 22.04 / 24.04 одной командой:  sudo bash install.sh
# Повторный запуск безопасен: ключи и база сохраняются, код обновляется.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE=smeta-bot
ENV_FILE="$APP_DIR/.env"
say() { printf '\n\033[1;34m▶ %s\033[0m\n' "$*"; }
ok()  { printf '\033[1;32m✔ %s\033[0m\n' "$*"; }
warn(){ printf '\033[1;33m⚠ %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "Запустите от root: sudo bash install.sh"; exit 1; }

get_env() { grep -E "^$1=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- || true; }
set_env() {
  if grep -qE "^$1=" "$ENV_FILE"; then
    python3 - "$ENV_FILE" "$1" "$2" <<'PY'
import sys
path, key, value = sys.argv[1:]
lines = open(path, encoding="utf-8").read().splitlines()
lines = [f"{key}={value}" if l.startswith(f"{key}=") else l for l in lines]
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
  else
    echo "$1=$2" >> "$ENV_FILE"
  fi
}

say "1/6 Системные пакеты"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip fonts-dejavu-core curl ca-certificates >/dev/null
ok "Python $(python3 -V | cut -d' ' -f2), шрифты для PDF"

say "2/6 Библиотеки"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
ok "Установлены"

say "3/6 Ключи"
[ -f "$ENV_FILE" ] || cp "$APP_DIR/env.example" "$ENV_FILE"
chmod 600 "$ENV_FILE"

TOKEN="$(get_env SMETA_BOT_TOKEN)"
while true; do
  if [ -z "$TOKEN" ]; then
    read -rp "Токен бота от @BotFather: " TOKEN
  fi
  NAME="$(curl -s --max-time 15 "https://api.telegram.org/bot${TOKEN}/getMe" | python3 -c 'import json,sys
try:
  d=json.load(sys.stdin); print(d["result"]["username"] if d.get("ok") else "")
except Exception: print("")')"
  if [ -n "$NAME" ]; then ok "Бот @$NAME"; break; fi
  if [ -n "$(get_env TELEGRAM_PROXY)" ]; then warn "Проверить токен не удалось (сервер ходит в Телеграм через прокси) — продолжаю"; break; fi
  warn "Телеграм не принял токен или недоступен с сервера."
  read -rp "Ввести токен заново? [Y/n] " again
  [[ "${again:-y}" =~ ^[Nn] ]] && break
  TOKEN=""
done
set_env SMETA_BOT_TOKEN "$TOKEN"

if [ -z "$(get_env SMETA_ADMIN_IDS)" ]; then
  read -rp "Ваш Telegram ID (узнать у @userinfobot, Enter — пропустить): " ADMIN
  [ -n "${ADMIN:-}" ] && set_env SMETA_ADMIN_IDS "$ADMIN"
fi
if [ -z "$(get_env SMETA_PAYMENT_TOKEN)" ]; then
  echo "Оплата: токен провайдера из @BotFather → Payments (ЮKassa и др.)."
  read -rp "Токен оплаты (Enter — принимать Telegram Stars): " PAY
  [ -n "${PAY:-}" ] && set_env SMETA_PAYMENT_TOKEN "$PAY"
fi

say "4/6 Мини-апп (нужен HTTPS)"
URL="$(get_env SMETA_WEBAPP_URL)"
if [ -z "$URL" ]; then
  IP="$(curl -s --max-time 10 https://api.ipify.org || hostname -I | awk '{print $1}')"
  echo "  1) У меня есть домен, направленный на этот сервер ($IP)"
  echo "  2) Домена нет — использовать бесплатный адрес ${IP//./-}.sslip.io"
  echo "  3) Без мини-аппа (только бот)"
  read -rp "Выбор [2]: " CHOICE
  case "${CHOICE:-2}" in
    1) read -rp "Домен (например smeta.example.ru): " DOMAIN ;;
    2) DOMAIN="${IP//./-}.sslip.io" ;;
    *) DOMAIN="" ;;
  esac
else
  DOMAIN="${URL#https://}"; DOMAIN="${DOMAIN%%/*}"
fi

if [ -n "${DOMAIN:-}" ]; then
  if ! command -v caddy >/dev/null; then
    apt-get install -y -qq caddy >/dev/null 2>&1 || {
      apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https gnupg >/dev/null
      curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
      curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
      apt-get update -qq && apt-get install -y -qq caddy >/dev/null
    }
  fi
  PORT="$(get_env SMETA_WEBAPP_PORT)"; PORT="${PORT:-8080}"
  cat > /etc/caddy/Caddyfile <<CADDY
$DOMAIN {
    encode gzip
    reverse_proxy 127.0.0.1:$PORT
}
CADDY
  if command -v ufw >/dev/null && ufw status | grep -q active; then ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null; fi
  systemctl enable --now caddy >/dev/null 2>&1 || true
  systemctl reload caddy || systemctl restart caddy
  set_env SMETA_WEBAPP_URL "https://$DOMAIN"
  ok "Мини-апп: https://$DOMAIN (сертификат Caddy получит сам за ~1 минуту; порты 80 и 443 должны быть открыты)"
else
  set_env SMETA_WEBAPP_URL ""
  ok "Мини-апп выключен — можно включить позже, запустив install.sh ещё раз"
fi

say "5/6 Автозапуск"
cat > /etc/systemd/system/$SERVICE.service <<UNIT
[Unit]
Description=Smeta bot (Сметчик)
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$APP_DIR/.venv/bin/python -m smeta.bot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now $SERVICE >/dev/null
systemctl restart $SERVICE

say "6/6 Ежедневный бэкап"
cat > /etc/cron.daily/smeta-backup <<CRON
#!/bin/sh
bash "$APP_DIR/backup.sh" >/dev/null 2>&1
CRON
chmod +x /etc/cron.daily/smeta-backup "$APP_DIR/backup.sh" "$APP_DIR/update.sh"
ok "Каждую ночь — в /root/smeta-backups (хранится 14 копий)"

sleep 4
if systemctl is-active --quiet $SERVICE; then
  ok "Сметчик запущен. Откройте бота в Телеграме и нажмите /start"
else
  warn "Бот не запустился. Последние строки лога:"
  journalctl -u $SERVICE -n 30 --no-pager
fi
echo
echo "Лог:         journalctl -u $SERVICE -f"
echo "Перезапуск:  systemctl restart $SERVICE"
echo "Обновление:  положите новую папку поверх и запустите  sudo bash update.sh"
