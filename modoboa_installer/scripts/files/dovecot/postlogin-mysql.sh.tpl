#!/bin/sh

DBNAME=%modoboa_dbname DBUSER=%modoboa_dbuser DBPASSWORD=%modoboa_dbpassword

echo "UPDATE core_user SET last_login=now() WHERE username='$USER'" | mysql -u $DBUSER -p$DBPASSWORD $DBNAME

exec "$@"
