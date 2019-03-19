"""Modoboa related tasks."""

import json
import os
import pwd
import shutil
import stat
import sys

from .. import compatibility_matrix
from .. import package
from .. import python
from .. import utils

from . import base


class Modoboa(base.Installer):
    """Modoboa installation."""

    appname = "modoboa"
    no_daemon = True
    packages = {
        "deb": [
            "build-essential", "python-dev", "libxml2-dev", "libxslt-dev",
            "libjpeg-dev", "librrd-dev", "rrdtool", "libffi-dev", "cron"],
        "rpm": [
            "gcc", "gcc-c++", "python-devel", "libxml2-devel", "libxslt-devel",
            "libjpeg-turbo-devel", "rrdtool-devel", "rrdtool", "libffi-devel",
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
        python.setup_virtualenv(self.venv_path, sudo_user=self.user)
        packages = ["rrdtool"]
        version = self.config.get("modoboa", "version")
        if version == "latest":
            modoboa_package = "modoboa"
            packages += self.extensions
        else:
            matrix = compatibility_matrix.COMPATIBILITY_MATRIX[version]
            modoboa_package = "modoboa=={}".format(version)
            for extension in list(self.extensions):
                if not self.is_extension_ok_for_version(extension, version):
                    self.extensions.remove(extension)
                    continue
                if extension in matrix:
                    req_version = matrix[extension]
                    req_version = req_version.replace("<", "\<")
                    req_version = req_version.replace(">", "\>")
                    packages.append("{}{}".format(extension, req_version))
                else:
                    packages.append(extension)
        # Temp fix for https://github.com/modoboa/modoboa-installer/issues/197
        python.install_package(
            modoboa_package, self.venv_path,
            upgrade=self.upgrade, binary=False, sudo_user=self.user)
        if self.dbengine == "postgres":
            packages.append("psycopg2-binary")
        else:
            packages.append("mysqlclient")
        if sys.version_info.major == 2 and sys.version_info.micro < 9:
            # Add extra packages to fix the SNI issue
            packages += ["pyOpenSSL"]
        if "modoboa-radicale" in self.extensions:
            # Temp. fix
            packages += [
                "https://github.com/modoboa/caldav/tarball/master#egg=caldav"]
        python.install_packages(
            packages, self.venv_path, upgrade=self.upgrade, sudo_user=self.user)
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
            "--dburl", "'default:{}://{}:{}@{}/{}'".format(
                self.config.get("database", "engine"),
                self.dbuser, self.dbpasswd, self.dbhost, self.dbname
            )
        ]
        if self.devmode:
            args = ["--devel"] + args
        if self.amavis_enabled:
            args += [
                "'amavis:{}://{}:{}@{}/{}'".format(
                    self.config.get("database", "engine"),
                    self.config.get("amavis", "dbuser"),
                    self.config.get("amavis", "dbpassword"),
                    self.dbhost,
                    self.config.get("amavis", "dbname")
                )
            ]
        code, output = utils.exec_cmd(
            "bash -c '{} modoboa-admin.py deploy instance {}'".format(
                prefix, " ".join(args)),
            sudo_user=self.user, cwd=self.home_dir)
        if code:
            raise utils.FatalError(output)

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

    def get_template_context(self):
        """Additional variables."""
        context = super(Modoboa, self).get_template_context()
        extensions = self.config.get("modoboa", "extensions")
        extensions = extensions.split()
        context.update({
            "sudo_user": (
                "uwsgi" if package.backend.FORMAT == "rpm" else context["user"]
            ),
            "dovecot_mailboxes_owner": (
                self.config.get("dovecot", "mailboxes_owner")),
            "radicale_enabled": (
                "" if "modoboa-radicale" in extensions else "#"),
            "opendkim_user": self.config.get("opendkim", "user"),
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
            utils.mkdir(d, stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])
        settings = {
            "admin": {
                "handle_mailboxes": True,
                "account_auto_removal": True
            },
            "modoboa_amavis": {
                "am_pdp_mode": "inet",
            },
            "modoboa_stats": {
                "rrd_rootdir": rrd_root_dir,
            },
            "modoboa_pdfcredentials": {
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
                settings["modoboa_stats"]["logfile"] = path
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
