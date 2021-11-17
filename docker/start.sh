#!/bin/bash
set -e

export CHIA_ROOT=/data/chia/${CHIA_NETWORK:=mainnet}
export POOL_CONFIG_PATH="/data/config.yaml"
export POOL_LOG_PATH="/data/pool_log/stdout"

cd /root/api
../venv/bin/python manage.py collectstatic --no-input
../venv/bin/python manage.py migrate

echo "PATH=/bin:/sbin:/usr/sbin:/usr/bin" > /etc/cron.d/giveaway
echo "POOL_CONFIG_PATH=${POOL_CONFIG_PATH}" >> /etc/cron.d/giveaway
echo "0 0 * * * root cd /root/api && (../venv/bin/python manage.py giveaway_new || true) && ../venv/bin/python manage.py giveaway_round >> /var/log/cron.log 2>&1" >> /etc/cron.d/giveaway

cron

exec ../venv/bin/daphne --bind 0.0.0.0 --port 8000 openchiaapi.asgi:application
