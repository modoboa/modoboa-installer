"""Base classes."""

import os

from .. import database
from .. import package
from .. import system
from .. import utils


class Installer(object):
    """Simple installer for one application."""

    appname = None
    no_daemon = False
    daemon_name = None
    packages = {}
    with_user = False
    with_db = False
    config_files = []

    def __init__(self, config, upgrade):
        """Get configuration."""
        self.config = config
        self.upgrade = upgrade
        if self.config.has_section(self.appname):
            self.app_config = dict(self.config.items(self.appname))
        self.dbengine = self.config.get("database", "engine")
        # Used to install system packages
        self.db_driver = (
            "pgsql" if self.dbengine == "postgres" else self.dbengine)
        self.dbhost = self.config.get("database", "host")
        self._config_dir = None
        if not self.with_db:
            return
        self.dbname = self.config.get(self.appname, "dbname")
        self.dbuser = self.config.get(self.appname, "dbuser")
        self.dbpasswd = self.config.get(self.appname, "dbpassword")

    @property
    def config_dir(self):
        """Return main configuration directory."""
        if self._config_dir is None and self.config.has_option(
                self.appname, "config_dir"):
            self._config_dir = self.config.get(self.appname, "config_dir")
        return self._config_dir

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

    def setup_user(self):
        """Setup a system user."""
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
        return self.packages.get(package.backend.FORMAT, {})

    def install_packages(self):
        """Install required packages."""
        packages = self.get_packages()
        if not packages:
            return
        package.backend.install_many(packages)

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
            if "=" in ftpl:
                ftpl, dstname = ftpl.split("=")
            else:
                dstname = ftpl
            src = self.get_file_path("{}.tpl".format(ftpl))
            dst = dstname
            if not dst.startswith("/"):
                dst = os.path.join(self.config_dir, dst)
            utils.copy_from_template(src, dst, context)

    def get_daemon_name(self):
        """Return daemon name if defined."""
        return self.daemon_name if self.daemon_name else self.appname

    def restart_daemon(self):
        """Restart daemon process."""
        if self.no_daemon:
            return
        name = self.get_daemon_name()
        system.enable_and_start_service(name)

    def run(self):
        """Run the installer."""
        self.install_packages()
        self.setup_user()
        if not self.upgrade:
            self.setup_database()
        self.install_config_files()
        self.post_run()
        self.restart_daemon()

    def post_run(self):
        """Additionnal tasks."""
        pass
