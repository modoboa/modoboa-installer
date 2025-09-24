# Authentication for SQL users. Included from auth.conf.
#
# <https://doc.dovecot.org/latest/core/config/auth/databases/sql.html>

# For the sql passdb module, you'll need a database with a table that
# contains fields for at least the username and password. If you want to
# use the user@domain syntax, you might want to have a separate domain
# field as well.
#
# If your users all have the same uig/gid, and have predictable home
# directories, you can use the static userdb module to generate the home
# dir based on the username and domain. In this case, you won't need fields
# for home, uid, or gid in the database.
#
# If you prefer to use the sql userdb module, you'll want to add fields
# for home, uid, and gid. Here is an example table:
#
# CREATE TABLE users (
#     username VARCHAR(128) NOT NULL,
#     domain VARCHAR(128) NOT NULL,
#     password VARCHAR(64) NOT NULL,
#     home VARCHAR(255) NOT NULL,
#     uid INTEGER NOT NULL,
#     gid INTEGER NOT NULL,
#     active CHAR(1) DEFAULT 'Y' NOT NULL
# );

# Database driver: mysql, pgsql, sqlite
sql_driver = %db_driver

# Database connection string. This is driver-specific setting.
#
# HA / round-robin load-balancing is supported by giving multiple host
# settings, like: host=sql1.host.org host=sql2.host.org
#
# pgsql:
#   For available options, see the PostgreSQL documention for the
#   PQconnectdb function of libpq.
#   Use maxconns=n (default 5) to change how many connections Dovecot can
#   create to pgsql.
#
# mysql:
#   Basic options emulate PostgreSQL option names:
#     host, port, user, password, dbname
#
#   But also adds some new settings:
#     client_flags        - See MySQL manual
#     ssl_ca, ssl_ca_path - Set either one or both to enable SSL
#     ssl_cert, ssl_key   - For sending client-side certificates to server
#     ssl_cipher          - Set minimum allowed cipher security (default: HIGH)
#     option_file         - Read options from the given file instead of
#                           the default my.cnf location
#     option_group        - Read options from the given group (default: client)
# 
#   You can connect to UNIX sockets by using host: host=/var/run/mysql.sock
#   Note that currently you can't use spaces in parameters.
#
# sqlite:
#   The path to the database file.
#
# Examples:
# mysql 192.168.1.1 {
#   dbname = users
# }
# mysql sql.example.com {
#   ssl = yes
#   user = virtual
#   password = blarg
#   dbname = virtual
# }
# sqlite /etc/dovecot/authdb.sqlite {
# }
#
#mysql /var/run/mysqld/mysqld.sock {
#  user = dovecot
#  password = dvmail
#  dbname = dovecot
#}
#mysql localhost {
# ...
#}
mysql %dbhost {
  port = %dbport
  dbname = %modoboa_dbname
  user = %modoboa_dbuser
  password = %modoboa_dbpassword
}

#passdb sql {
#  default_password_scheme = SHA256

# passdb query to retrieve the password. It can return fields:
#   password - The user's password. This field must be returned.
#   user - user@domain from the database. Needed with case-insensitive lookups.
#   username and domain - An alternative way to represent the "user" field.
#
# The "user" field is often necessary with case-insensitive lookups to avoid
# e.g. "name" and "nAme" logins creating two different mail directories. If
# your user and domain names are in separate fields, you can return "username"
# and "domain" fields instead of "user".
#
# The query can also return other fields which have a special meaning, see
# https://doc.dovecot.org/latest/core/config/auth/passdb.html#extra-fields
#
# Commonly used available substitutions (see https://doc.dovecot.org/latest/core/settings/variables.html
# for full list):
#   %%{user} = entire user@domain
#   %%{user|username} = user part of user@domain
#   %%{user|domain} = domain part of user@domain
# 
# Note that these can be used only as input to SQL query. If the query outputs
# any of these substitutions, they're not touched. Otherwise it would be
# difficult to have eg. usernames containing '%%' characters.
#
# Example:
#   query = SELECT userid AS user, pw AS password \
#     FROM users WHERE userid = '%%u' AND active = 'Y'
#
#  query = \
#    SELECT userid as username, domain, password \
#    FROM users WHERE userid = '%%{user|username}' AND domain = '%%{user|domain}'
#}

passdb sql {
  query = SELECT email AS user, password FROM core_user u INNER JOIN admin_mailbox mb ON u.id=mb.user_id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE (mb.is_send_only=0 OR '%%{protocol}' NOT IN ('imap', 'pop3')) AND u.email='%%{user}' AND u.is_active=1 AND dom.enabled=1
}

#userdb sql {
# userdb query to retrieve the user information. It can return fields:
#   uid - System UID (overrides mail_uid setting)
#   gid - System GID (overrides mail_gid setting)
#   home - Home directory
#   mail_driver - Mail driver
#   mail_path - Mail storage path
#
# None of these are strictly required. If you use a single UID and GID, and
# home or mail directory fits to a template string, you could use userdb static
# instead. For a list of all fields that can be returned, see
# Examples:
#   query = SELECT home, uid, gid FROM users WHERE userid = '%%{user}'
#   query = SELECT dir AS home, user AS uid, group AS gid FROM users where userid = '%%{user}'
#   query = SELECT home, 501 AS uid, 501 AS gid FROM users WHERE userid = '%%{user}'
#
#  query = \
#    SELECT home, uid, gid \
#    FROM users WHERE userid = '%%{user|username}' AND domain = '%%{user|domain}'

# Query to get a list of all usernames.
#  iterate_query = SELECT username AS user,domain FROM users

#  userdb_ldap {
#    iterate_fields {
#      home = /var/vmail/%%{home}
#    }
#  }
#}

userdb sql {
  query = SELECT '%{home_dir}/%%{user|domain}/%%{user|username}' AS home, %mailboxes_owner_uid as uid, %mailboxes_owner_gid as gid, CONCAT(mb.quota, 'M') AS quota_storage_size FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN core_user u ON u.id=mb.user_id WHERE (mb.is_send_only=0 OR '%%{protocol}' NOT IN ('imap', 'pop3', 'lmtp')) AND mb.address='%%{user|username}' AND dom.name='%%{user|domain}'
  iterate_query = SELECT email AS user FROM core_user
}

#passdb static {
#  fields {
#    user=%%{user|username|lower}
#    noauthenticate=yes
#  }
## you can remove next line if you want to always normalize your usernames
#  skip = authenticated
#}

# "prefetch" user database means that the passdb already provided the
# needed information and there's no need to do a separate userdb lookup.
# <https://doc.dovecot.org/latest/core/config/auth/databases/prefetch.html>
#userdb prefetch {
#}

#userdb static {
#  fields {
#    user=%%{user|lower}
#  }
# you can remove next line if you want to always normalize your usernames
#  skip = found
#}

# If you don't have any user-specific settings, you can avoid the user_query
# by using userdb static instead of userdb sql, for example:
# <https://doc.dovecot.org/latest/core/config/auth/databases/static.html>
#userdb static {
  #fields {
  #  uid = vmail
  #  gid = vmail
  #  home = /var/vmail/%%{user}
  #}
#}
