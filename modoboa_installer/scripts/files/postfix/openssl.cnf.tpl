postfix = postfix_settings

[postfix_settings]
ssl_conf = postfix_ssl_settings

[postfix_ssl_settings]
system_default = baseline_postfix_settings

[baseline_postfix_settings]
SignatureAlgorithms = ECDSA+SHA256:ECDSA+SHA384:ECDSA+SHA512:RSA-PSS+SHA256:RSA-PSS+SHA384:RSA-PSS+SHA512:RSA+SHA512:RSA+SHA256:RSA+SHA384
