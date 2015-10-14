"""Base classes."""

import os

from .. import database
from .. import system
from .. import utils


class Installer(object):

    """Simple installer for one application."""

    appname = None
    no_daemon = False
    daemon_name = None
    packages = []
    with_user = False
    with_db = False
    config_files = []

    def __init__(self, config):
        """Get configuration."""
        self.config = config
        self.dbengine = self.config.get("database", "engine")
        # Used to install system packages
        self.db_driver = (
            "pgsql" if self.dbengine == "postgres" else self.dbengine)
        self.dbhost = self.config.get("database", "host")
        if self.config.has_option(self.appname, "config_dir"):
            self.config_dir = self.config.get(self.appname, "config_dir")
        if not self.with_db:
            return
        self.dbname = self.config.get(self.appname, "dbname")
        self.dbuser = self.config.get(self.appname, "dbuser")
        self.dbpasswd = self.config.get(self.appname, "dbpassword")

    def get_sql_schema_path(self):
        """Return a schema to install."""
        return None

    def get_file_path(self, fname):
        """Return the absolute path of this file."""
        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "files", self.appname, fname)
        )

    def setup_database(self):
        """Setup a database."""
        if not self.with_db:
            return
        self.backend = database.get_backend(self.config)
        self.backend.create_user(self.dbuser, self.dbpasswd)
        self.backend.create_database(self.dbname, self.dbuser)
        schema = self.get_sql_schema_path()
        if schema:
            self.backend.load_sql_file(
                self.dbname, self.dbuser, self.dbpasswd, schema)

    def create_user(self):
        """Create a system user."""
        if not self.with_user:
            return
        self.user = self.config.get(self.appname, "user")
        if self.config.has_option(self.appname, "home_dir"):
            self.home_dir = self.config.get(self.appname, "home_dir")
        else:
            self.home_dir = None
        system.create_user(self.user, self.home_dir)

    def get_template_context(self):
        """Return context used for template rendering."""
        context = {
            "dbengine": (
                "Pg" if self.dbengine == "postgres" else self.dbengine),
            "dbhost": self.dbhost,
        }
        for option, value in self.config.items("general"):
            context[option] = value
        for option, value in self.config.items(self.appname):
            context[option] = value
        for section in self.config.sections():
            if section == self.appname:
                continue
            if self.config.has_option(section, "enabled"):
                val = "" if self.config.getboolean(section, "enabled") else "#"
                context["{}_enabled".format(section)] = val
        return context

    def get_packages(self):
        """Return the list of packages to install."""
        return self.packages

    def install_packages(self):
        """Install required packages."""
        packages = self.get_packages()
        if not packages:
            return
        utils.install_system_packages(packages)

    def get_config_files(self):
        """Return the list of configuration files to copy."""
        return self.config_files

    def install_config_files(self):
        """Install configuration files."""
        config_files = self.get_config_files()
        if not config_files:
            return
        context = self.get_template_context()
        for ftpl in config_files:
            src = self.get_file_path("{}.tpl".format(ftpl))
            dst = os.path.join(self.config_dir, ftpl)
            utils.copy_from_template(src, dst, context)

    def restart_daemon(self):
        """Restart daemon process."""
        if self.no_daemon:
            return
        name = self.daemon_name if self.daemon_name else self.appname
        code, output = utils.exec_cmd("service {} status".format(name))
        action = "start" if code else "restart"
        utils.exec_cmd("service {} {}".format(name, action))

    def run(self):
        """Run the installer."""
        self.install_packages()
        self.create_user()
        self.setup_database()
        self.install_config_files()
        self.post_run()
        self.restart_daemon()

    def post_run(self):
        """Additionnal tasks."""
        pass
