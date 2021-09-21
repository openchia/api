#!/bin/bash
set -e

export CHIA_ROOT=/data/chia/${CHIA_NETWORK:=mainnet}
export POOL_CONFIG_PATH="/data/config.yaml"
export POOL_LOG_PATH="/data/pool_log/stdout"

cd /root/api
../venv/bin/python manage.py collectstatic --no-input
../venv/bin/python manage.py migrate
exec ../venv/bin/daphne --port 8000 openchiaapi.asgi:application
