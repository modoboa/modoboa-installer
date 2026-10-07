[postfix]
enabled = true
port = %ports_blocked
maxretry = %max_retry
bantime = %ban_time
findtime = %find_time
filter = postfix[mode=aggressive]
logpath = /var/log/mail.log
ignoreip = ::1 127.0.0.1/8
