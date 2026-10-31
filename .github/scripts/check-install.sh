#!/bin/bash
# Fail when a freshly installed mail server is not usable.
set -eu

hostname=${1:-mail.example.test}

postfix check
doveconf -n > /dev/null
nginx -t

for service in postgresql redis-server uwsgi nginx postfix dovecot \
    amavis opendkim clamav-daemon; do
    systemctl is-active --quiet "$service" || {
        echo "$service is not running"
        systemctl status "$service" --no-pager || true
        exit 1
    }
done

# The exit code of supervisorctl does not tell STARTING or BACKOFF from RUNNING
for _ in $(seq 15); do
    workers=$(supervisorctl status || true)
    grep -qv RUNNING <<< "$workers" || break
    sleep 2
done
echo "$workers"
if grep -v RUNNING <<< "$workers"; then
    echo "Some workers are not running"
    exit 1
fi

curl --silent --show-error --fail --insecure --output /dev/null \
    --resolve "$hostname:443:127.0.0.1" "https://$hostname/"
