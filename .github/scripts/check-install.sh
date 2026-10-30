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

# Supervisor fails until the last script creates the opendkim user, then
# systemd restarts it: leave it the time to do so
for _ in $(seq 18); do
    supervisorctl status > /dev/null 2>&1 && break
    sleep 10
done
supervisorctl status

curl --silent --show-error --fail --insecure --output /dev/null \
    --resolve "$hostname:443:127.0.0.1" "https://$hostname/"
