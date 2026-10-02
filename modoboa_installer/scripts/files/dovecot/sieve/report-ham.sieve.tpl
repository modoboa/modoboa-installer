require ["vnd.dovecot.pipe", "copy", "imapsieve", "environment", "variables"];

if environment :matches "imap.mailbox" "*" {
  set "mailbox" "${1}";
}

# Messages moved from Junk to Trash are not ham
if string "${mailbox}" "Trash" {
  stop;
}

pipe :copy "rspamd-learn-ham.sh";
