"""Amavis related functions."""

import os
import platform

from .. import package
from .. import utils

from . import base
from . import install


class Amavis(base.Installer):

    """Amavis installer."""

    appname = "amavis"
    packages = {
        "deb": [
            "libdbi-perl", "amavisd-new", "arc", "arj", "cabextract",
            "liblz4-tool", "lrzip", "lzop", "p7zip-full", "rpm2cpio",
            "unrar-free",
        ],
        "rpm": [
            "amavisd-new", "arj", "cabextract", "lz4", "lrzip",
            "lzop", "p7zip", "unar", "unzoo"
        ],
    }
    with_db = True

    @property
    def config_dir(self):
        """Return appropriate config dir."""
        if package.backend.FORMAT == "rpm":
            return "/etc/amavisd"
        return "/etc/amavis"

    def get_daemon_name(self):
        """Return appropriate daemon name."""
        if package.backend.FORMAT == "rpm":
            return "amavisd"
        return "amavis"

    def get_config_files(self):
        """Return appropriate config files."""
        if package.backend.FORMAT == "deb":
            return [
                "conf.d/05-node_id", "conf.d/15-content_filter_mode",
                "conf.d/50-user"]
        return ["amavisd.conf"]

    def get_packages(self):
        """Additional packages."""
        packages = super(Amavis, self).get_packages()
        if package.backend.FORMAT == "deb":
            db_driver = "pg" if self.db_driver == "pgsql" else self.db_driver
            return packages + ["libdbd-{}-perl".format(db_driver)]
        if self.db_driver == "pgsql":
            db_driver = "Pg"
        elif self.db_driver == "mysql":
            db_driver = "MySQL"
        else:
            raise NotImplementedError("DB driver not supported")
        return packages + ["perl-DBD-{}".format(db_driver)]

    def get_sql_schema_path(self):
        """Return schema path."""
        version = package.backend.get_installed_version("amavisd-new")
        if version is None:
            raise utils.FatalError("Amavis is not installed")
        path = self.get_file_path(
            "amavis_{}_{}.sql".format(self.dbengine, version))
        if not os.path.exists(path):
            version = ".".join(version.split(".")[:-1]) + ".X"
            path = self.get_file_path(
                "amavis_{}_{}.sql".format(self.dbengine, version))
            if not os.path.exists(path):
               raise utils.FatalError("Failed to find amavis database schema")
        return path

    def post_run(self):
        """Additional tasks."""
        with open("/etc/mailname", "w") as fp:
            fp.write("{}\n".format(self.config.get("general", "hostname")))
        install("spamassassin", self.config, self.upgrade)
        install("clamav", self.config, self.upgrade)
