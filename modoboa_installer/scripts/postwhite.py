"""postwhite related functions."""

import os
import shutil

from .. import utils

from . import base

POSTWHITE_REPOSITORY = "https://github.com/stevejenkins/postwhite"
SPF_TOOLS_REPOSITORY = "https://github.com/jsarenik/spf-tools"
# These sources run as root, so never follow their default branch
POSTWHITE_COMMIT = "c880eb448959b831ea28c77a61c24c613b91db1d"
SPF_TOOLS_COMMIT = "9b38f7cc516d376b54bb6471c0a25e7eea68510b"


class Postwhite(base.Installer):
    """Postwhite installer."""

    appname = "postwhite"
    config_files = [
        "crontab=/etc/cron.d/postwhite",
    ]
    no_daemon = True
    packages = ["bind9-host", "unzip"]

    def install_from_archive(self, repository, commit, target_dir):
        """Install from an archive."""
        url = "{}/archive/{}.zip".format(repository, commit)
        target = os.path.join(target_dir, os.path.basename(url))
        if os.path.exists(target):
            os.unlink(target)
        utils.exec_cmd("wget {}".format(url), cwd=target_dir)
        app_name = os.path.basename(repository)
        archive_dir = os.path.join(target_dir, app_name)
        if os.path.exists(archive_dir):
            shutil.rmtree(archive_dir)
        utils.exec_cmd("unzip {}.zip".format(commit), cwd=target_dir)
        utils.exec_cmd(
            "mv {name}-{commit} {name}".format(name=app_name, commit=commit),
            cwd=target_dir)
        os.unlink(target)
        return archive_dir

    def post_run(self):
        """Additionnal tasks."""
        install_dir = "/usr/local/bin"
        self.install_from_archive(
            SPF_TOOLS_REPOSITORY, SPF_TOOLS_COMMIT, install_dir)
        self.postw_dir = self.install_from_archive(
            POSTWHITE_REPOSITORY, POSTWHITE_COMMIT, install_dir)
        utils.copy_file(
            os.path.join(self.postw_dir, "postwhite.conf"), self.config_dir)
        self.postw_bin = os.path.join(self.postw_dir, "postwhite")
        utils.exec_cmd("{} /etc/postwhite.conf".format(self.postw_bin))

    def custom_backup(self, path):
        """Backup custom configuration if any."""
        postswhite_custom = "/etc/postwhite.conf"
        if os.path.isfile(postswhite_custom):
            utils.copy_file(postswhite_custom, path)
            utils.printcolor(
                "Postwhite configuration saved!", utils.GREEN)

    def restore(self):
        """Restore config files."""
        postwhite_backup_configuration = os.path.join(
            self.archive_path, "custom/postwhite.conf")
        if os.path.isfile(postwhite_backup_configuration):
            utils.copy_file(postwhite_backup_configuration, self.config_dir)
            utils.success("postwhite.conf restored from backup")
