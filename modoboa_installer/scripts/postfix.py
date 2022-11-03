"""Postfix related tools."""

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os

from .. import package
from .. import utils

from . import base
from . import install


class Postfix(base.Installer):

    """Postfix installer."""

    appname = "postfix"
    packages = {
        "deb": ["postfix"],
        "rpm": ["postfix"],
    }
    config_files = ["main.cf", "master.cf"]

    def get_packages(self):
        """Additional packages."""
        if package.backend.FORMAT == "deb":
            packages = ["postfix-{}".format(self.db_driver)]
        else:
            packages = []
        return super(Postfix, self).get_packages() + packages

    def install_packages(self):
        """Preconfigure postfix package installation."""
        if "centos" in utils.dist_name():
            config = configparser.ConfigParser()
            with open("/etc/yum.repos.d/CentOS-Base.repo") as fp:
                config.read_file(fp)
            config.set("centosplus", "enabled", "1")
            config.set("centosplus", "includepkgs", "postfix-*")
            config.set("base", "exclude", "postfix-*")
            config.set("updates", "exclude", "postfix-*")
            with open("/etc/yum.repos.d/CentOS-Base.repo", "w") as fp:
                config.write(fp)

        package.backend.preconfigure(
            "postfix", "main_mailer_type", "select", "No configuration")
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
            "opendkim_port": self.config.get(
                "opendkim", "port")
        })
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

        # Generate EDH parameters
        if not os.path.exists("{}/dh2048.pem".format(self.config_dir)):
            cmd = "openssl dhparam -dsaparam -out dh2048.pem 2048"
            utils.exec_cmd(cmd, cwd=self.config_dir)

        # Generate /etc/aliases.db file to avoid warnings
        aliases_file = "/etc/aliases"
        if os.path.exists(aliases_file):
            utils.exec_cmd("postalias {}".format(aliases_file))

        # Postwhite
        install("postwhite", self.config, self.upgrade, self.restore)
