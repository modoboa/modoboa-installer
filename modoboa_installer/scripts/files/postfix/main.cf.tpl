inet_interfaces = all
inet_protocols = ipv4
myhostname = %hostname
myorigin = $myhostname
mydestination =
mynetworks = 127.0.0.0/8
smtpd_banner = $myhostname ESMTP
biff = no
unknown_local_recipient_reject_code = 550
unverified_recipient_reject_code = 550

# appending .domain is the MUA's job.
append_dot_mydomain = no

readme_directory = no

mailbox_size_limit = 0
message_size_limit = %message_size_limit
recipient_delimiter = +

alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases

## Proxy maps
proxy_read_maps =
        proxy:unix:passwd.byname
        proxy:%{db_driver}:/etc/postfix/sql-domains.cf
        proxy:%{db_driver}:/etc/postfix/sql-domain-aliases.cf
        proxy:%{db_driver}:/etc/postfix/sql-aliases.cf
        proxy:%{db_driver}:/etc/postfix/sql-relaydomains.cf
        proxy:%{db_driver}:/etc/postfix/sql-relaydomains-transport.cf
        proxy:%{db_driver}:/etc/postfix/sql-relaydomain-aliases-transport.cf
        proxy:%{db_driver}:/etc/postfix/sql-autoreplies-transport.cf
        proxy:%{db_driver}:/etc/postfix/sql-maintain.cf
        proxy:%{db_driver}:/etc/postfix/sql-relay-recipient-verification.cf
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-mailboxes.cf
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-aliases.cf
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-mailboxes-extra.cf
        proxy:%{db_driver}:/etc/postfix/sql-spliteddomains-transport.cf

## TLS settings
#
smtpd_use_tls = yes
smtpd_tls_auth_only = no
smtpd_tls_key_file = %tls_key_file
smtpd_tls_cert_file = %tls_cert_file
smtpd_tls_dh1024_param_file = ${config_directory}/dh2048.pem
smtpd_tls_loglevel = 1
smtpd_tls_session_cache_database = btree:$data_directory/smtpd_tls_session_cache
smtpd_tls_security_level = may
smtpd_tls_received_header = yes

# Disallow SSLv2 and SSLv3, only accept secure ciphers
smtpd_tls_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_ciphers = high
smtpd_tls_mandatory_exclude_ciphers = aNULL, MD5 , DES, ADH, RC4, PSD, SRP, 3DES, eNULL
smtpd_tls_exclude_ciphers = aNULL, MD5 , DES, ADH, RC4, PSD, SRP, 3DES, eNULL

# Enable elliptic curve cryptography
smtpd_tls_eecdh_grade = strong

# Use TLS if this is supported by the remote SMTP server, otherwise use plaintext.
smtp_tls_security_level = may
smtp_tls_loglevel = 1
smtp_tls_exclude_ciphers = EXPORT, LOW

## Virtual transport settings
#
%{dovecot_enabled}virtual_transport = lmtp:unix:private/dovecot-lmtp

virtual_mailbox_domains = proxy:%{db_driver}:/etc/postfix/sql-domains.cf
virtual_alias_domains = proxy:%{db_driver}:/etc/postfix/sql-domain-aliases.cf
virtual_alias_maps =
        proxy:%{db_driver}:/etc/postfix/sql-aliases.cf

## Relay domains
#
relay_domains =
        proxy:%{db_driver}:/etc/postfix/sql-relaydomains.cf
transport_maps =
        proxy:%{db_driver}:/etc/postfix/sql-spliteddomains-transport.cf
	proxy:%{db_driver}:/etc/postfix/sql-relaydomains-transport.cf 
        proxy:%{db_driver}:/etc/postfix/sql-autoreplies-transport.cf

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

# List of authorized senders
smtpd_sender_login_maps =
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-mailboxes.cf
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-aliases.cf
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-mailboxes-extra.cf

# Recipient restriction rules
smtpd_recipient_restrictions =
      permit_mynetworks
      permit_sasl_authenticated
      check_recipient_access
          proxy:%{db_driver}:/etc/postfix/sql-maintain.cf
          proxy:%{db_driver}:/etc/postfix/sql-relay-recipient-verification.cf
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

# Use some DNSBL
postscreen_dnsbl_sites = 
  b.barracudacentral.org=127.0.0.2*7
  dnsbl.inps.de=127.0.0.2*7
  bl.mailspike.net=127.0.0.2*5
  bl.mailspike.net=127.0.0.[10;11;12]*4
  dnsbl.sorbs.net=127.0.0.10*8
  dnsbl.sorbs.net=127.0.0.5*6
  dnsbl.sorbs.net=127.0.0.7*3
  dnsbl.sorbs.net=127.0.0.8*2
  dnsbl.sorbs.net=127.0.0.6*2
  dnsbl.sorbs.net=127.0.0.9*2
  zen.spamhaus.org=127.0.0.[10;11]*8
  zen.spamhaus.org=127.0.0.[4..7]*6
  zen.spamhaus.org=127.0.0.3*4
  zen.spamhaus.org=127.0.0.2*3
  hostkarma.junkemailfilter.com=127.0.0.2*3
  hostkarma.junkemailfilter.com=127.0.0.4*1
  hostkarma.junkemailfilter.com=127.0.1.2*1
  wl.mailspike.net=127.0.0.[18;19;20]*-2
  hostkarma.junkemailfilter.com=127.0.0.1*-2 
  bl.spameatingmonkey.net*2 
  dnsbl.habl.org 
  bl.spamcop.net 
postscreen_dnsbl_threshold = 8 
postscreen_dnsbl_action = enforce 

postscreen_greet_banner = Welcome, please wait... 
postscreen_greet_action = enforce

# Fix GMAIL ... Others ?
postscreen_pipelining_enable = no
# postscreen_pipelining_action = enforce

postscreen_non_smtp_command_enable = no
# postscreen_non_smtp_command_action = enforce

postscreen_bare_newline_enable = no
# postscreen_bare_newline_action = enforce
