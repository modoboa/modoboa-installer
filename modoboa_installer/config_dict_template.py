import random
import string

from .constants import DEFAULT_BACKUP_DIRECTORY


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
        "name": "antispam",
        "values": [
            {
                "option": "enabled",
                "default": "true",
                "customizable": True,
                "values": ["true", "false"],
                "question": "Do you want to setup an antispam utility?"
            },
            {
                "option": "type",
                "default": "amavis",
                "customizable": True,
                "question": "Please select your antispam utility",
                "values": ["rspamd", "amavis"],
                "if": ["antispam.enabled=true"]
            }
        ]
    },
    {
        "name": "certificate",
        "values": [
            {
                "option": "type",
                "default": "self-signed",
                "customizable": True,
                "question": "Please choose your certificate type",
                "values": ["self-signed", "letsencrypt", "manual"],
                "non_interactive_values": ["manual"],
            },
            {
                "option": "tls_cert_file_path",
                "default": ""
            },
            {
                "option": "tls_key_file_path",
                "default": ""
            }
        ],
    },
    {
        "name": "letsencrypt",
        "if": ["certificate.type=letsencrypt"],
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
        "if": ["database.engine=postgres"],
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
        "if": ["database.engine=mysql"],
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
        "name": "fail2ban",
        "values": [
            {
                "option": "enabled",
                "default": "true",
            },
            {
                "option": "config_dir",
                "default": "/etc/fail2ban"
            },
            {
                "option": "max_retry",
                "default": "20"
            },
            {
                "option": "ban_time",
                "default": "3600"
            },
            {
                "option": "find_time",
                "default": "30"
            },
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
                "option": "cron_error_recipient",
                "default": "root",
                "customizable": True,
                "question":
                    "Please enter a mail recipient for cron error reports"
            },
            {
                "option": "extensions",
                "default": ""
            },
            {
                "option": "devmode",
                "default": "false",
            },
        ]
    },
    {
        "name": "rspamd",
        "if": ["antispam.enabled=true", "antispam.type=rspamd"],
        "values": [
            {
                "option": "enabled",
                "default": ["antispam.enabled=true", "antispam.type=rspamd"],
            },
            {
                "option": "user",
                "default": "_rspamd",
            },
            {
                "option": "password",
                "default": make_password,
                "customizable": True,
                "question": "Please enter Rspamd interface password",
            },
            {
                "option": "dnsbl",
                "default": "true",
            },
            {
                "option": "dkim_keys_storage_dir",
                "default": "/var/lib/dkim"
            },
            {
                "option": "key_map_path",
                "default": "/var/lib/dkim/keys.path.map"
            },
            {
                "option": "selector_map_path",
                "default": "/var/lib/dkim/selectors.path.map"
            },
            {
                "option": "greylisting",
                "default": "true"
            },
            {
                "option": "whitelist_auth",
                "default": "true"
            },
            {
                "option": "whitelist_auth_weigth",
                "default": "-5"
            }
        ],
    },
    {
        "name": "amavis",
        "values": [
            {
                "option": "enabled",
                "default": ["antispam.enabled=true", "antispam.type=amavis"],
            },
            {
                "option": "user",
                "default": "amavis",
            },
            {
                "option": "max_servers",
                "default": "2",
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
                "default": "dovecot",
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
            {
                "option": "radicale_auth_socket_path",
                "default": "/var/run/dovecot/auth-radicale",
            },
            {
                "option": "move_spam_to_junk",
                "default": "true",
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
                "default": "false",
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
            {
                "option": "dhe_group",
                "default": "4096"
            }
        ]
    },
    {
        "name": "postwhite",
        "values": [
            {
                "option": "enabled",
                "default": ["antispam.enabled=true", "antispam.type=amavis"],
            },
            {
                "option": "config_dir",
                "default": "/etc",
            },
        ]
    },
    {
        "name": "spamassassin",
        "if": ["antispam.enabled=true", "antispam.type=amavis"],
        "values": [
            {
                "option": "enabled",
                "default": ["antispam.enabled=true", "antispam.type=amavis"],
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
                "default": "4",
            },
        ]
    },
    {
        "name": "radicale",
        "values": [
            {
                "option": "enabled",
                "default": "true",
            },
            {
                "option": "user",
                "default": "radicale",
            },
            {
                "option": "config_dir",
                "default": "/etc/radicale",
            },
            {
                "option": "home_dir",
                "default": "/srv/radicale",
            },
            {
                "option": "venv_path",
                "default": "%(home_dir)s/env",
            }
        ]
    },
    {
        "name": "opendkim",
        "if": ["antispam.enabled=true", "antispam.type=amavis"],
        "values": [
            {
                "option": "enabled",
                "default": ["antispam.enabled=true", "antispam.type=amavis"],
            },
            {
                "option": "user",
                "default": "opendkim",
            },
            {
                "option": "config_dir",
                "default": "/etc",
            },
            {
                "option": "port",
                "default": "12345"
            },
            {
                "option": "keys_storage_dir",
                "default": "/var/lib/dkim"
            },
            {
                "option": "dbuser",
                "default": "opendkim",
            },
            {
                "option": "dbpassword",
                "default": make_password,
                "customizable": True,
                "question": "Please enter OpenDKIM db password"
            },

        ]
    },
    {
        "name": "backup",
        "values": [
            {
                "option": "default_path",
                "default": DEFAULT_BACKUP_DIRECTORY
            }
        ]
    }
]
