"""Razor related functions."""

import os
import pwd
import shutil
import stat

from .. import utils

from . import base


class Razor(base.Installer):

    """Razor installer."""

    appname = "razor"
    no_daemon = True
    packages = ["razor"]

    def post_run(self):
        """Additional tasks."""
        user = self.config.get("amavis", "user")
        pw = pwd.getpwnam(user)
        utils.mkdir(
            "/var/log/razor",
            stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
            stat.S_IROTH | stat.S_IXOTH,
            pw[2], pw[3]
        )
        path = os.path.join(self.config.get("amavis", "home_dir"), ".razor")
        utils.mkdir(path, stat.S_IRWXU, pw[2], pw[3])
        utils.exec_cmd("razor-admin -home {} -create".format(path))
        shutil.copy(os.path.join(path, "razor-agent.conf"), self.config_dir)
        utils.exec_cmd("razor-admin -home {} -discover".format(path),
                       sudo_user=user)
        utils.exec_cmd("razor-admin -home {} -register".format(path),
                       sudo_user=user)
        # FIXME: move log file to /var/log ?
