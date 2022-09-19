connect = host=%dbhost port=%dbport dbname=%modoboa_dbname user=%modoboa_dbuser password=%modoboa_dbpassword

# CREATE TABLE quota (
#   username varchar(100) not null,
#   bytes bigint not null default 0,
#   messages integer not null default 0,
#   primary key (username)
# );

map {
  pattern = priv/quota/storage
  table = admin_quota
  username_field = username
  value_field = bytes
}
map {
  pattern = priv/quota/messages
  table = admin_quota
  username_field = username
  value_field = messages
}

# CREATE TABLE expires (
#   username varchar(100) not null,
#   mailbox varchar(255) not null,
#   expire_stamp integer not null,
#   primary key (username, mailbox)
# );

map {
  pattern = shared/expire/$user/$mailbox
  table = expires
  value_field = expire_stamp

  fields {
    username = $user
    mailbox = $mailbox
  }
}
