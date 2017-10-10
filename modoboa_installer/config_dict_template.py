import random
import string


def make_password(length=16):
    """Create a random password."""
    return "".join(
        random.SystemRandom().choice(
            string.ascii_letters + string.digits) for _ in range(length))


# Validators should return a tuple bool, error message
def is_email(user_input):
    """Return True in input is a valid email"""
    return "@" in user_input, "Please enter a valid email"


ConfigDictTemplate = [
        {
            "name": "general",
            "values": [
                {
                    "option": "hostname",
                    "default": "mail.%(domain)s",
                }
            ]
        },
        {
            "name": "certificate",
            "values": [
                {
                    "option": "generate",
                    "default": "true",
                },
                {
                    "option": "type",
                    "default": "self-signed",
                    "customizable": True,
                    "question": "Please choose your certificate type",
                    "values": ["self-signed", "letsencrypt"],
                }
            ],
        },
        {
            "name": "letsencrypt",
            "if": "certificate.type=letsencrypt",
            "values": [
                {
                    "option": "email",
                    "default": "admin@example.com",
                    "question": (
                        "Please enter the mail you wish to use for "
                        "letsencrypt"),
                    "customizable": True,
                    "validators": [is_email]
                }
            ]
        },
        {
            "name": "database",
            "values": [
                {
                    "option": "engine",
                    "default": "postgres",
                    "customizable": True,
                    "question": "Please choose your database engine",
                    "values": ["postgres", "mysql"],
                },
                {
                    "option": "host",
                    "default": "127.0.0.1",
                },
                {
                    "option": "install",
                    "default": "true",
                }
            ]
        },
        {
            "name": "postgres",
            "if": "database.engine=postgres",
            "values": [
                {
                    "option": "user",
                    "default": "postgres",
                },
                {
                    "option": "password",
                    "default": "",
                    "customizable": True,
                    "question": "Please enter postgres password",
                },
            ]
        },
        {
            "name": "mysql",
            "if": "database.engine=mysql",
            "values": [
                {
                    "option": "user",
                    "default": "root",
                },
                {
                    "option": "password",
                    "default": make_password,
                    "customizable": True,
                    "question": "Please enter mysql root password"
                },
                {
                    "option": "charset",
                    "default": "utf8",
                },
                {
                    "option": "collation",
                    "default": "utf8_general_ci",
                }
            ]
        },
        {
            "name": "modoboa",
            "values": [
                 {
                    "option": "user",
                    "default": "modoboa",
                 },
                 {
                    "option": "home_dir",
                    "default": "/srv/modoboa",
                 },
                 {
                    "option": "venv_path",
                    "default": "%(home_dir)s/env",
                 },
                 {
                    "option": "instance_path",
                    "default": "%(home_dir)s/instance",
                 },
                 {
                    "option": "timezone",
                    "default": "Europe/Paris",
                 },
                 {
                    "option": "dbname",
                    "default": "modoboa",
                 },
                 {
                    "option": "dbuser",
                    "default": "modoboa",
                 },
                 {
                    "option": "dbpassword",
                    "default": make_password,
                    "customizable": True,
                    "question": "Please enter Modoboa db password",
                 },
                 {
                    "option": "extensions",
                    "default": (
                        "modoboa-amavis modoboa-pdfcredentials "
                        "modoboa-postfix-autoreply modoboa-sievefilters "
                        "modoboa-stats modoboa-webmail modoboa-contacts"),
                 },
                 {
                    "option": "devmode",
                    "default": "false",
                 },
            ]
        },
        {
            "name": "automx",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "user",
                    "default": "automx",
                },
                {
                    "option": "config_dir",
                    "default": "/etc",
                },
                {
                    "option": "home_dir",
                    "default": "/srv/automx",
                },
                {
                    "option": "venv_path",
                    "default": "%(home_dir)s/env",
                },
                {
                    "option": "instance_path",
                    "default": "%(home_dir)s/instance",
                },
            ]
        },
        {
            "name": "amavis",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "user",
                    "default": "amavis",
                },
                {
                    "option": "max_servers",
                    "default": "1",
                },
                {
                    "option": "dbname",
                    "default": "amavis",
                },
                {
                    "option": "dbuser",
                    "default": "amavis",
                },
                {
                    "option": "dbpassword",
                    "default": make_password,
                    "customizable": True,
                    "question": "Please enter amavis db password"
                },
            ],
        },
        {
            "name": "clamav",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "user",
                    "default": "clamav",
                },
            ]
        },
        {
            "name": "dovecot",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "config_dir",
                    "default": "/etc/dovecot",
                },
                {
                    "option": "user",
                    "default": "vmail",
                },
                {
                    "option": "home_dir",
                    "default": "/srv/vmail",
                },
                {
                    "option": "mailboxes_owner",
                    "default": "vmail",
                },
                {
                    "option": "extra_protocols",
                    "default": "",
                },
                {
                    "option": "postmaster_address",
                    "default": "postmaster@%(domain)s",
                },
            ]
        },
        {
            "name": "nginx",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "config_dir",
                    "default": "/etc/nginx",
                },
            ],
        },
        {
            "name": "razor",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "config_dir",
                    "default": "/etc/razor",
                },
            ]
        },
        {
            "name": "postfix",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "config_dir",
                    "default": "/etc/postfix",
                },
                {
                    "option": "message_size_limit",
                    "default": "11534336",
                },
            ]
        },
        {
            "name": "spamassassin",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "config_dir",
                    "default": "/etc/mail/spamassassin",
                },
                {
                    "option": "dbname",
                    "default": "spamassassin",
                },
                {
                    "option": "dbuser",
                    "default": "spamassassin",
                },
                {
                    "option": "dbpassword",
                    "default": make_password,
                    "customizable": True,
                    "question": "Please enter spamassassin db password"
                },
            ]
        },
        {
            "name": "uwsgi",
            "values": [
                {
                    "option": "enabled",
                    "default": "true",
                },
                {
                    "option": "config_dir",
                    "default": "/etc/uwsgi",
                },
                {
                    "option": "nb_processes",
                    "default": "2",
                },
            ]
        },
]
