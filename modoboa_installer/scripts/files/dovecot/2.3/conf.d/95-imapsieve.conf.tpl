##
## Rspamd learning from user actions (IMAPSieve)
##

protocol imap {
  # imap_quota is repeated here since $mail_plugins only refers to the
  # global value (see 20-imap.conf)
  mail_plugins = $mail_plugins imap_quota imap_sieve
}

plugin {
  sieve_plugins = sieve_imapsieve sieve_extprograms
  sieve_global_extensions = +vnd.dovecot.pipe
  sieve_pipe_bin_dir = %{config_dir}/sieve

  # From elsewhere to Junk folder
  imapsieve_mailbox1_name = Junk
  imapsieve_mailbox1_causes = COPY
  imapsieve_mailbox1_before = file:%{config_dir}/sieve/report-spam.sieve

  # From Junk folder to elsewhere
  imapsieve_mailbox2_name = *
  imapsieve_mailbox2_from = Junk
  imapsieve_mailbox2_causes = COPY
  imapsieve_mailbox2_before = file:%{config_dir}/sieve/report-ham.sieve
}
