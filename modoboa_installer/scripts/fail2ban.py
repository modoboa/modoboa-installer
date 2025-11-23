"""fail2ban related functions."""

import os

from . import base
from .. import utils


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
        """Add dovecot and postfix jails if enabled."""

        config_files = super().get_config_files()

        if self.app_config["postfix_dovecot_filter"].lower() == "true":
            config_files += ["jail.d/postfix.conf",
                            "jail.d/dovecot.conf"]
        return config_files

    def install_config_files(self):
        """Installer postfix and dovecot filters if enabled."""

        if self.app_config["postfix_dovecot_filter"].lower() == "true":
            for config_file in ["filter.d/postfix-modoboa.conf",
                                "filter.d/dovecot-modoboa.conf"]:
                src = self.get_file_path(config_file)
                dst = os.path.join(self.config_dir, config_file)
                utils.copy_file(src, dst)
        super().install_config_files()
