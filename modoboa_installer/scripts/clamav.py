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
        if self.config.getboolean("amavis", "enabled"):
            system.add_user_to_group(
                user, self.config.get("amavis", "user")
            )
        pattern = (
            "s/^AllowSupplementaryGroups false/"
            "AllowSupplementaryGroups true/")
        utils.exec_cmd(
            "perl -pi -e '{}' /etc/clamav/clamd.conf".format(pattern))
        # Stop freshclam daemon to allow manual download
        utils.exec_cmd("service clamav-freshclam stop")
        utils.exec_cmd("freshclam", sudo_user=user, login=False)
        utils.exec_cmd("service clamav-freshclam start")
