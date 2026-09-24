#!/usr/bin/env bash
# EMPIRE Reply — установка на чистый сервер Ubuntu/Debian одной командой:
#   sudo bash deploy/install.sh
# Повторный запуск = обновление: код обновляется, .env и база сохраняются.
# Без Docker: Docker Hub из РФ работает нестабильно, а PyPI доступен.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/empire}"
SERVICE="empire-bot"
RUN_USER="empire"
NO_SERVICE="${NO_SERVICE:-0}"   # 1 = без apt/systemd (для проверки скрипта)
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[x] %s\033[0m\n' "$*"; exit 1; }

if [ "$NO_SERVICE" != "1" ]; then
  [ "$(id -u)" -eq 0 ] || die "Запустите через sudo: sudo bash deploy/install.sh"
  command -v apt-get >/dev/null || die "Нужен Ubuntu/Debian (apt-get)."
  say "Устанавливаю системные пакеты"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq python3 python3-venv python3-pip curl ca-certificates >/dev/null
fi

python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || die "Нужен Python 3.10+ (Ubuntu 22.04 или новее)."

say "Копирую приложение в $APP_DIR"
mkdir -p "$APP_DIR/data"
rm -rf "$APP_DIR/app"
cp -r "$SRC_DIR/app" "$SRC_DIR/requirements.txt" "$APP_DIR/"

say "Ставлю зависимости Python (1–2 минуты)"
[ -x "$APP_DIR/.venv/bin/python" ] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip >/dev/null
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

ENV_FILE="$APP_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  say "Найден $ENV_FILE — оставляю ключи без изменений"
else
  say "Настройка. Вставляйте ключи сюда — в чат их отправлять не нужно."

  while :; do
    read -r -s -p "1/4 Токен бота от @BotFather (ввод скрыт): " BOT_TOKEN; echo
    BOT_TOKEN="$(printf '%s' "$BOT_TOKEN" | tr -d '[:space:]')"
    [[ "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]{30,}$ ]] && break
    warn "Не похоже на токен (формат 123456789:AA...). Ещё раз."
  done

  TELEGRAM_PROXY=""
  if ME="$(curl -fsS --max-time 15 "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>/dev/null)"; then
    printf '    Бот найден: @%s\n' "$(printf '%s' "$ME" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["username"])')"
  else
    warn "api.telegram.org не ответил: токен неверный или сервер не видит Telegram."
    read -r -p "    Прокси для Telegram (http://user:pass@host:port или socks5://...), Enter — пропустить: " TELEGRAM_PROXY
  fi

  read -r -s -p "2/4 API-ключ YandexGPT (Enter — демо-режим без ИИ; ввод скрыт): " YANDEX_API_KEY; echo
  YANDEX_API_KEY="$(printf '%s' "$YANDEX_API_KEY" | tr -d '[:space:]')"
  YANDEX_FOLDER_ID=""
  LLM_PROVIDER="mock"
  if [ -n "$YANDEX_API_KEY" ]; then
    read -r -p "3/4 ID каталога Yandex Cloud (folder id, начинается с b1…): " YANDEX_FOLDER_ID
    YANDEX_FOLDER_ID="$(printf '%s' "$YANDEX_FOLDER_ID" | tr -d '[:space:]')"
    LLM_PROVIDER="yandex"
    CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 \
      -H "Authorization: Api-Key ${YANDEX_API_KEY}" -H "x-folder-id: ${YANDEX_FOLDER_ID}" \
      -d "{\"modelUri\":\"gpt://${YANDEX_FOLDER_ID}/yandexgpt/latest\",\"completionOptions\":{\"maxTokens\":\"5\"},\"messages\":[{\"role\":\"user\",\"text\":\"ok\"}]}" \
      https://llm.api.cloud.yandex.net/foundationModels/v1/completion || true)"
    if [ "$CODE" = "200" ]; then echo "    YandexGPT отвечает ✅"; else
      warn "YandexGPT ответил HTTP $CODE. Проверьте ключ, folder id и роль ai.languageModels.user. Исправить можно в $ENV_FILE."
    fi
  else
    warn "Демо-режим: ответы-заглушки вместо ИИ. Ключ YandexGPT можно добавить позже в $ENV_FILE."
  fi

  read -r -p "4/4 Ваш Telegram ID для админ-команд (узнать у @userinfobot), Enter — пропустить: " ADMIN_IDS
  ADMIN_IDS="$(printf '%s' "$ADMIN_IDS" | tr -d '[:space:]')"

  FERNET_KEY="$(cd "$APP_DIR" && .venv/bin/python -m app.crypto)"
  umask 077
  cat > "$ENV_FILE" <<EOF
BOT_TOKEN=${BOT_TOKEN}
FERNET_KEY=${FERNET_KEY}
LLM_PROVIDER=${LLM_PROVIDER}
YANDEX_API_KEY=${YANDEX_API_KEY}
YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
YANDEX_MODEL=yandexgpt/latest
ADMIN_IDS=${ADMIN_IDS}
POLL_INTERVAL_SEC=300
MAX_ITEMS_PER_POLL=20
FREE_MONTHLY_LIMIT=100
DB_PATH=data/app.db
TELEGRAM_PROXY=${TELEGRAM_PROXY}
EOF
  umask 022
  echo "    Сохранено в $ENV_FILE (доступ только владельцу)."
  warn "Сделайте копию $ENV_FILE: без FERNET_KEY подключённые магазины не расшифровать."
fi

(cd "$APP_DIR" && .venv/bin/python -c "from app.config import Settings; from app.llm import make_llm; make_llm(Settings.from_env())") \
  || die "Проверка конфигурации не прошла — исправьте $ENV_FILE и запустите скрипт снова."

if [ "$NO_SERVICE" = "1" ]; then
  say "Готово (NO_SERVICE=1: служба не устанавливалась)"; exit 0
fi

say "Создаю службу $SERVICE (автозапуск и перезапуск при сбоях)"
id -u "$RUN_USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$RUN_USER"
chown -R "$RUN_USER:$RUN_USER" "$APP_DIR"
chmod 600 "$ENV_FILE"
cat > "/etc/systemd/system/${SERVICE}.service" <<EOF
[Unit]
Description=EMPIRE Reply Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/.venv/bin/python -m app.main
Restart=always
RestartSec=10
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=${APP_DIR}/data

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null 2>&1
systemctl restart "$SERVICE"
sleep 5
if systemctl is-active --quiet "$SERVICE"; then
  say "Бот работает ✅  Откройте его в Telegram и отправьте /start"
else
  warn "Служба не запустилась. Последние строки лога:"
  journalctl -u "$SERVICE" -n 30 --no-pager || true
  exit 1
fi
cat <<EOF

Полезные команды:
  journalctl -u ${SERVICE} -f            — лог в реальном времени
  sudo systemctl restart ${SERVICE}      — перезапуск (после правки ${ENV_FILE})
  git pull && sudo bash deploy/install.sh — обновление (ключи и база сохраняются)
  Бэкап: ${APP_DIR}/data/app.db + ${ENV_FILE}
EOF
