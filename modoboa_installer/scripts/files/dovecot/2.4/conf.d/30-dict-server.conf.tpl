##
## Dictionary server settings
##

# Dictionary can be used to store key=value lists. This is used by several
# plugins. The dictionary can be accessed either directly or though a
# dictionary server. The following dict block maps dictionary names to URIs
# when the server is used. These can then be referenced using URIs in format
# "proxy::<name>".

dict_server {
  dict quota {
    driver = sql
    sql_driver = %db_driver
    hostname = %dbhost
    dbname = %modoboa_dbname
    user = %modoboa_dbuser
    password = %modoboa_dbpassword

    dict_map priv/quota/storage {
      sql_table = admin_quota
      username_field = username
      value_field bytes {
        type = uint
      }
    }

    dict_map priv/quota/messages {
      sql_table = admin_quota
      username_field = username
      value_field messages {
        type = uint
      }
    }
  }
}

quota_clone {
  dict proxy {
    name = quota
  }
}
