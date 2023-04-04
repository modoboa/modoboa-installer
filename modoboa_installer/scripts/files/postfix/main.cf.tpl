inet_interfaces = all
inet_protocols = all
myhostname = %hostname
myorigin = $myhostname
mydestination = $myhostname
mynetworks = 127.0.0.0/8 [::1]/128
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
        proxy:%{db_driver}:/etc/postfix/sql-maintain.cf
        proxy:%{db_driver}:/etc/postfix/sql-relay-recipient-verification.cf
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-map.cf
        proxy:%{db_driver}:/etc/postfix/sql-spliteddomains-transport.cf
        proxy:%{db_driver}:/etc/postfix/sql-transport.cf

## TLS settings
#
smtpd_use_tls = yes
smtpd_tls_auth_only = no
smtpd_tls_CApath = /etc/ssl/certs
smtpd_tls_key_file = %tls_key_file
smtpd_tls_cert_file = %tls_cert_file
smtpd_tls_dh1024_param_file = ${config_directory}/ffdhe%{dhe_group}.pem
smtpd_tls_loglevel = 1
smtpd_tls_session_cache_database = btree:$data_directory/smtpd_tls_session_cache
smtpd_tls_security_level = may
smtpd_tls_received_header = yes

# Disallow SSLv2 and SSLv3, only accept secure ciphers
smtpd_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_ciphers = high
smtpd_tls_mandatory_exclude_ciphers = aNULL, eNULL, EXPORT, DES, RC4, MD5, PSK, aECDH, EDH-DSS-DES-CBC3-SHA, EDH-RSA-DES-CBC3-SHA, KRB5-DES, CBC3-SHA, CAMELLIA, SEED-SHA, AES256-SHA, AES256-SHA256, AES256-GCM-SHA384, AES128-SHA, AES128-SHA256, AES128-GCM-SHA256, DHE-RSA-AES128-GCM-SHA256, DHE-RSA-AES128-SHA, DHE-RSA-AES128-SHA256, DHE-RSA-AES256-GCM-SHA384, DHE-RSA-AES256-SHA, DHE-RSA-AES256-SHA256, DHE-RSA-CHACHA20-POLY1305, ECDHE-RSA-AES128-SHA, ECDHE-RSA-AES256-SHA
smtpd_tls_exclude_ciphers = aNULL, eNULL, EXPORT, DES, RC4, MD5, PSK, aECDH, EDH-DSS-DES-CBC3-SHA, EDH-RSA-DES-CBC3-SHA, KRB5-DES, CBC3-SHA, CAMELLIA, SEED-SHA, AES256-SHA, AES256-SHA256, AES256-GCM-SHA384, AES128-SHA, AES128-SHA256, AES128-GCM-SHA256, DHE-RSA-AES128-GCM-SHA256, DHE-RSA-AES128-SHA, DHE-RSA-AES128-SHA256, DHE-RSA-AES256-GCM-SHA384, DHE-RSA-AES256-SHA, DHE-RSA-AES256-SHA256, DHE-RSA-CHACHA20-POLY1305, ECDHE-RSA-AES128-SHA, ECDHE-RSA-AES256-SHA
tls_preempt_cipherlist = yes
tls_ssl_options = NO_COMPRESSION

# Enable elliptic curve cryptography
smtpd_tls_eecdh_grade = strong

# SMTP Smuggling prevention
# See https://www.postfix.org/smtp-smuggling.html
smtpd_data_restrictions = reject_unauth_pipelining
smtpd_forbid_unauth_pipelining = yes

# Use TLS if this is supported by the remote SMTP server, otherwise use plaintext.
smtp_tls_CApath = /etc/ssl/certs
smtp_tls_security_level = may
smtp_tls_loglevel = 1
smtp_tls_exclude_ciphers = EXPORT, LOW

## Virtual transport settings
#
%{dovecot_enabled}virtual_transport = lmtp:unix:private/dovecot-lmtp

%{dovecot_enabled}virtual_mailbox_domains = proxy:%{db_driver}:/etc/postfix/sql-domains.cf
%{dovecot_enabled}virtual_alias_domains = proxy:%{db_driver}:/etc/postfix/sql-domain-aliases.cf
%{dovecot_enabled}virtual_alias_maps =
%{dovecot_enabled}        proxy:%{db_driver}:/etc/postfix/sql-aliases.cf

## Relay domains
#
relay_domains =
        proxy:%{db_driver}:/etc/postfix/sql-relaydomains.cf
transport_maps =
	proxy:%{db_driver}:/etc/postfix/sql-transport.cf
        proxy:%{db_driver}:/etc/postfix/sql-spliteddomains-transport.cf

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

# OpenDKIM setup
%{opendkim_enabled}smtpd_milters = inet:127.0.0.1:%{opendkim_port}
%{opendkim_enabled}non_smtpd_milters = inet:127.0.0.1:%{opendkim_port}
%{opendkim_enabled}milter_default_action = accept
%{opendkim_enabled}milter_content_timeout = 30s

# Rspamd setup
%{rspamd_enabled}smtpd_milters = inet:localhost:11332
%{rspamd_enabled}milter_default_action = accept
%{rspamd_enabled}milter_protocol = 6

# List of authorized senders
smtpd_sender_login_maps =
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-map.cf

# Recipient restriction rules
smtpd_recipient_restrictions =
      check_policy_service inet:127.0.0.1:9999
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
%{rspamd_disabled}postscreen_access_list =
%{rspamd_disabled}       permit_mynetworks
%{rspamd_disabled}      cidr:/etc/postfix/postscreen_spf_whitelist.cidr
%{rspamd_disabled}postscreen_blacklist_action = enforce

# Use some DNSBL
%{rspamd_disabled}postscreen_dnsbl_sites =
%{rspamd_disabled}	zen.spamhaus.org=127.0.0.[2..11]*3
%{rspamd_disabled}	bl.spameatingmonkey.net=127.0.0.2*2
%{rspamd_disabled}	bl.spamcop.net=127.0.0.2
%{rspamd_disabled}postscreen_dnsbl_threshold = 3
%{rspamd_disabled}postscreen_dnsbl_action = enforce

postscreen_greet_banner = Welcome, please wait... 
postscreen_greet_action = enforce

postscreen_pipelining_enable = yes
postscreen_pipelining_action = enforce

postscreen_non_smtp_command_enable = yes
postscreen_non_smtp_command_action = enforce

postscreen_bare_newline_enable = yes
postscreen_bare_newline_action = enforce
