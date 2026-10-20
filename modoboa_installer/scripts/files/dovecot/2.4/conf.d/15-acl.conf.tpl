##
## Shared folders (IMAP ACL)
##

mail_plugins {
  acl = yes
}
protocol imap {
  mail_plugins {
    imap_acl = yes
  }
}

acl_driver = vfile
# Master users would otherwise be subject to the ACLs of the user they
# log in as, and lose access to the mailboxes.
acl_user = %%{user}

# Shared folders are listed as shared/<owner address>/<folder>: addresses
# contain dots, so the separator can't be '.'.
namespace inbox {
  separator = /
}

namespace shared {
  type = shared
  separator = /
  prefix = shared/$user/
  mail_driver = maildir
  # Owner path built like mail_home, to avoid a userdb lookup per owner.
  mail_path = %{home_dir}/%%{owner_user|domain}/%%{owner_user|username}/Maildir
  # Keeps the \Seen flag private to each user
  mail_index_private_path = ~/Maildir/shared/%%{owner_user}
  subscriptions = no
  list = children
}

acl_sharing_map {
  dict proxy {
    name = acl
  }
}
