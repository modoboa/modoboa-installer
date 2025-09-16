auth_mechanisms {
  xoauth2 = yes
  oauthbearer = yes
}

oauth2 {
  introspection_mode = post
  introspection_url = %{oauth2_introspection_url}
  #force_introspection = yes
  username_attribute = username
}

# with local validation
#oauth2 {
#  introspection_mode = local
#  username_attribute = email
#  oauth2_local_validation {
#    dict fs {
#      fs posix {
#        prefix = /etc/dovecot/oauth2-keys/
#      }
#    }
#  }
#}
