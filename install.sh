#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
ENV_EXAMPLE_FILE="${ROOT_DIR}/.env.example"

print_step() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

die() {
  printf 'Ошибка: %s\n' "$1" >&2
  exit 1
}

env_value() {
  local key="$1"
  local fallback="${2:-}"
  local source_file="${3:-$ENV_FILE}"

  if [[ -f "$source_file" ]]; then
    local value
    value="$(grep -E "^${key}=" "$source_file" | tail -n 1 | cut -d= -f2- || true)"
    value="${value%\"}"
    value="${value#\"}"
    if [[ -n "$value" ]]; then
      printf '%s' "$value"
      return 0
    fi
  fi

  printf '%s' "$fallback"
}

ask_input() {
  local prompt="$1"
  local default="${2:-}"
  local answer=""

  if [[ -n "$default" ]]; then
    read -r -p "${prompt} [${default}]: " answer
    printf '%s' "${answer:-$default}"
  else
    read -r -p "${prompt}: " answer
    printf '%s' "$answer"
  fi
}

ask_required() {
  local prompt="$1"
  local default="${2:-}"
  local answer=""

  while true; do
    answer="$(ask_input "$prompt" "$default")"
    if [[ -n "$answer" ]]; then
      printf '%s' "$answer"
      return 0
    fi
    printf 'Значение обязательно.\n' >&2
  done
}

ask_secret() {
  local prompt="$1"
  local default="${2:-}"
  local answer=""

  while true; do
    if [[ -n "$default" ]]; then
      read -r -s -p "${prompt} [hidden, Enter to keep current]: " answer
      printf '\n' >&2
      answer="${answer:-$default}"
    else
      read -r -s -p "${prompt}: " answer
      printf '\n' >&2
    fi

    if [[ -n "$answer" ]]; then
      printf '%s' "$answer"
      return 0
    fi
    printf 'Значение обязательно.\n' >&2
  done
}

ask_yes_no() {
  local prompt="$1"
  local default="${2:-Y}"
  local answer=""
  local normalized=""

  while true; do
    read -r -p "${prompt} [${default}/$( [[ "$default" == "Y" ]] && printf 'n' || printf 'y' )]: " answer
    answer="${answer:-$default}"
    normalized="$(printf '%s' "$answer" | tr '[:upper:]' '[:lower:]')"

    case "$normalized" in
      y|yes) return 0 ;;
      n|no) return 1 ;;
      *) printf 'Введите y или n.\n' >&2 ;;
    esac
  done
}

