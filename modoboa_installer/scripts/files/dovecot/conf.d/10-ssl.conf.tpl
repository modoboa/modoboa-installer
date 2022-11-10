##
## SSL settings
##

# SSL/TLS support: yes, no, required. <doc/wiki/SSL.txt>
#ssl = yes

# Workarround https://github.com/modoboa/modoboa/issues/2570 
# We try to load the key and pass if it fails
# Keys require root permissions, standard commands would be blocked
# because dovecot can't load these cert
!include_try /etc/dovecot/conf.d/10-ssl-keys.try

# If key file is password protected, give the password here. Alternatively
# give it when starting dovecot with -p parameter. Since this file is often
# world-readable, you may want to place this setting instead to a different
# root owned 0600 file by using ssl_key_password = <path.
#ssl_key_password =

# PEM encoded trusted certificate authority. Set this only if you intend to use
# ssl_verify_client_cert=yes. The file should contain the CA certificate(s)
# followed by the matching CRL(s). (e.g. ssl_ca = </etc/ssl/certs/ca.pem)
#ssl_ca = 

# Require that CRL check succeeds for client certificates.
#ssl_require_crl = yes

# Request client to send a certificate. If you also want to require it, set
# auth_ssl_require_client_cert=yes in auth section.
#ssl_verify_client_cert = no

# Which field from certificate to use for username. commonName and
# x500UniqueIdentifier are the usual choices. You'll also need to set
# auth_ssl_username_from_cert=yes.
#ssl_cert_username_field = commonName

# How often to regenerate the SSL parameters file. Generation is quite CPU
# intensive operation. The value is in hours, 0 disables regeneration
# entirely.
#ssl_parameters_regenerate = 168

# SSL protocols to use
%ssl_protocol_parameter = %ssl_protocols


# SSL ciphers to use
ssl_cipher_list = EECDH+ECDSA+AESGCM:EECDH+aRSA+AESGCM:EECDH+ECDSA+SHA384:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA384:EECDH+aRSA+SHA256:EECDH+aRSA+RC4:EECDH:EDH+aRSA:!aNULL:!eNULL:!LOW:!3DES:!MD5:!EXP:!PSK:!SRP:!DSS:!RC4

# SSL crypto device to use, for valid values run "openssl engine"
#ssl_crypto_device =
