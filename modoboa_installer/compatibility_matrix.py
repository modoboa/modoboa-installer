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
}

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
