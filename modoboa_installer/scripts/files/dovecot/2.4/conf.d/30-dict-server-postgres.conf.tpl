##
## Dictionary server settings
##

# Dictionary can be used to store key=value lists. This is used by several
# plugins. The dictionary can be accessed either directly or though a
# dictionary server. The following dict block maps dictionary names to URIs
# when the server is used. These can then be referenced using URIs in format
# "proxy::<name>".

dict_server {
  pgsql %dbhost {
    parameters {
      port = %dbport
      dbname = %modoboa_dbname
      user = %modoboa_dbuser
      password = %modoboa_dbpassword
    }
  }
  dict quota {
    driver = sql
    sql_driver = %db_driver
    hostname = %dbhost

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

  # Who shares folders with whom (shared namespace listing). Tables are
  # created by Modoboa.
  dict acl {
    driver = sql
    sql_driver = %db_driver
    hostname = %dbhost

    dict_map shared/shared-boxes/user/$to/$from {
      sql_table = admin_usershare
      value_field dummy {
      }
      key_field from_user {
        value = $from
      }
      key_field to_user {
        value = $to
      }
    }

    dict_map shared/shared-user-boxes-rev/$from/$to {
      sql_table = admin_usershare
      value_field dummy {
      }
      key_field from_user {
        value = $from
      }
      key_field to_user {
        value = $to
      }
    }

    dict_map shared/shared-boxes/anyone/$from {
      sql_table = admin_anyoneshare
      value_field dummy {
      }
      key_field from_user {
        value = $from
      }
    }
  }
}

quota_clone {
  dict proxy {
    name = quota
  }
}
