[dovecot]
enabled = true
port = %ports_blocked
filter = dovecot
logpath = /var/log/mail.log
maxretry = %max_retry
bantime = %ban_time
findtime = %find_time
ignoreip = ::1 127.0.01/8
