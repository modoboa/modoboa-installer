# Modoboas configuration for postfix

## -- General --
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

compatibility_level = 3.10

## ------------------

## -- Proxy maps --
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

# -------------------

## -- TLS settings --

tls_config_file = /etc/postfix/openssl.cnf
tls_config_name = postfix

tls_preempt_cipherlist = yes
tls_ssl_options = NO_COMPRESSION


### -- SMTPD --
smtpd_tls_security_level = may
smtpd_tls_auth_only = no
smtpd_tls_CApath = /etc/ssl/certs
smtpd_tls_chain_files =
        $tls_key_file,
        $tls_cert_file
smtpd_tls_loglevel = 1
smtpd_tls_session_cache_database = btree:$data_directory/smtpd_tls_session_cache
smtpd_tls_received_header = yes

# Only accept TLS1.2+ and secure ciphers
smtpd_tls_protocols = >=TLSv1.2
smtpd_tls_mandatory_protocols = $smtpd_tls_protocols

smtpd_tls_ciphers = high
smtpd_tls_mandatory_ciphers = $smtpd_tls_ciphers
smtpd_tls_exclude_ciphers = aNULL, ECDHE-ECDSA-CAMELLIA256-SHA384, ECDHE-ECDSA-ARIA128-GCM-SHA256, ECDHE-ECDSA-CAMELLIA128-SHA256, ECDHE-ECDSA-AES256-SHA384, ECDHE-ECDSA-AES256-SHA, ECDHE-ECDSA-AES128-SHA, ECDHE-ECDSA-ARIA256-GCM-SHA384, ECDHE-ECDSA-AES128-SHA256
smtpd_tls_mandatory_exclude_ciphers = $smtpd_tls_exclude_ciphers

### -- SMTP --
# Use DANE TLS if this is supported by the remote SMTP server,
# otherwise use STARTTLS, or plaintext.
%{dnssec_resolver}smtp_dns_support_level = dnssec
smtp_tls_security_level = %{smtp_security_level}
smtp_tls_CApath = /etc/ssl/certs
smtp_tls_session_cache_database = btree:$data_directory/smtp_tls_session_cache

smtp_tls_protocols = >=TLSv1.2
smtp_tls_mandatory_protocols = $smtp_tls_protocols

smtp_tls_ciphers = high
smtp_tls_mandatory_ciphers = $smtp_tls_ciphers
smtp_tls_exclude_ciphers = $smtpd_tls_exclude_ciphers
smtp_tls_mandatory_exclude_ciphers = $smtp_tls_exclude_ciphers

smtp_tls_loglevel = 1
## --------------------

# SMTP Smuggling prevention
# See https://www.postfix.org/smtp-smuggling.html
smtpd_data_restrictions = reject_unauth_pipelining
smtpd_forbid_unauth_pipelining = yes


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
%{rspamd_enabled}non_smtpd_milters = inet:localhost:11332
%{rspamd_enabled}milter_default_action = accept
%{rspamd_enabled}milter_protocol = 6

# List of authorized senders
smtpd_sender_login_maps =
        proxy:%{db_driver}:/etc/postfix/sql-sender-login-map.cf

# Add authenticated header to hide public client IP
smtpd_sasl_authenticated_header = yes

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

%{rspamd_disabled}postscreen_greet_banner = Welcome, please wait...
%{rspamd_disabled}postscreen_greet_action = enforce

%{rspamd_disabled}postscreen_pipelining_enable = yes
%{rspamd_disabled}postscreen_pipelining_action = enforce

%{rspamd_disabled}postscreen_non_smtp_command_enable = yes
%{rspamd_disabled}postscreen_non_smtp_command_action = enforce

%{rspamd_disabled}postscreen_bare_newline_enable = yes
%{rspamd_disabled}postscreen_bare_newline_action = enforce
