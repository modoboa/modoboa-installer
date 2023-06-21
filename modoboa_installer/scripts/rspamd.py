"""Amavis related functions."""

import os

from .. import package
from .. import utils
from .. import system

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
                    "local.d/worker-proxy.inc",
                    "local.d/greylist.conf",
                    "local.d/milter_headers.conf",
                    "local.d/metrics.conf"]

    @property
    def config_dir(self):
        """Return appropriate config dir."""
        return "/etc/rspamd"

    def install_packages(self):
        status, codename = utils.exec_cmd("lsb_release -c -s")

        if codename.lower() in ["bionic", "bookworm", "bullseye", "buster",
                                "focal", "jammy", "jessie", "sid", "stretch",
                                "trusty", "wheezy", "xenial"]:
            utils.mkdir_safe("/etc/apt/keyrings")

            if codename.lower() == "bionic":
                package.backend.install("software-properties-common")
                utils.exec_cmd("add-apt-repository ppa:ubuntu-toolchain-r/test")

            utils.exec_cmd("wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key|sudo apt-key add -")
            utils.exec_cmd(f"echo \"deb http://apt.llvm.org/{codename}/ llvm-toolchain-{codename}-16 main\" | sudo tee /etc/apt/sources.list.d/llvm-16.list")
            utils.exec_cmd(f"echo \"deb-src http://apt.llvm.org/{codename}/ llvm-toolchain-{codename}-16 main\"  | sudo tee -a /etc/apt/sources.list.d/llvm-16.list")

            utils.exec_cmd("wget -O- https://rspamd.com/apt-stable/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/rspamd.gpg > /dev/null")
            utils.exec_cmd(f"echo \"deb [arch=amd64 signed-by=/etc/apt/keyrings/rspamd.gpg] http://rspamd.com/apt-stable/ {codename} main\" | sudo tee /etc/apt/sources.list.d/rspamd.list")
            utils.exec_cmd(f"echo \"deb-src [arch=amd64 signed-by=/etc/apt/keyrings/rspamd.gpg] http://rspamd.com/apt-stable/ {codename} main\"  | sudo tee -a /etc/apt/sources.list.d/rspamd.list")
            package.backend.update()

        return super().install_packages()

    def install_config_files(self):
        """Make sure config directory exists."""
        user = self.config.get("modoboa", "user")
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
            _context["controller_password"] = password
        else:
            _context["controller_password"] = controller_password
        _context["greylisting_disabled"] = "" if not self.app_config["greylisting"].lower() == "true" else "#"
        _context["whitelist_auth_enabled"] = "" if self.app_config["whitelist_auth"].lower() == "true" else "#"
        return _context

    def post_run(self):
        """Additional tasks."""
        system.add_user_to_group(
            self.config.get("modoboa", "user"),
            "_rspamd"
            )
        if self.config("clamav", "enabled"):
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
        custom_backup_dir = os.path.join(path, "/rspamd/")
        backed_up_files = [f for f in os.listdir(custom_backup_dir)
                           if os.path.isfile(custom_backup_dir, f)
                          ]
        for file in backed_up_files:
            utils.copy_file(file, custom_config_dir)
            utils.success("Custom Rspamd configuration restored.")
