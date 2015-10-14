"""Postfix related tools."""

import os

from .. import utils

from . import base


class Postfix(base.Installer):

    """Postfix installer."""

    appname = "postfix"
    packages = ["postfix"]
    config_files = ["main.cf", "master.cf"]

    def get_packages(self):
        """Additional packages."""
        return self.packages + ["postfix-{}".format(self.db_driver)]

    def install_packages(self):
        """Preconfigure postfix package installation."""
        cfg = "postfix postfix/main_mailer_type select No configuration"
        utils.exec_cmd("echo '{}' | debconf-set-selections".format(cfg))
        super(Postfix, self).install_packages()

    def get_template_context(self):
        """Additional variables."""
        context = super(Postfix, self).get_template_context()
        context.update({
            "db_driver": self.db_driver,
            "dovecot_mailboxes_owner": self.config.get(
                "dovecot", "mailboxes_owner"),
            "modoboa_venv_path": self.config.get(
                "modoboa", "venv_path"),
            "modoboa_instance_path": self.config.get(
                "modoboa", "instance_path"),
        })
        return context

    def post_run(self):
        """Additional tasks."""
        venv_path = self.config.get("modoboa", "venv_path")
        python_path = os.path.join(venv_path, "bin", "python")
        script_path = os.path.join(venv_path, "bin", "modoboa-admin.py")
        db_url = "{}://{}:{}@{}/{}".format(
            self.dbengine, self.config.get("modoboa", "dbuser"),
            self.config.get("modoboa", "dbpassword"),
            self.dbhost, self.config.get("modoboa", "dbname"))
        cmd = (
            "{} {} postfix_maps --dbtype {} --extensions all --dburl {} {}"
            .format(python_path, script_path, self.dbengine, db_url,
                    self.config_dir))
        utils.exec_cmd(cmd)
