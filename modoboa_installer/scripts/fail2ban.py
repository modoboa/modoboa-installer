"""fail2ban related functions."""

from . import base


class Fail2ban(base.Installer):
    """Fail2ban installer."""

    appname = "fail2ban"
    packages = {
        "deb": ["fail2ban"],
        "rpm": ["fail2ban"]
    }
    config_files = [
        "jail.d/modoboa.conf",
        "filter.d/modoboa-auth.conf",
    ]

    def get_config_files(self):
        config_files = super().get_config_files()

        if self.app_config["postfix_dovecot_filter"]:
            config_files += ["jail.d/postfix.conf",
                            "jail.d/dovecot.conf", 
                            "filter.d/postfix-modoboa.conf",
                            "filter.d/dovecot-modoboa.conf"]
        return config_files
