"""Modoboa compatibility matrix."""

COMPATIBILITY_MATRIX = {
    "1.8.1": {
        "modoboa-pdfcredentials": "<=1.1.0",
        "modoboa-sievefilters": "<=1.1.0",
        "modoboa-webmail": "<=1.1.5",
    },
    "1.8.2": {
        "modoboa-pdfcredentials": ">=1.1.1",
        "modoboa-sievefilters": ">=1.1.1",
        "modoboa-webmail": ">=1.2.0",
    },
    "1.8.3": {
        "modoboa-pdfcredentials": ">=1.1.1",
        "modoboa-sievefilters": ">=1.1.1",
        "modoboa-webmail": ">=1.2.0",
    },
    "1.9.0": {
        "modoboa-pdfcredentials": ">=1.1.1",
        "modoboa-sievefilters": ">=1.1.1",
        "modoboa-webmail": ">=1.2.0",
    },
    "2.1.0": {
        "modoboa-pdfcredentials": None,
        "modoboa-dmarc": None,
        "modoboa-imap-migration": None,
    },
}

EXTENSIONS_AVAILABILITY = {
    "modoboa-contacts": "1.7.4",
}

APP_INCOMPATIBILITY = {
    "opendkim": ["rspamd"],
    "amavis": ["rspamd"],
    "postwhite": ["rspamd"],
    "spamassassin": ["rspamd"]
}
