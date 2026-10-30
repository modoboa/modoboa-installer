"""Amavis related functions."""

import os

from .. import package
from .. import utils

from . import base
from . import backup, install


class Amavis(base.Installer):

    """Amavis installer."""

    appname = "amavis"
    config_files = [
        "conf.d/05-node_id", "conf.d/15-content_filter_mode", "conf.d/50-user",
    ]
    packages = [
        "libdbi-perl", "amavisd-new", "arc", "arj", "cabextract", "lz4",
        "lrzip", "lzop", "p7zip-full", "rpm2cpio", "unrar-free",
    ]
    with_db = True

    @property
    def config_dir(self):
        """Return appropriate config dir."""
        return "/etc/amavis"

    def get_packages(self):
        """Additional packages."""
        db_driver = "pg" if self.db_driver == "pgsql" else self.db_driver
        return super().get_packages() + [f"libdbd-{db_driver}-perl"]

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
        self.protect_file(
            os.path.join(self.config_dir, "conf.d/50-user"),
            self.app_config["user"])
        install("spamassassin", self.config, self.upgrade, self.archive_path)
        install("clamav", self.config, self.upgrade, self.archive_path)

    def custom_backup(self, path):
        """Backup custom configuration if any."""
        amavis_custom = f"{self.config_dir}/conf.d/99-custom"
        if os.path.isfile(amavis_custom):
            utils.copy_file(amavis_custom, path)
            utils.success("Amavis custom configuration saved!")
        backup("spamassassin", self.config, os.path.dirname(path))

    def restore(self):
        """Restore custom config files."""
        amavis_custom_configuration = os.path.join(
            self.archive_path, "custom/99-custom")
        if os.path.isfile(amavis_custom_configuration):
            utils.copy_file(amavis_custom_configuration, os.path.join(
                self.config_dir, "conf.d"))
            utils.success("Custom amavis configuration restored.")
