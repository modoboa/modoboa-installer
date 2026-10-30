"""Modoboa compatibility matrix."""

# First Modoboa version providing the "deploy --redisurl" option
REDIS_URL_MIN_VERSION = "2.11.1"

EXTENSIONS_AVAILABILITY = {
    "modoboa-contacts": "1.7.4",
}

REMOVED_EXTENSIONS = {
    "modoboa-pdfcredentials": "2.1.0",
    "modoboa-dmarc": "2.1.0",
    "modoboa-imap-migration": "2.1.0",
    "modoboa-sievefilters": "2.3.0",
    "modoboa-postfix-autoreply": "2.3.0",
    "modoboa-contacts": "2.4.0",
    "modoboa-radicale": "2.4.0",
    "modoboa-webmail": "2.4.0",
}

APP_INCOMPATIBILITY = {
    "opendkim": ["rspamd"],
    "amavis": ["rspamd"],
    "postwhite": ["rspamd"],
    "spamassassin": ["rspamd"]
}
