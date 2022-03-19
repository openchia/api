#!/bin/bash
set -e

export CHIA_ROOT=/data/chia/${CHIA_NETWORK:=mainnet}
export POOL_CONFIG_PATH="/data/config.yaml"
POOL_LOG_PATH=${POOL_LOG_PATH:=/data/pool_log/stdout.json}
export POOL_LOG_PATH

cd /root/api
../venv/bin/python manage.py collectstatic --no-input
../venv/bin/python manage.py migrate

echo "PATH=/bin:/sbin:/usr/sbin:/usr/bin" > /etc/cron.d/giveaway
echo "POOL_CONFIG_PATH=${POOL_CONFIG_PATH}" >> /etc/cron.d/giveaway
echo "DJANGO_SETTINGS_FILE=${DJANGO_SETTINGS_FILE}" >> /etc/cron.d/giveaway
echo "0 0 * * * root cd /root/api && (../venv/bin/python manage.py giveaway_new || true) && ../venv/bin/python manage.py giveaway_round >> /var/log/cron.log 2>&1" >> /etc/cron.d/giveaway

cron

sed -i s,%%DOMAIN%%,${DOMAIN:=localhost},g /etc/Caddyfile

caddy start -config /etc/Caddyfile

exec ../venv/bin/gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 openchiaapi.asgi:application
