"""Rspamd related functions."""

import os
import pwd
import shutil
import stat

from .. import package
from .. import utils
from .. import system

from . import base
from . import redis
from . import install


class Rspamd(base.Installer):
    """Rspamd installer."""

    appname = "rspamd"
    packages = {
        "deb": [
            "rspamd"
        ]
    }
    config_files = [
        "local.d/arc.conf",
        "local.d/dkim_signing.conf",
        "local.d/dmarc.conf",
        "local.d/force_actions.conf",
        "local.d/greylist.conf",
        "local.d/metrics.conf",
        "local.d/milter_headers.conf",
        "local.d/mx_check.conf",
        "local.d/redis.conf",
        "local.d/settings.conf",
        "local.d/spf.conf",
        "local.d/worker-normal.inc",
        "local.d/worker-proxy.inc",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generate_password_condition = (
            not self.upgrade or utils.user_input(
                "Do you want to (re)generate rspamd password ? (y/N)").lower().startswith("y")
        )

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
        if self.generate_password_condition:
            _config_files.append("local.d/worker-controller.inc")
        return _config_files

    def get_template_context(self):
        _context = super().get_template_context()
        _context["greylisting_disabled"] = "" if not self.app_config["greylisting"].lower() == "true" else "#"
        redis_host, redis_port, redis_password = redis.get_settings(self.config)
        _context["redis_host"] = redis.format_host(redis_host)
        _context["redis_port"] = redis_port
        _context["redis_password_line"] = (
            'password = "{}";'.format(
                redis_password.replace("\\", "\\\\").replace('"', '\\"'))
            if redis_password else ""
        )
        _context["whitelist_auth_enabled"] = "" if self.app_config["whitelist_auth"].lower() == "true" else "#"
        if self.generate_password_condition:
            code, controller_password = utils.exec_cmd(
                r"rspamadm pw -p {}".format(self.app_config["password"]))
            if code != 0:
                utils.error("Error setting rspamd password. "
                            "Please make sure it is not 'q1' or 'q2'."
                            "Storing the password in plain. See"
                            "https://rspamd.com/doc/quickstart.html#setting-the-controller-password")
                _context["controller_password"] = self.app_config["password"]
            else:
                controller_password = controller_password.decode().replace("\n", "")
                _context["controller_password"] = controller_password
        return _context

    def post_run(self):
        """Additional tasks."""
        user = self.config.get(self.appname, "user")
        system.add_user_to_group(
            self.config.get("modoboa", "user"),
            user
        )
        for fname in ["redis.conf", "greylist.conf", "worker-controller.inc"]:
            self.protect_file(
                os.path.join(self.config_dir, "local.d", fname), user)
        if self.config.getboolean("clamav", "enabled"):
            install("clamav", self.config, self.upgrade, self.archive_path)

    def custom_backup(self, path):
        """Backup custom configuration and DKIM keys."""
        custom_config_dir = os.path.join(self.config_dir, "local.d")
        custom_backup_dir = os.path.join(path, "rspamd")
        os.makedirs(custom_backup_dir, exist_ok=True)
        for fname in os.listdir(custom_config_dir):
            file_path = os.path.join(custom_config_dir, fname)
            if os.path.isfile(file_path):
                utils.copy_file(file_path, custom_backup_dir)
        utils.success("Rspamd custom configuration saved!")
        dkim_keys_dir = self.app_config["dkim_keys_storage_dir"]
        if os.path.isdir(dkim_keys_dir):
            shutil.copytree(dkim_keys_dir, os.path.join(path, "dkim"))
            utils.success("DKIM keys saved!")

    def restore(self):
        """Restore custom config files and DKIM keys."""
        custom_backup_dir = os.path.join(self.archive_path, "custom/rspamd")
        if os.path.isdir(custom_backup_dir):
            custom_config_dir = os.path.join(self.config_dir, "local.d")
            for fname in os.listdir(custom_backup_dir):
                utils.copy_file(
                    os.path.join(custom_backup_dir, fname), custom_config_dir)
            utils.success("Custom Rspamd configuration restored.")
        dkim_keys_backup = os.path.join(self.archive_path, "custom/dkim")
        if os.path.isdir(dkim_keys_backup):
            dkim_keys_dir = self.app_config["dkim_keys_storage_dir"]
            shutil.copytree(
                dkim_keys_backup, dkim_keys_dir, dirs_exist_ok=True)
            user = self.config.get(self.appname, "user")
            utils.exec_cmd(f"chown -R {user}:{user} {dkim_keys_dir}")
            utils.success("DKIM keys restored from backup")
