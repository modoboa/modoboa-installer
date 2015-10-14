"""Amavis related functions."""

import re

from .. import utils

from . import base
from . import install


class Amavis(base.Installer):

    """Amavis installer."""

    appname = "amavis"
    packages = ["libdbi-perl", "amavisd-new"]
    with_db = True
    config_files = ["05-node_id", "15-content_filter_mode", "50-user"]

    def get_packages(self):
        """Additional packages."""
        db_driver = "pg" if self.db_driver == "pgsql" else self.db_driver
        return self.packages + ["libdbd-{}-perl".format(db_driver)]

    @property
    def installed_version(self):
        """Check the installed version."""
        name = "amavisd-new"
        code, output = utils.exec_cmd(
            """dpkg -s {} | grep Version""".format(name),
            capture_output=True
        )
        match = re.match(r"Version: \d:(.+)-\d", output.decode())
        if match:
            return match.group(1)
        return None

    def get_sql_schema_path(self):
        """Return schema path."""
        version = self.installed_version
        if version is None:
            raise utils.FatalError("Amavis is not installed")
        return self.get_file_path(
            "amavis_{}_{}.sql".format(self.dbengine, version))

    def setup_database(self):
        """Additional config."""
        super(Amavis, self).setup_database()
        self.backend.grant_access(
            self.dbname, self.config.get("modoboa", "dbuser"))

    def post_run(self):
        """Additional tasks."""
        with open("/etc/mailname", "w") as fp:
            fp.write("{}\n".format(self.config.get("general", "hostname")))
        install("spamassassin", self.config)
        install("clamav", self.config)
