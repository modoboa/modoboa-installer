"""Rspamd related functions."""

import os
import pwd
import stat

from .. import package
from .. import utils
from .. import system

from . import base
from . import install


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
                    "local.d/worker-proxy.inc",
                    "local.d/greylist.conf",
                    "local.d/milter_headers.conf",
                    "local.d/metrics.conf"]

    @property
    def config_dir(self):
        """Return appropriate config dir."""
        return "/etc/rspamd"

    def install_packages(self):
        debian_based_dist, codename = utils.is_dist_debian_based()
        if debian_based_dist:
            utils.mkdir_safe(
                "/etc/apt/keyrings",
                stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
                stat.S_IROTH | stat.S_IXOTH,
                0, 0
            )

            if codename == "bionic":
                package.backend.install("software-properties-common")
                utils.exec_cmd("add-apt-repository ppa:ubuntu-toolchain-r/test")

            package.backend.add_custom_repository(
                "rspamd",
                "http://rspamd.com/apt-stable/",
                "https://rspamd.com/apt-stable/gpg.key",
                codename
            )
            package.backend.update()

        return super().install_packages()

    def install_config_files(self):
        """Make sure config directory exists."""
        user = self.config.get(self.appname, "user")
        pw = pwd.getpwnam(user)
        targets = [
            [self.app_config["dkim_keys_storage_dir"], pw[2], pw[3]]
        ]
        for target in targets:
            if not os.path.exists(target[0]):
                utils.mkdir(
                    target[0],
                    stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
                    stat.S_IROTH | stat.S_IXOTH,
                    target[1], target[2]
                )
        super().install_config_files()

    def get_config_files(self):
        """Return appropriate config files."""
        _config_files = self.config_files
        if self.config.getboolean("clamav", "enabled"):
            _config_files.append("local.d/antivirus.conf")
        if self.app_config["dnsbl"].lower() == "true":
            _config_files.append("local.d/rbl.conf")
        if self.app_config["whitelist_auth"].lower() == "true":
            _config_files.append("local.d/groups.conf")
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
            _context["controller_password"] = self.app_config["password"]
        else:
            _context["controller_password"] = controller_password
        _context["greylisting_disabled"] = "" if not self.app_config["greylisting"].lower() == "true" else "#"
        _context["whitelist_auth_enabled"] = "" if self.app_config["whitelist_auth"].lower() == "true" else "#"
        return _context

    def post_run(self):
        """Additional tasks."""
        user = self.config.get(self.appname, "user")
        system.add_user_to_group(
            self.config.get("modoboa", "user"),
            user
        )
        if self.config.getboolean("clamav", "enabled"):
            install("clamav", self.config, self.upgrade, self.archive_path)

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
        custom_backup_dir = os.path.join(self.archive_path, "/rspamd/")
        backed_up_files = [
            f for f in os.listdir(custom_backup_dir)
            if os.path.isfile(custom_backup_dir, f)
        ]
        for f in backed_up_files:
            utils.copy_file(f, custom_config_dir)
        utils.success("Custom Rspamd configuration restored.")
