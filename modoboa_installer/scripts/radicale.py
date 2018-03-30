"""Radicale related tasks."""

import os
import stat

from .. import python
from .. import utils

from . import base


class Radicale(base.Installer):
    """Radicale installation."""

    appname = "radicale"
    config_files = [
        "config",
        "supervisor=/etc/supervisor/conf.d/radicale.conf"
    ]
    no_daemon = True
    packages = {
        "deb": ["supervisor"],
        "rpm": ["supervisor"]
    }
    with_user = True

    def __init__(self, config):
        """Get configuration."""
        super(Radicale, self).__init__(config)
        self.venv_path = config.get("radicale", "venv_path")

    def _setup_venv(self):
        """Prepare a dedicated virtualenv."""
        python.setup_virtualenv(
            self.venv_path, sudo_user=self.user, python_version=3)
        packages = ["Radicale", "radicale-dovecot-auth", "pytz"]
        python.install_packages(packages, self.venv_path, sudo_user=self.user)
        python.install_package_from_repository(
            "radicale-storage-by-index",
            "https://github.com/tonioo/RadicaleStorageByIndex",
            venv=self.venv_path, sudo_user=self.user)

    def get_template_context(self):
        """Additional variables."""
        context = super(Radicale, self).get_template_context()
        radicale_auth_socket_path = self.config.get(
            "dovecot", "radicale_auth_socket_path")
        context.update({
            "radicale_auth_socket_path": radicale_auth_socket_path
        })
        return context

    def install_config_files(self):
        """Make sure config directory exists."""
        if not os.path.exists(self.config_dir):
            utils.mkdir(
                self.config_dir,
                stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
                stat.S_IROTH | stat.S_IXOTH,
                0, 0
            )
        super(Radicale, self).install_config_files()

    def post_run(self):
        """Additional tasks."""
        self._setup_venv()
        utils.exec_cmd("service supervisor start")
