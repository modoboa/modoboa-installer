"""Modoboa related tasks."""

import json
import os
import pwd
import random
import shutil
import stat
import sys

from .. import compatibility_matrix
from .. import package
from .. import python
from .. import system
from .. import utils

from . import base


class Modoboa(base.Installer):
    """Modoboa installation."""

    appname = "modoboa"
    no_daemon = True
    packages = {
        "deb": [
            "build-essential", "python3-dev", "libxml2-dev", "libxslt-dev",
            "libjpeg-dev", "librrd-dev", "rrdtool", "libffi-dev", "cron",
            "libssl-dev", "redis-server", "supervisor", "pkg-config",
            "libcairo2-dev"
        ],
        "rpm": [
            "gcc", "gcc-c++", "python3-devel", "libxml2-devel", "libxslt-devel",
            "libjpeg-turbo-devel", "rrdtool-devel", "rrdtool", "libffi-devel",
            "supervisor", "redis"
        ]
    }
    config_files = [
        "crontab=/etc/cron.d/modoboa",
        "sudoers=/etc/sudoers.d/modoboa",
    ]
    with_db = True
    with_user = True

    def __init__(self, *args, **kwargs):
        """Get configuration."""
        super(Modoboa, self).__init__(*args, **kwargs)
        self.venv_path = self.config.get("modoboa", "venv_path")
        self.instance_path = self.config.get("modoboa", "instance_path")
        self.extensions = self.config.get("modoboa", "extensions").split()
        self.devmode = self.config.getboolean("modoboa", "devmode")
        # Sanity check for amavis
        self.amavis_enabled = False
        if "modoboa-amavis" in self.extensions:
            if self.config.getboolean("amavis", "enabled"):
                self.amavis_enabled = True
            else:
                self.extensions.remove("modoboa-amavis")
        if "modoboa-radicale" in self.extensions:
            if not self.config.getboolean("radicale", "enabled"):
                self.extensions.remove("modoboa-radicale")
        self.dovecot_enabled = self.config.getboolean("dovecot", "enabled")
        self.opendkim_enabled = self.config.getboolean("opendkim", "enabled")

    def is_extension_ok_for_version(self, extension, version):
        """Check if extension can be installed with this modo version."""
        if extension not in compatibility_matrix.EXTENSIONS_AVAILABILITY:
            return True
        version = utils.convert_version_to_int(version)
        min_version = compatibility_matrix.EXTENSIONS_AVAILABILITY[extension]
        min_version = utils.convert_version_to_int(min_version)
        return version >= min_version

    def _setup_venv(self):
        """Prepare a dedicated virtualenv."""
        python.setup_virtualenv(
            self.venv_path, sudo_user=self.user, python_version=3)
        packages = ["rrdtool"]
        version = self.config.get("modoboa", "version")
        if version == "latest":
            packages += ["modoboa"] + self.extensions
        else:
            matrix = compatibility_matrix.COMPATIBILITY_MATRIX[version]
            packages.append("modoboa=={}".format(version))
            for extension in list(self.extensions):
                if not self.is_extension_ok_for_version(extension, version):
                    self.extensions.remove(extension)
                    continue
                if extension in matrix:
                    req_version = matrix[extension]
                    if req_version is None:
                        continue
                    req_version = req_version.replace("<", "\<")
                    req_version = req_version.replace(">", "\>")
                    packages.append("{}{}".format(extension, req_version))
                else:
                    packages.append(extension)
        # Temp fix for django-braces
        python.install_package(
            "django-braces", self.venv_path, upgrade=self.upgrade,
            sudo_user=self.user
        )
        if self.dbengine == "postgres":
            packages.append("psycopg2-binary\<2.9")
        else:
            packages.append("mysqlclient")
        if sys.version_info.major == 2 and sys.version_info.micro < 9:
            # Add extra packages to fix the SNI issue
            packages += ["pyOpenSSL"]
        python.install_packages(
            packages, self.venv_path,
            upgrade=self.upgrade,
            sudo_user=self.user,
            beta=self.config.getboolean("modoboa", "install_beta")
        )
        if self.devmode:
            # FIXME: use dev-requirements instead
            python.install_packages(
                ["django-bower", "django-debug-toolbar"], self.venv_path,
                upgrade=self.upgrade, sudo_user=self.user)

    def _deploy_instance(self):
        """Deploy Modoboa."""
        target = os.path.join(self.home_dir, "instance")
        if os.path.exists(target):
            condition = (
                not self.upgrade and
                not self.config.getboolean("general", "force")
            )
            if condition:
                utils.printcolor(
                    "Target directory for Modoboa deployment ({}) already "
                    "exists. If you choose to continue, it will be removed."
                    .format(target),
                    utils.YELLOW
                )
                answer = utils.user_input("Do you confirm? (Y/n) ")
                if answer.lower().startswith("n"):
                    return
            shutil.rmtree(target)

        prefix = ". {}; ".format(
            os.path.join(self.venv_path, "bin", "activate"))
        args = [
            "--collectstatic",
            "--timezone", self.config.get("modoboa", "timezone"),
            "--domain", self.config.get("general", "hostname"),
            "--extensions", " ".join(self.extensions),
            "--dont-install-extensions",
            "--dburl", "'default:{}://{}:{}@{}:{}/{}'".format(
                self.config.get("database", "engine"),
                self.dbuser, self.dbpasswd, self.dbhost, self.dbport,
                self.dbname
            )
        ]
        if self.devmode:
            args = ["--devel"] + args
        if self.amavis_enabled:
            args += [
                "'amavis:{}://{}:{}@{}:{}/{}'".format(
                    self.config.get("database", "engine"),
                    self.config.get("amavis", "dbuser"),
                    self.config.get("amavis", "dbpassword"),
                    self.dbhost,
                    self.dbport,
                    self.config.get("amavis", "dbname")
                )
            ]
        if self.upgrade and self.opendkim_enabled and self.dbengine == "postgres":
            # Drop dkim view to prevent an error during migration (2.0)
            self.backend._exec_query("DROP VIEW IF EXISTS dkim")
        code, output = utils.exec_cmd(
            "bash -c '{} modoboa-admin.py deploy instance {}'".format(
                prefix, " ".join(args)),
            sudo_user=self.user, cwd=self.home_dir)
        if code:
            raise utils.FatalError(output)
        if self.upgrade and self.opendkim_enabled and self.dbengine == "postgres":
            # Restore view previously deleted
            self.backend.load_sql_file(
                self.dbname, self.dbuser, self.dbpasswd,
                self.get_file_path("dkim_view_{}.sql".format(self.dbengine))
            )
            self.backend.grant_right_on_table(
                self.dbname, "dkim", self.config.get("opendkim", "dbuser"),
                "SELECT"
            )

    def setup_database(self):
        """Additional config."""
        super(Modoboa, self).setup_database()
        if not self.amavis_enabled:
            return
        self.backend.grant_access(
            self.config.get("amavis", "dbname"), self.dbuser)

    def get_packages(self):
        """Include extra packages if needed."""
        packages = super(Modoboa, self).get_packages()
        condition = (
            package.backend.FORMAT == "rpm" and
            sys.version_info.major == 2 and
            sys.version_info.micro < 9)
        if condition:
            # Add extra packages to fix the SNI issue
            packages += ["openssl-devel"]
        return packages

    def get_config_files(self):
        """Return appropriate path."""
        config_files = super().get_config_files()
        if package.backend.FORMAT == "deb":
            path = "supervisor=/etc/supervisor/conf.d/policyd.conf"
        else:
            path = "supervisor=/etc/supervisord.d/policyd.ini"
        config_files.append(path)
        return config_files

    def get_template_context(self):
        """Additional variables."""
        context = super(Modoboa, self).get_template_context()
        extensions = self.config.get("modoboa", "extensions")
        extensions = extensions.split()
        random_hour = random.randint(0, 6)
        context.update({
            "sudo_user": (
                "uwsgi" if package.backend.FORMAT == "rpm" else context["user"]
            ),
            "dovecot_mailboxes_owner": (
                self.config.get("dovecot", "mailboxes_owner")),
            "radicale_enabled": (
                "" if "modoboa-radicale" in extensions else "#"),
            "opendkim_user": self.config.get("opendkim", "user"),
            "minutes": random.randint(1, 59),
            "hours" : f"{random_hour},{random_hour+12}"
        })
        return context

    def apply_settings(self):
        """Configure modoboa."""
        rrd_root_dir = os.path.join(self.home_dir, "rrdfiles")
        pdf_storage_dir = os.path.join(self.home_dir, "pdfcredentials")
        webmail_media_dir = os.path.join(
            self.instance_path, "media", "webmail")
        pw = pwd.getpwnam(self.user)
        for d in [rrd_root_dir, pdf_storage_dir, webmail_media_dir]:
            utils.mkdir_safe(d, stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])
        settings = {
            "admin": {
                "handle_mailboxes": True,
                "account_auto_removal": True
            },
            "modoboa_amavis": {
                "am_pdp_mode": "inet",
            },
            "maillog": {
                "rrd_rootdir": rrd_root_dir,
            },
            "pdfcredentials": {
                "storage_dir": pdf_storage_dir
            },
            "modoboa_radicale": {
                "server_location": "https://{}/radicale/".format(
                    self.config.get("general", "hostname")),
                "rights_file_path": "{}/rights".format(
                    self.config.get("radicale", "config_dir"))
            }
        }
        for path in ["/var/log/maillog", "/var/log/mail.log"]:
            if os.path.exists(path):
                settings["maillog"]["logfile"] = path
        if self.config.getboolean("opendkim", "enabled"):
            settings["admin"]["dkim_keys_storage_dir"] = (
                self.config.get("opendkim", "keys_storage_dir"))
        settings = json.dumps(settings)
        query = (
            "UPDATE core_localconfig SET _parameters='{}'"
            .format(settings)
        )
        self.backend._exec_query(
            query, self.dbname, self.dbuser, self.dbpasswd)

    def post_run(self):
        """Additional tasks."""
        self._setup_venv()
        self._deploy_instance()
        if not self.upgrade:
            self.apply_settings()

        if 'centos' in utils.dist_name():
            supervisor = "supervisord"
            system.enable_and_start_service("redis")
        else:
            supervisor = "supervisor"
            system.enable_and_start_service("redis-server")
        # Restart supervisor
        system.enable_service(supervisor)
        utils.exec_cmd("service {} stop".format(supervisor))
        utils.exec_cmd("service {} start".format(supervisor))
