#!/bin/sh
set -eu

port="${PORT:-80}"
case "$port" in
  ''|*[!0-9]*) echo "PORT must be numeric" >&2; exit 64 ;;
esac

# Render supplies PORT at runtime. Keep nginx and the backend private to the
# container and let nginx expose the single public listener.
sed "s/__PORT__/${port}/g" /etc/nginx/conf.d/default.template.conf > /etc/nginx/conf.d/default.conf
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
