"""Radicale related tasks."""

import os
import shutil
import stat

from .. import package
from .. import python
from .. import system
from .. import utils

from . import base


class Radicale(base.Installer):
    """Radicale installation."""

    appname = "radicale"
    config_files = ["config"]
    no_daemon = True
    packages = {
        "deb": ["supervisor"],
        "rpm": ["supervisor"]
    }
    with_user = True

    def __init__(self, *args, **kwargs):
        """Get configuration."""
        super().__init__(*args, **kwargs)
        self.venv_path = self.config.get("radicale", "venv_path")

    def _setup_venv(self):
        """Prepare a dedicated virtualenv."""
        python.setup_virtualenv(self.venv_path, sudo_user=self.user)
        packages = [
            "Radicale", "pytz", "radicale-modoboa-auth-oauth2"
        ]
        python.install_packages(packages, self.venv_path, sudo_user=self.user)

    def get_template_context(self):
        """Additional variables."""
        context = super().get_template_context()
        oauth2_client_id, oauth2_client_secret = utils.create_oauth2_app(
            "Radicale",
            "radicale",
            self.config.get("radicale", "oauth2_client_secret"),
            self.config
        )
        hostname = self.config.get("general", "hostname")
        oauth2_introspection_url = (
            f"https://{oauth2_client_id}:{oauth2_client_secret}"
            f"@{hostname}/api/o/introspect/"
        )
        context.update({
            "oauth2_introspection_url": oauth2_introspection_url,
        })
        return context

    def get_config_files(self):
        """Return appropriate path."""
        config_files = super().get_config_files()
        if package.backend.FORMAT == "deb":
            path = "supervisor=/etc/supervisor/conf.d/radicale.conf"
        else:
            path = "supervisor=/etc/supervisord.d/radicale.ini"
        config_files.append(path)
        return config_files

    def install_config_files(self):
        """Make sure config directory exists."""
        if not os.path.exists(self.config_dir):
            utils.mkdir(
                self.config_dir,
                stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
                stat.S_IROTH | stat.S_IXOTH,
                0, 0
            )
        super().install_config_files()

    def restore(self):
        """Restore collections."""
        radicale_backup = os.path.join(
            self.archive_path, "custom/radicale")
        if os.path.isdir(radicale_backup):
            restore_target = os.path.join(self.home_dir, "collections")
            if os.path.isdir(restore_target):
                shutil.rmtree(restore_target)
            shutil.copytree(radicale_backup, restore_target)
            utils.success("Radicale collections restored from backup")

    def post_run(self):
        """Additional tasks."""
        self._setup_venv()
        daemon_name = (
            "supervisor" if package.backend.FORMAT == "deb" else "supervisord"
        )
        system.enable_service(daemon_name)
        utils.exec_cmd("service {} stop".format(daemon_name))
        utils.exec_cmd("service {} start".format(daemon_name))

    def custom_backup(self, path):
        """Backup collections."""
        radicale_backup = os.path.join(self.config.get(
            "radicale", "home_dir", fallback="/srv/radicale"), "collections")
        if os.path.isdir(radicale_backup):
            shutil.copytree(radicale_backup, os.path.join(
                path, "radicale"))
            utils.printcolor("Radicale files saved", utils.GREEN)
