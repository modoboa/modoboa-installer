#!/bin/sh

PATH="/usr/bin:/usr/local/bin:/bin"

psql -c "UPDATE core_user SET last_login=now() WHERE username='$USER'" > /dev/null

exec "$@"
