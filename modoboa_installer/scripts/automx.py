"""Automx related tasks."""

import os
import pwd
import shutil
import stat

from .. import python
from .. import system
from .. import utils

from . import base


class Automx(base.Installer):
    """Automx installation."""

    appname = "automx"
    config_files = ["automx.conf"]
    no_daemon = True
    packages = {
        "deb": ["memcached", "unzip"],
        "rpm": ["memcached", "unzip"]
    }
    with_user = True

    def __init__(self, *args, **kwargs):
        """Get configuration."""
        super(Automx, self).__init__(*args, **kwargs)
        self.venv_path = self.config.get("automx", "venv_path")
        self.instance_path = self.config.get("automx", "instance_path")

    def get_template_context(self):
        """Additional variables."""
        context = super(Automx, self).get_template_context()
        sql_dsn = "{}://{}:{}@{}:{}/{}".format(
            "postgresql" if self.dbengine == "postgres" else self.dbengine,
            self.config.get("modoboa", "dbuser"),
            self.config.get("modoboa", "dbpassword"),
            self.dbhost,
            self.dbport,
            self.config.get("modoboa", "dbname"))
        if self.db_driver == "pgsql":
            sql_query = (
                "SELECT first_name || ' ' || last_name AS display_name, email"
                ", SPLIT_PART(email, '@', 2) AS domain "
                "FROM core_user WHERE email='%s' AND is_active;")
        else:
            sql_query = (
                "SELECT concat(first_name, ' ', last_name) AS display_name, "
                "email, SUBSTRING_INDEX(email, '@', -1) AS domain "
                "FROM core_user WHERE email='%s' AND is_active=1;"
            )
        context.update({"sql_dsn": sql_dsn, "sql_query": sql_query})
        return context

    def _setup_venv(self):
        """Prepare a python virtualenv."""
        python.setup_virtualenv(
            self.venv_path, sudo_user=self.user, python_version=3)
        packages = [
            "future", "lxml", "ipaddress", "sqlalchemy < 2.0", "python-memcached",
            "python-dateutil", "configparser"
        ]
        if self.dbengine == "postgres":
            packages.append("psycopg2-binary")
        else:
            packages.append("mysqlclient")
        python.install_packages(packages, self.venv_path, sudo_user=self.user)
        target = "{}/master.zip".format(self.home_dir)
        downloaded_file_path = utils.download_remote_file("https://github.com/sys4/automx/archive/master.zip", target)
        self.repo_dir = "{}/automx-master".format(self.home_dir)
        if os.path.exists(self.repo_dir):
            shutil.rmtree(self.repo_dir)
        # Use the absolute path of the downloaded file for the unzip command
        utils.exec_cmd(
            f"unzip {downloaded_file_path}", sudo_user=self.user, cwd=self.home_dir)
        utils.exec_cmd(
            "{} setup.py install".format(
                python.get_path("python", self.venv_path)),
            cwd=self.repo_dir)

    def _deploy_instance(self):
        """Copy files to instance dir."""
        if not os.path.exists(self.instance_path):
            pw = pwd.getpwnam(self.user)
            mode = (
                stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
                stat.S_IROTH | stat.S_IXOTH)
            utils.mkdir(self.instance_path, mode, pw[2], pw[3])
        path = "{}/src/automx_wsgi.py".format(self.repo_dir)
        utils.exec_cmd("cp {} {}".format(path, self.instance_path),
                       sudo_user=self.user, cwd=self.home_dir)

    def post_run(self):
        """Additional tasks."""
        self._setup_venv()
        self._deploy_instance()
        system.enable_and_start_service("memcached")
