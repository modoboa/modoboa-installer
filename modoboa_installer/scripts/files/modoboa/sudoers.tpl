%{sudo_user} ALL=(%{dovecot_mailboxes_owner}) NOPASSWD: /usr/bin/doveadm
%{opendkim_enabled}%{opendkim_user} ALL=(%{dovecot_mailboxes_owner}) NOPASSWD: /usr/bin/doveadm
