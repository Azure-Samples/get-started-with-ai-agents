#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"

if [ ! -d .venv ]; then
  python -m venv .venv
  # Activate before installing packages
  # shellcheck disable=SC1091
  . .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r src/requirements.txt
else
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

echo "Starting Gunicorn on 0.0.0.0:$PORT"
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT "api.main:create_app"
