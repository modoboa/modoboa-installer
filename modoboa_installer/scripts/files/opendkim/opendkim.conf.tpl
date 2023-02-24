# This is a basic configuration that can easily be adapted to suit a standard
# installation. For more advanced options, see opendkim.conf(5) and/or
# /usr/share/doc/opendkim/examples/opendkim.conf.sample.

# Log to syslog
Syslog			yes
SyslogSuccess   	Yes
LogWhy			Yes
LogResults  Yes

# Required to use local socket with MTAs that access the socket as a non-
# privileged user (e.g. Postfix)
UMask			007

# Sign for example.com with key in /etc/dkimkeys/dkim.key using
# selector '2007' (e.g. 2007._domainkey.example.com)
#Domain			example.com
#KeyFile		/etc/dkimkeys/dkim.key
#Selector		2007

KeyTable		dsn:%{db_driver}://%{db_user}:%{db_password}@%{dbport}+%{dbhost}/%{db_name}/table=dkim?keycol=id?datacol=domain_name,selector,private_key_path
SigningTable		dsn:%db_driver://%{db_user}:%{db_password}@%{dbport}+%{dbhost}/%{db_name}/table=dkim?keycol=domain_name?datacol=id

# Commonly-used options; the commented-out versions show the defaults.
#Canonicalization	simple
#Mode			sv
SubDomains		yes	
Canonicalization        relaxed/relaxed

# Socket smtp://localhost
#
# ##  Socket socketspec
# ##
# ##  Names the socket where this filter should listen for milter connections
# ##  from the MTA.  Required.  Should be in one of these forms:
# ##
# ##  inet:port@address           to listen on a specific interface
# ##  inet:port                   to listen on all interfaces
# ##  local:/path/to/socket       to listen on a UNIX domain socket
#
Socket                  inet:%{port}@localhost
#Socket			local:/var/run/opendkim/opendkim.sock

##  PidFile filename
###      default (none)
###
###  Name of the file where the filter should write its pid before beginning
###  normal operations.
#
PidFile               /var/run/opendkim/opendkim.pid


# Always oversign From (sign using actual From and a null From to prevent
# malicious signatures header fields (From and/or others) between the signer
# and the verifier.  From is oversigned by default in the Debian pacakge
# because it is often the identity key used by reputation systems and thus
# somewhat security sensitive.
OversignHeaders		From

##  ResolverConfiguration filename
##      default (none)
##
##  Specifies a configuration file to be passed to the Unbound library that
##  performs DNS queries applying the DNSSEC protocol.  See the Unbound
##  documentation at http://unbound.net for the expected content of this file.
##  The results of using this and the TrustAnchorFile setting at the same
##  time are undefined.
##  In Debian, /etc/unbound/unbound.conf is shipped as part of the Suggested
##  unbound package

# ResolverConfiguration     /etc/unbound/unbound.conf

##  TrustAnchorFile filename
##      default (none)
##
## Specifies a file from which trust anchor data should be read when doing
## DNS queries and applying the DNSSEC protocol.  See the Unbound documentation
## at http://unbound.net for the expected format of this file.

# TrustAnchorFile       /usr/share/dns/root.key

##  Userid userid
###      default (none)
###
###  Change to user "userid" before starting normal operation?  May include
###  a group ID as well, separated from the userid by a colon.
#
UserID                %{user}

ExternalIgnoreList      /etc/opendkim.hosts
InternalHosts           /etc/opendkim.hosts
