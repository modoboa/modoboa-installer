##
## Rspamd learning from user actions (IMAPSieve)
##

protocol imap {
  mail_plugins {
    imap_sieve = yes
  }
}

sieve_plugins {
  sieve_imapsieve = yes
  sieve_extprograms = yes
}

sieve_global_extensions {
  vnd.dovecot.pipe = yes
}

sieve_pipe_bin_dir = %{config_dir}/sieve

# From elsewhere to Junk folder
mailbox Junk {
  sieve_script report-spam {
    type = before
    cause = copy
    path = %{config_dir}/sieve/report-spam.sieve
  }
}

# From Junk folder to elsewhere
imapsieve_from Junk {
  sieve_script report-ham {
    type = before
    cause = copy
    path = %{config_dir}/sieve/report-ham.sieve
  }
}
