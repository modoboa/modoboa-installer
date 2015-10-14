inet_interfaces = all
inet_protocols = ipv4
myhostname = %hostname
myorigin = $myhostname
mydestination =
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
smtpd_banner = $myhostname ESMTP
biff = no
unknown_local_recipient_reject_code = 550
unverified_recipient_reject_code = 550

# appending .domain is the MUA's job.
append_dot_mydomain = no

# Uncomment the next line to generate "delayed mail" warnings
#delay_warning_time = 4h

readme_directory = no

mailbox_size_limit = 0
message_size_limit = %message_size_limit
recipient_delimiter = +

alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases

## TLS settings
#
smtpd_use_tls = yes
smtpd_tls_auth_only = no
smtpd_tls_key_file = %tls_key_file
smtpd_tls_cert_file = %tls_cert_file
smtpd_tls_loglevel = 1
smtpd_tls_session_cache_database = btree:$data_directory/smtpd_tls_session_cache
smtpd_tls_security_level = may
smtpd_tls_received_header = yes

## Virtual transport settings
#
%{dovecot_enabled}virtual_transport = lmtp:unix:private/dovecot-lmtp

virtual_mailbox_domains = %{db_driver}:/etc/postfix/sql-domains.cf
virtual_alias_domains = %{db_driver}:/etc/postfix/sql-domain-aliases.cf
virtual_alias_maps =
        %{db_driver}:/etc/postfix/sql-aliases.cf
        %{db_driver}:/etc/postfix/sql-domain-aliases-mailboxes.cf
        %{db_driver}:/etc/postfix/sql-autoreplies.cf
        %{db_driver}:/etc/postfix/sql-mailboxes-self-aliases.cf
        %{db_driver}:/etc/postfix/sql-catchall-aliases.cf

## Relay domains
#
relay_domains =
        %{db_driver}:/etc/postfix/sql-relaydomains.cf
transport_maps =
	%{db_driver}:/etc/postfix/sql-relaydomains-transport.cf 
	%{db_driver}:/etc/postfix/sql-relaydomain-aliases-transport.cf
        %{db_driver}:/etc/postfix/sql-autoreplies-transport.cf

## SASL authentication through Dovecot
#
%{dovecot_enabled}smtpd_sasl_type = dovecot
%{dovecot_enabled}smtpd_sasl_path = private/auth
%{dovecot_enabled}smtpd_sasl_auth_enable = yes
%{dovecot_enabled}broken_sasl_auth_clients = yes
%{dovecot_enabled}smtpd_sasl_security_options = noanonymous

## SMTP session policies
#

# We require HELO to check it later
smtpd_helo_required = yes

# We do not let others find out which recipients are valid
disable_vrfy_command = yes

# MTA to MTA communication on Port 25. We expect (!) the other party to
# specify messages as required by RFC 821.
strict_rfc821_envelopes = yes

# Verify cache setup
%{dovecot_enabled}address_verify_map = proxy:btree:$data_directory/verify_cache

%{dovecot_enabled}proxy_write_maps =
%{dovecot_enabled}    $smtp_sasl_auth_cache_name
%{dovecot_enabled}    $lmtp_sasl_auth_cache_name
%{dovecot_enabled}    $address_verify_map

smtpd_sender_login_maps =
        %{db_driver}:/etc/postfix/sql-sender-login-mailboxes.cf
        %{db_driver}:/etc/postfix/sql-sender-login-aliases.cf

# Recipient restriction rules
smtpd_recipient_restrictions =
      permit_mynetworks
      permit_sasl_authenticated
      check_recipient_access
          %{db_driver}:/etc/postfix/sql-maintain.cf
          %{db_driver}:/etc/postfix/sql-relay-recipient-verification.cf
      reject_unverified_recipient
      reject_unauth_destination
      reject_non_fqdn_sender
      reject_non_fqdn_recipient
      reject_non_fqdn_helo_hostname

## Postcreen settings
#
postscreen_access_list =
       permit_mynetworks
postscreen_blacklist_action = enforce 

postscreen_dnsbl_sites = 
	zen.spamhaus.org*3 
	bl.spameatingmonkey.net*2 
	dnsbl.habl.org 
	bl.spamcop.net 
	dnsbl.sorbs.net 
postscreen_dnsbl_threshold = 3 
postscreen_dnsbl_action = enforce 

postscreen_greet_banner = Welcome, please wait... 
postscreen_greet_action = enforce

postscreen_pipelining_enable = yes
postscreen_pipelining_action = enforce

postscreen_non_smtp_command_enable = yes
postscreen_non_smtp_command_action = enforce

postscreen_bare_newline_enable = yes
postscreen_bare_newline_action = enforce
