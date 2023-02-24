# -*- mode: conf -*-
# vim:ft=cfg

# Config file for Radicale - A simple calendar server
#
# Place it into /etc/radicale/config (global)
# or ~/.config/radicale/config (user)
#
# The current values are the default ones


[server]

# CalDAV server hostnames separated by a comma
# IPv4 syntax: address:port
# IPv6 syntax: [address]:port
# For example: 0.0.0.0:9999, [::]:9999
#hosts = 127.0.0.1:5232

# Daemon flag
#daemon = False

# File storing the PID in daemon mode
#pid =

# Max parallel connections
#max_connections = 20

# Max size of request body (bytes)
#max_content_length = 10000000

# Socket timeout (seconds)
#timeout = 10

# SSL flag, enable HTTPS protocol
#ssl = False

# SSL certificate path
#certificate = /etc/ssl/radicale.cert.pem

# SSL private key
#key = /etc/ssl/radicale.key.pem

# CA certificate for validating clients. This can be used to secure
# TCP traffic between Radicale and a reverse proxy
#certificate_authority =

# SSL Protocol used. See python's ssl module for available values
#protocol = PROTOCOL_TLSv1_2

# Available ciphers. See python's ssl module for available ciphers
#ciphers =

# Reverse DNS to resolve client address in logs
#dns_lookup = True

# Message displayed in the client when a password is needed
#realm = Radicale - Password Required


[encoding]

# Encoding for responding requests
#request = utf-8

# Encoding for storing local collections
#stock = utf-8


[auth]

# Authentication method
# Value: none | htpasswd | remote_user | http_x_remote_user
type = radicale_dovecot_auth 

# Htpasswd filename
# htpasswd_filename = users

# Htpasswd encryption method
# Value: plain | sha1 | ssha | crypt | bcrypt | md5
# Only bcrypt can be considered secure.
# bcrypt and md5 require the passlib library to be installed.
# htpasswd_encryption = plain 

# Incorrect authentication delay (seconds)
#delay = 1

auth_socket = %{auth_socket_path}


[rights]

# Rights backend
# Value: none | authenticated | owner_only | owner_write | from_file
type = from_file 

# File for rights management from_file
file = %{config_dir}/rights


[storage]

# Storage backend
# Value: multifilesystem
type = radicale_storage_by_index
radicale_storage_by_index_fields = dtstart, dtend, uid, summary

# Folder for storing local collections, created if not present
filesystem_folder = %{home_dir}/collections

# Lock the storage. Never start multiple instances of Radicale or edit the
# storage externally while Radicale is running if disabled.
#filesystem_locking = True

# Sync all changes to disk during requests. (This can impair performance.)
# Disabling it increases the risk of data loss, when the system crashes or
# power fails!
#filesystem_fsync = True

# Delete sync token that are older (seconds)
#max_sync_token_age = 2592000

# Close the lock file when no more clients are waiting.
# This option is not very useful in general, but on Windows files that are
# opened cannot be deleted.
#filesystem_close_lock_file = False

# Command that is run after changes to storage
# Example: ([ -d .git ] || git init) && git add -A && (git diff --cached --quiet || git commit -m "Changes by "%%(user)s)
#hook =


[web]

# Web interface backend
# Value: none | internal
type = none 


[logging]

# Logging configuration file
# If no config is given, simple information is printed on the standard output
# For more information about the syntax of the configuration file, see:
# http://docs.python.org/library/logging.config.html
#config = /etc/radicale/logging

# Store all environment variables (including those set in the shell)
#full_environment = False

# Don't include passwords in logs
#mask_passwords = True


[headers]

# Additional HTTP headers
#Access-Control-Allow-Origin = *
