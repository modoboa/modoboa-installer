"""Amavis related functions."""

import os

from .. import package
from .. import utils

from . import base
from . import backup, install


class Rspamd(base.Installer):

    """Rspamd installer."""

    appname = "rspamd"
    packages = {
        "deb": [
            "rspamd", "redis"
        ]
    }
    config_files = ["local.d/dkim_signing.conf",
                    "local.d/mx_check.conf",
                    "local.d/spf.conf",
                    "local.d/worker-controller.inc",
                    "local.d/worker-normal.inc",
                    "local.d/worker-proxy.inc"]

    @property
    def config_dir(self):
        """Return appropriate config dir."""
        return "/etc/rspamd"

    def get_config_files(self):
        """Return appropriate config files."""
        _config_files = self.config_files
        if self.config.get("clamav", "enabled"):
            _config_files.append("local.d/antivirus.conf")
        if self.app_config["dnsbl"]:
            _config_files.append("local.d/greylisting.conf")
        if not self.app_config["dnsbl"]:
            _config_files.append("local.d/rbl.conf")
        return _config_files

    def get_template_context(self):
        _context = super().get_template_context()
        code, controller_password = utils.exec_cmd(
            r"rspamadm pw -p {}".format(self.app_config["password"]))
        if code != 0:
            utils.error("Error setting rspamd password. "
                        "Please make sure it is not 'q1' or 'q2'."
                        "Storing the password in plain. See"
                        "https://rspamd.com/doc/quickstart.html#setting-the-controller-password")
            _context["controller_password"] = password
        else:
            _context["controller_password"] = controller_password
        return _context

    def custom_backup(self, path):
        """Backup custom configuration if any."""
        custom_config_dir = os.path.join(self.config_dir,
                                         "/local.d/")
        custom_backup_dir = os.path.join(path, "/rspamd/")
        local_files = [f for f in os.listdir(custom_config_dir)
                       if os.path.isfile(custom_config_dir, f)
                       ]
        for file in local_files:
            utils.copy_file(file, custom_backup_dir)
        if len(local_files) != 0:
            utils.success("Rspamd custom configuration saved!")

    def restore(self):
        """Restore custom config files."""
        custom_config_dir = os.path.join(self.config_dir,
                                         "/local.d/")
        custom_backup_dir = os.path.join(path, "/rspamd/")
        backed_up_files = [f for f in os.listdir(custom_backup_dir)
                           if os.path.isfile(custom_backup_dir, f)
                          ]
        for file in backed_up_files:
            utils.copy_file(file, custom_config_dir)
            utils.success("Custom Rspamd configuration restored.")
