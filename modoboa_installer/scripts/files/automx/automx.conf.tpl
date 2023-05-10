[automx]
provider = %domain
domains = *

#debug=yes
#logfile = /srv/automx/automx.log

# Protect against DoS
memcache = 127.0.0.1:11211
memcache_ttl = 600
client_error_limit = 20
rate_limit_exception_networks = 127.0.0.0/8, ::1/128

[global]
backend = sql
action = settings
account_type = email
host = %sql_dsn
query = %sql_query
result_attrs = display_name, email

display_name = ${display_name}

smtp = yes
smtp_server = %hostname
smtp_port = 587
smtp_encryption = starttls
smtp_auth = plaintext
smtp_auth_identity = ${email}
smtp_refresh_ttl = 6
smtp_default = yes

imap = yes
imap_server = %hostname
imap_port = 143
imap_encryption = starttls
imap_auth = plaintext
imap_auth_identity = ${email}
imap_refresh_ttl = 6
