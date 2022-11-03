"""postwhite related functions."""

import os
import shutil

from .. import utils

from . import base

POSTWHITE_REPOSITORY = "https://github.com/stevejenkins/postwhite"
SPF_TOOLS_REPOSITORY = "https://github.com/jsarenik/spf-tools"


class Postwhite(base.Installer):
    """Postwhite installer."""

    appname = "postwhite"
    config_files = [
        "crontab=/etc/cron.d/postwhite",
    ]
    no_daemon = True
    packages = {
        "deb": ["bind9-host"],
        "rpm": ["bind-utils"]
    }

    def install_from_archive(self, repository, target_dir):
        """Install from an archive."""
        url = "{}/archive/master.zip".format(repository)
        target = os.path.join(target_dir, os.path.basename(url))
        if os.path.exists(target):
            os.unlink(target)
        utils.exec_cmd("wget {}".format(url), cwd=target_dir)
        app_name = os.path.basename(repository)
        archive_dir = os.path.join(target_dir, app_name)
        if os.path.exists(archive_dir):
            shutil.rmtree(archive_dir)
        utils.exec_cmd("unzip master.zip", cwd=target_dir)
        utils.exec_cmd(
            "mv {name}-master {name}".format(name=app_name), cwd=target_dir)
        os.unlink(target)
        return archive_dir

    def post_run(self):
        """Additionnal tasks."""
        install_dir = "/usr/local/bin"
        self.install_from_archive(SPF_TOOLS_REPOSITORY, install_dir)
        postw_dir = self.install_from_archive(
            POSTWHITE_REPOSITORY, install_dir)
        # Attempt to restore config file from backup
        if self.restore is not None:
            postwhite_backup_configuration = os.path.join(
                self.restore, "custom/postwhite.conf")
            if os.path.isfile(postwhite_backup_configuration):
                utils.copy_file(postwhite_backup_configuration, self.config_dir)
                utils.printcolor(
                    "postwhite.conf restored from backup", utils.GREEN)
            else:
                utils.copy_file(os.path.join(postw_dir, "postwhite.conf"), self.config_dir)
        postw_bin = os.path.join(postw_dir, "postwhite")
        utils.exec_cmd("{} /etc/postwhite.conf".format(postw_bin))
