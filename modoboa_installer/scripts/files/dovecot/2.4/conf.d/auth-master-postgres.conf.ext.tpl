# Authentication for master users. Included from auth.conf.

# By adding master=yes setting inside a passdb you make the passdb a list
# of "master users", who can log in as anyone else.
# <https://doc.dovecot.org/latest/core/config/auth/master_users.html>

# Example master user passdb using passwd-file. You can use any passdb though.
#passdb master-passwd-file {
#  driver = passwd-file
#  master = yes
#  passwd_file_path = /etc/dovecot/master-users
#}

sql_driver = %db_driver

pgsql %dbhost {
  parameters {
    port = %dbport
    dbname = %modoboa_dbname
    user = %modoboa_dbuser
    password = %modoboa_dbpassword
  }
}

passdb db1 {
  driver = sql
  sql_query = SELECT email AS user, password FROM core_user WHERE email='%%{user}' and is_active and master_user
  master = yes
  result_success = continue
}
