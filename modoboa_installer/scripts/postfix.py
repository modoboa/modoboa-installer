"""Postfix related tools."""

import os

from .. import package
from .. import utils

from . import base
from . import backup, install


class Postfix(base.Installer):
    """Postfix installer."""

    appname = "postfix"
    packages = ["postfix", "postfix-pcre"]
    config_files = ["main.cf", "master.cf", "anonymize_headers.pcre", "openssl.cnf"]

    def get_packages(self):
        """Additional packages."""
        return super().get_packages() + ["postfix-{}".format(self.db_driver)]

    def install_packages(self):
        """Preconfigure postfix package installation."""
        package.backend.preconfigure(
            "postfix", "main_mailer_type", "select", "No configuration")
        super().install_packages()

    def get_template_context(self):
        """Additional variables."""
        context = super().get_template_context()
        dnssec_ready = self.config.getboolean("postfix", "dnssec_resolver")
        context.update(
            {
                "db_driver": self.db_driver,
                "dovecot_mailboxes_owner": self.config.get(
                    "dovecot", "mailboxes_owner"
                ),
                "modoboa_venv_path": self.config.get("modoboa", "venv_path"),
                "modoboa_instance_path": self.config.get("modoboa", "instance_path"),
                "opendkim_port": self.config.get("opendkim", "port"),
                "rspamd_disabled": (
                    "" if not self.config.getboolean("rspamd", "enabled") else "#"
                ),
                "smtp_security_level": "dane" if dnssec_ready else "may",
                "dnssec_resolver": "" if dnssec_ready else "#",
            }
        )
        return context

    def post_run(self):
        """Additional tasks."""
        venv_path = self.config.get("modoboa", "venv_path")
        python_path = os.path.join(venv_path, "bin", "python")
        instance_path = self.config.get("modoboa", "instance_path")
        script_path = os.path.join(instance_path, "manage.py")
        cmd = (
            "{} {} generate_postfix_maps --destdir {} --force-overwrite"
            .format(python_path, script_path, self.config_dir))
        utils.exec_cmd(cmd)

        # Check chroot directory
        chroot_dir = "/var/spool/postfix/etc"
        chroot_files = ["services", "resolv.conf"]
        if not os.path.exists(chroot_dir):
            os.mkdir(chroot_dir)
        for f in chroot_files:
            path = os.path.join(chroot_dir, f)
            if not os.path.exists(path):
                utils.copy_file(os.path.join("/etc", f), path)

        # Generate /etc/aliases.db file to avoid warnings
        aliases_file = "/etc/aliases"
        if os.path.exists(aliases_file):
            utils.exec_cmd("postalias {}".format(aliases_file))

        # Postwhite
        condition = (
            not self.config.getboolean("rspamd", "enabled") and
            self.config.getboolean("postwhite", "enabled")
            )
        if condition:
            install("postwhite", self.config, self.upgrade, self.archive_path)

    def backup(self, path):
        """Launch postwhite backup."""
        condition = (
            not self.config.getboolean("rspamd", "enabled") and
            self.config.getboolean("postwhite", "enabled")
            )
        if condition:
            backup("postwhite", self.config, path)
