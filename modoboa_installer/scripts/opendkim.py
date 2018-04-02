"""OpenDKIM related tools."""

import os
import pwd
import stat

from .. import database
from .. import package
from .. import utils

from . import base


class Opendkim(base.Installer):
    """OpenDKIM installer."""

    appname = "opendkim"
    packages = {
        "deb": ["opendkim"],
        "rpm": ["opendkim"]
    }
    config_files = ["opendkim.conf", "opendkim.hosts"]

    def get_packages(self):
        """Additional packages."""
        packages = super(Opendkim, self).get_packages()
        if package.backend.FORMAT == "deb":
            packages += ["libopendbx1-{}".format(self.db_driver)]
        else:
            dbengine = "postgresql" if self.dbengine == "postgres" else "mysql"
            packages += ["opendbx-{}".format(dbengine)]
        return packages

    def install_config_files(self):
        """Make sure config directory exists."""
        user = self.config.get("opendkim", "user")
        pw = pwd.getpwnam(user)
        targets = [
            [self.app_config["keys_storage_dir"], pw[2], pw[3]]
        ]
        for target in targets:
            if not os.path.exists(target[0]):
                utils.mkdir(
                    target[0],
                    stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
                    stat.S_IROTH | stat.S_IXOTH,
                    target[1], target[2]
                )
        super(Opendkim, self).install_config_files()

    def get_template_context(self):
        """Additional variables."""
        context = super(Opendkim, self).get_template_context()
        context.update({
            "db_driver": self.db_driver,
            "db_name": self.config.get("modoboa", "dbname"),
            "db_user": self.app_config["dbuser"],
            "db_password": self.app_config["dbpassword"],
            "port": self.app_config["port"],
            "user": self.app_config["user"]
        })
        return context

    def setup_database(self):
        """Setup database."""
        self.backend = database.get_backend(self.config)
        self.backend.create_user(
            self.app_config["dbuser"], self.app_config["dbpassword"]
        )
        dbname = self.config.get("modoboa", "dbname")
        dbuser = self.config.get("modoboa", "dbuser")
        dbpassword = self.config.get("modoboa", "dbpassword")
        self.backend.load_sql_file(
            dbname, dbuser, dbpassword,
            self.get_file_path("dkim_view_{}.sql".format(self.dbengine))
        )
        self.backend.grant_right_on_table(
            dbname, "dkim", self.app_config["dbuser"], "SELECT")
