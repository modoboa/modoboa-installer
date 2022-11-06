"""OpenDKIM related tools."""

import os
import pwd
import shutil
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
        # Restore dkim keys from backup if restoring
        if self.restore is not None:
            dkim_keys_backup = os.path.join(
                self.restore, "custom/dkim")
            if os.path.isdir(dkim_keys_backup):
                for file in os.listdir(dkim_keys_backup):
                    file_path = os.path.join(dkim_keys_backup, file)
                    if os.path.isfile(file_path):
                        utils.copy_file(file_path, self.config.get(
                            "opendkim", "keys_storage_dir", fallback="/var/lib/dkim"))
                utils.printcolor(
                    "DKIM keys restored from backup", utils.GREEN)
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

    def post_run(self):
        """Additional tasks.
        Check linux distribution (package deb, rpm), to adapt
        to config file location and syntax.
        - update opendkim isocket port config
        - make sure opendkim starts after db service started
        """
        if package.backend.FORMAT == "deb":
            params_file = "/etc/default/opendkim"
        else:
            params_file = "/etc/opendkim.conf"
        pattern = r"s/^(SOCKET=.*)/#\1/"
        utils.exec_cmd(
            "perl -pi -e '{}' {}".format(pattern, params_file))
        with open(params_file, "a") as f:
            f.write('\n'.join([
                "",
                'SOCKET="inet:12345@localhost"',
            ]))

        # Make sure opendkim is started after postgresql and mysql,
        # respectively.
        if (self.dbengine != "postgres" and package.backend.FORMAT == "deb"):
            dbservice = "mysql.service"
        elif (self.dbengine != "postgres" and package.backend.FORMAT != "deb"):
            dbservice = "mysqld.service"
        else:
            dbservice = "postgresql.service"
        pattern = (
            "s/^After=(.*)$/After=$1 {}/".format(dbservice))
        utils.exec_cmd(
            "perl -pi -e '{}' /lib/systemd/system/opendkim.service".format(pattern))

    def custom_backup(self, path):
        """Backup DKIM keys."""
        storage_dir = self.config.get(
            "opendkim", "keys_storage_dir", fallback="/var/lib/dkim")
        if os.path.isdir(storage_dir):
            shutil.copytree(storage_dir, os.path.join(path, "dkim"))
            utils.printcolor(
                "DKIM keys saved!", utils.GREEN)
