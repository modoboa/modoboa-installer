"""ClamAV related tools."""

from .. import utils
from .. import system

from . import base


class Clamav(base.Installer):

    """ClamAV installer."""

    appname = "clamav"
    daemon_name = "clamav-daemon"
    packages = ["clamav-daemon"]

    def post_run(self):
        """Additional tasks."""
        user = self.config.get(self.appname, "user")
        system.add_user_to_group(
            user, self.config.get("amavis", "user")
        )
        if utils.dist_name == "ubuntu":
            # Stop freshclam daemon to allow manual download
            utils.exec_cmd("service clamav-freshclam stop")
            utils.exec_cmd("freshclam", sudo_user=user)
            utils.exec_cmd("service clamav-freshclam start")
        else:
            utils.exec_cmd("freshclam", sudo_user=user)
