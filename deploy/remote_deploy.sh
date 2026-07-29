#!/usr/bin/env bash
# Runs ON THE TARGET SERVER (invoked over SSH by the release_frontend GitHub
# Actions workflow). Idempotent: safe to run on a totally fresh VPS (creates
# every directory, the venv, the systemd unit) and safe to run again on a
# server that already has everything set up (just updates code/deps and
# restarts the service). This is what makes "change DEPLOY_HOST to a new VPS"
# work with zero manual setup.
set -euo pipefail

: "${DEPLOY_PATH:?DEPLOY_PATH must be set}"
: "${APP_USERNAME:?APP_USERNAME must be set}"
: "${APP_PASSWORD:?APP_PASSWORD must be set}"
: "${APP_SECRET_KEY:?APP_SECRET_KEY must be set}"

APP_DIR="${DEPLOY_PATH}/app"
VENV_DIR="${DEPLOY_PATH}/venv"
DATA_DIR="${DEPLOY_PATH}/data"
LOG_DIR="${DEPLOY_PATH}/logs"
PORT="${PORT:-8000}"
SERVICE_NAME="pathmate-analyzer"

echo "==> Ensuring directory layout under ${DEPLOY_PATH}"
mkdir -p "$APP_DIR" "$VENV_DIR" "$DATA_DIR/coachings/files" "$DATA_DIR/patient_models" "$LOG_DIR"

# Decide how to run privileged commands: root already, passwordless sudo, or
# sudo with the password supplied via DEPLOY_SUDO_PASSWORD.
if [ "$(id -u)" -eq 0 ]; then
	run_privileged() { "$@"; }
elif sudo -n true 2>/dev/null; then
	run_privileged() { sudo "$@"; }
elif [ -n "${DEPLOY_SUDO_PASSWORD:-}" ]; then
	run_privileged() { echo "$DEPLOY_SUDO_PASSWORD" | sudo -S "$@"; }
else
	run_privileged() {
		echo "No root, no passwordless sudo, and no DEPLOY_SUDO_PASSWORD set - cannot run: $*" >&2
		return 1
	}
fi

echo "==> Ensuring python3 + venv module are available"
if ! command -v python3 >/dev/null 2>&1; then
	if command -v apt-get >/dev/null 2>&1; then
		run_privileged apt-get update -y
		run_privileged apt-get install -y python3 python3-venv python3-pip
	else
		echo "python3 is missing and apt-get is not available; install python3 manually." >&2
		exit 1
	fi
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
	if command -v apt-get >/dev/null 2>&1; then
		run_privileged apt-get update -y
		run_privileged apt-get install -y python3-venv
	fi
fi

echo "==> Creating/updating virtualenv at ${VENV_DIR}"
if [ ! -x "${VENV_DIR}/bin/python" ]; then
	python3 -m venv "$VENV_DIR"
fi

"${VENV_DIR}/bin/pip" install --upgrade pip wheel >/dev/null
"${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "==> Writing ${APP_DIR}/.env"
cat > "${APP_DIR}/.env" <<EOF
APP_USERNAME=${APP_USERNAME}
APP_PASSWORD=${APP_PASSWORD}
APP_SECRET_KEY=${APP_SECRET_KEY}
DATA_DIR=${DATA_DIR}
PORT=${PORT}
EOF
chmod 600 "${APP_DIR}/.env"

echo "==> Installing systemd unit"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
RENDERED_UNIT="$(mktemp)"
sed \
	-e "s#__APP_DIR__#${APP_DIR}#g" \
	-e "s#__VENV_DIR__#${VENV_DIR}#g" \
	-e "s#__PORT__#${PORT}#g" \
	-e "s#__RUN_USER__#$(id -un)#g" \
	"${APP_DIR}/deploy/pathmate-analyzer.service.template" > "$RENDERED_UNIT"

run_privileged cp "$RENDERED_UNIT" "$SERVICE_FILE"
rm -f "$RENDERED_UNIT"

run_privileged systemctl daemon-reload
run_privileged systemctl enable "$SERVICE_NAME"
run_privileged systemctl restart "$SERVICE_NAME"

echo "==> Deploy complete. Service status:"
run_privileged systemctl --no-pager status "$SERVICE_NAME" || true