ask_numeric() {
  local prompt="$1"
  local default="${2:-}"
  local answer=""

  while true; do
    answer="$(ask_required "$prompt" "$default")"
    if [[ "$answer" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      printf '%s' "$answer"
      return 0
    fi
    printf 'Введите корректное число.\n' >&2
  done
}

quote_env() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '"%s"' "$value"
}

ensure_curl() {
  if command -v curl >/dev/null 2>&1; then
    return 0
  fi

  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y curl
    return 0
  fi

  die "Для автоматической установки Docker нужен curl. Установите его вручную."
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi

  print_step "Docker не найден"
  if ! ask_yes_no "Установить Docker автоматически (подходит для Debian/Ubuntu)?" "Y"; then
    die "Docker обязателен для автоматического деплоя."
  fi

  ensure_curl
  curl -fsSL https://get.docker.com | sudo sh

  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl enable --now docker || true
  fi

  if [[ -n "${USER:-}" ]] && command -v usermod >/dev/null 2>&1; then
    sudo usermod -aG docker "$USER" || true
  fi
}

docker_available() {
  docker info >/dev/null 2>&1
}

sudo_docker_available() {
  command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1
}

compose_available() {
  if docker_available; then
    docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1
  elif sudo_docker_available; then
    sudo docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1
  else
    return 1
  fi
}

compose_cmd() {
  if docker_available; then
    if docker compose version >/dev/null 2>&1; then
      docker compose "$@"
      return 0
    fi

    if command -v docker-compose >/dev/null 2>&1; then
      docker-compose "$@"
      return 0
    fi
  fi

  if sudo_docker_available; then
    if sudo docker compose version >/dev/null 2>&1; then
      sudo docker compose "$@"
      return 0
    fi

    if command -v docker-compose >/dev/null 2>&1; then
      sudo docker-compose "$@"
      return 0
    fi
  fi

  die "Не удалось найти рабочий docker compose."
}

ensure_compose() {
  if compose_available; then
    return 0
  fi

  die "Docker Compose не найден. Установите Docker Compose Plugin или docker-compose."
}

write_env_file() {
  local bot_token="$1"
  local admin_ids="$2"
  local xui_host="$3"
  local xui_username="$4"
  local xui_password="$5"
  local xui_inbound_id="$6"
  local xui_tls_verify="$7"
  local subscription_base_url="$8"
  local trial_duration_days="$9"
  local trial_traffic_gb="${10}"
  local trial_device_limit="${11}"
  local monthly_price_stars="${12}"
  local monthly_duration_days="${13}"
  local monthly_traffic_gb="${14}"
  local monthly_device_limit="${15}"
  local database_url="${16}"

  cat > "$ENV_FILE" <<EOF
# Telegram Bot
BOT_TOKEN=$(quote_env "$bot_token")
ADMIN_IDS=$(quote_env "$admin_ids")

# 3X-UI Panel
XUI_HOST=$(quote_env "$xui_host")
XUI_USERNAME=$(quote_env "$xui_username")
XUI_PASSWORD=$(quote_env "$xui_password")
XUI_INBOUND_ID=${xui_inbound_id}
XUI_TLS_VERIFY=${xui_tls_verify}

# Подписки
SUBSCRIPTION_BASE_URL=$(quote_env "$subscription_base_url")

# Тарифы (в Telegram Stars)
TRIAL_DURATION_DAYS=${trial_duration_days}
TRIAL_TRAFFIC_GB=${trial_traffic_gb}
TRIAL_DEVICE_LIMIT=${trial_device_limit}

MONTHLY_PRICE_STARS=${monthly_price_stars}
MONTHLY_DURATION_DAYS=${monthly_duration_days}
MONTHLY_TRAFFIC_GB=${monthly_traffic_gb}
MONTHLY_DEVICE_LIMIT=${monthly_device_limit}

# База данных
DATABASE_URL=$(quote_env "$database_url")
EOF

  chmod 600 "$ENV_FILE"
}

backup_existing_env() {
  if [[ -f "$ENV_FILE" ]]; then
    local backup_file="${ENV_FILE}.bak.$(date '+%Y%m%d%H%M%S')"
    cp "$ENV_FILE" "$backup_file"
    printf 'Текущий .env сохранен в %s\n' "$backup_file"
  fi
}

collect_configuration() {
  local defaults_file="$ENV_EXAMPLE_FILE"
  if [[ -f "$ENV_FILE" ]]; then
    defaults_file="$ENV_FILE"
  fi

  print_step "Настройка переменных окружения"

  BOT_TOKEN="$(ask_required "Введите BOT_TOKEN" "$(env_value BOT_TOKEN '' "$defaults_file")")"
  ADMIN_IDS="$(ask_input "Введите ADMIN_IDS через запятую" "$(env_value ADMIN_IDS '' "$defaults_file")")"

  XUI_HOST="$(ask_required "Введите XUI_HOST" "$(env_value XUI_HOST 'https://panel.example.com:2053' "$defaults_file")")"
  XUI_USERNAME="$(ask_required "Введите XUI_USERNAME" "$(env_value XUI_USERNAME 'admin' "$defaults_file")")"
  XUI_PASSWORD="$(ask_secret "Введите XUI_PASSWORD" "$(env_value XUI_PASSWORD '' "$defaults_file")")"
  XUI_INBOUND_ID="$(ask_numeric "Введите XUI_INBOUND_ID" "$(env_value XUI_INBOUND_ID '1' "$defaults_file")")"
  if ask_yes_no "Проверять TLS сертификат 3X-UI?" "$( [[ "$(env_value XUI_TLS_VERIFY 'true' "$defaults_file")" == "true" ]] && printf 'Y' || printf 'N' )"; then
    XUI_TLS_VERIFY="true"
  else
    XUI_TLS_VERIFY="false"
  fi

  SUBSCRIPTION_BASE_URL="$(ask_required "Введите SUBSCRIPTION_BASE_URL" "$(env_value SUBSCRIPTION_BASE_URL 'https://panel.example.com:2096/sub/' "$defaults_file")")"

  TRIAL_DURATION_DAYS="$(ask_numeric "Trial: срок в днях" "$(env_value TRIAL_DURATION_DAYS '1' "$defaults_file")")"
  TRIAL_TRAFFIC_GB="$(ask_numeric "Trial: лимит трафика в ГБ" "$(env_value TRIAL_TRAFFIC_GB '1' "$defaults_file")")"
  TRIAL_DEVICE_LIMIT="$(ask_numeric "Trial: лимит устройств" "$(env_value TRIAL_DEVICE_LIMIT '1' "$defaults_file")")"

  MONTHLY_PRICE_STARS="$(ask_numeric "Месячный тариф: цена в Telegram Stars" "$(env_value MONTHLY_PRICE_STARS '50' "$defaults_file")")"
  MONTHLY_DURATION_DAYS="$(ask_numeric "Месячный тариф: срок в днях" "$(env_value MONTHLY_DURATION_DAYS '30' "$defaults_file")")"
  MONTHLY_TRAFFIC_GB="$(ask_numeric "Месячный тариф: лимит трафика в ГБ (0 для безлимита)" "$(env_value MONTHLY_TRAFFIC_GB '0' "$defaults_file")")"
  MONTHLY_DEVICE_LIMIT="$(ask_numeric "Месячный тариф: лимит устройств" "$(env_value MONTHLY_DEVICE_LIMIT '2' "$defaults_file")")"

  DATABASE_URL="$(ask_required "Введите DATABASE_URL" "$(env_value DATABASE_URL 'sqlite+aiosqlite:///./data/bot.db' "$defaults_file")")"
}

deploy_stack() {
  print_step "Сборка и запуск контейнеров"
  mkdir -p "${ROOT_DIR}/data" "${ROOT_DIR}/logs"

  compose_cmd build --pull
  compose_cmd up -d
  compose_cmd ps
}

main() {
  print_step "Подготовка 3X-UI Telegram Bot к деплою"
  cd "$ROOT_DIR"

  install_docker
  ensure_compose

  local overwrite_env="Y"
  if [[ -f "$ENV_FILE" ]]; then
    if ask_yes_no "Файл .env уже существует. Перезаписать его?" "N"; then
      backup_existing_env
    else
      overwrite_env="N"
    fi
  fi

  if [[ "$overwrite_env" == "Y" ]]; then
    collect_configuration
    write_env_file \
      "$BOT_TOKEN" \
      "$ADMIN_IDS" \
      "$XUI_HOST" \
      "$XUI_USERNAME" \
      "$XUI_PASSWORD" \
      "$XUI_INBOUND_ID" \
      "$XUI_TLS_VERIFY" \
      "$SUBSCRIPTION_BASE_URL" \
      "$TRIAL_DURATION_DAYS" \
      "$TRIAL_TRAFFIC_GB" \
      "$TRIAL_DEVICE_LIMIT" \
      "$MONTHLY_PRICE_STARS" \
      "$MONTHLY_DURATION_DAYS" \
      "$MONTHLY_TRAFFIC_GB" \
      "$MONTHLY_DEVICE_LIMIT" \
      "$DATABASE_URL"
    printf '.env успешно создан.\n'
  else
    printf 'Использую существующий .env без изменений.\n'
  fi

  if ask_yes_no "Собрать и запустить проект через Docker Compose сейчас?" "Y"; then
    deploy_stack
    printf '\nГотово. Для просмотра логов используйте:\n'
    printf '  docker compose logs -f bot\n'
  else
    printf '\nКонфигурация сохранена. Для ручного запуска выполните:\n'
    printf '  docker compose build --pull\n'
    printf '  docker compose up -d\n'
  fi
}

main "$@"
