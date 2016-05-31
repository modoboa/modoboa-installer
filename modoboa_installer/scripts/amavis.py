"""Amavis related functions."""

from .. import package
from .. import utils

from . import base
from . import install


class Amavis(base.Installer):

    """Amavis installer."""

    appname = "amavis"
    packages = {
        "deb": ["libdbi-perl", "amavisd-new"],
        "rpm": ["amavisd-new"],
    }
    with_db = True

    @property
    def config_dir(self):
        """Return appropriate config dir."""
        if package.backend.FORMAT == "rpm":
            return "/etc/amavisd"
        return "/etc/amavis"

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
