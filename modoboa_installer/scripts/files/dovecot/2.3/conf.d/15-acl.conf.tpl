##
## Shared folders (IMAP ACL)
##

# Must be loaded before 20-imap.conf: a global mail_plugins change does not
# reach a protocol block defined earlier.
mail_plugins = $mail_plugins acl
protocol imap {
  mail_plugins = $mail_plugins imap_acl
}

# Shared folders are listed as shared/<owner address>/<folder>: addresses
# contain dots, so the separator can't be '.'.
namespace inbox {
  separator = /
}

namespace shared {
  type = shared
  separator = /
  prefix = shared/%%%%u/
  # Owner path built like the userdb home, to avoid a userdb lookup per owner.
  # INDEXPVT keeps the \Seen flag private to each user.
  location = maildir:%{home_dir}/%%%%d/%%%%n/Maildir:INDEXPVT=~/Maildir/shared/%%%%u
  subscriptions = no
  list = children
}

dict {
  acl = %{db_driver}:/etc/dovecot/dovecot-dict-sql.conf.ext
}

plugin {
  acl = vfile
  # Master users would otherwise be subject to the ACLs of the user they
  # log in as, and lose access to the mailboxes.
  acl_user = %%u
  acl_shared_dict = proxy::acl
}
