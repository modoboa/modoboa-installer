"""Amavis related functions."""

import os

from .. import package
from .. import utils

from . import base
from . import backup, install


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
            "amavis", "arj", "lz4", "lzop", "p7zip",
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
        packages += ["perl-DBD-{}".format(db_driver)]
        name, version = utils.dist_info()
        if version.startswith('7'):
            packages += ["cabextract", "lrzip", "unar", "unzoo"]
        elif version.startswith('8'):
            packages += ["perl-IO-stringy"]
        return packages

    def get_sql_schema_path(self):
        """Return schema path."""
        version = package.backend.get_installed_version("amavisd-new")
        if version is None:
            # Fallback to amavis...
            version = package.backend.get_installed_version("amavis")
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

    def pre_run(self):
        """Tasks to run first."""
        with open("/etc/mailname", "w") as fp:
            fp.write("{}\n".format(self.config.get("general", "hostname")))

    def post_run(self):
        """Additional tasks."""
        install("spamassassin", self.config, self.upgrade, self.archive_path)
        install("clamav", self.config, self.upgrade, self.archive_path)

    def custom_backup(self, path):
        """Backup custom configuration if any."""
        if package.backend.FORMAT == "deb":
            amavis_custom = f"{self.config_dir}/conf.d/99-custom"
            if os.path.isfile(amavis_custom):
                utils.copy_file(amavis_custom, path)
                utils.success("Amavis custom configuration saved!")
        backup("spamassassin", self.config, os.path.dirname(path))

    def restore(self):
        """Restore custom config files."""
        if package.backend.FORMAT != "deb":
            return
        amavis_custom_configuration = os.path.join(
            self.archive_path, "custom/99-custom")
        if os.path.isfile(amavis_custom_configuration):
            utils.copy_file(amavis_custom_configuration, os.path.join(
                self.config_dir, "conf.d"))
            utils.success("Custom amavis configuration restored.")
