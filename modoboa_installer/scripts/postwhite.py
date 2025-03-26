"""postwhite related functions."""

import os
import shutil
import zipfile
import urllib.request

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
        url = f"{repository}/archive/master.zip"
        target = os.path.join(target_dir, "master.zip")

        # Download the archive
        try:
            self.download_file(url, target)
        except Exception as e:
            raise Exception(f"Failed to download {url}: {str(e)}")

        # Extract the archive
        app_name = os.path.basename(repository)
        archive_dir = os.path.join(target_dir, app_name)
        try:
            with zipfile.ZipFile(target, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
        except Exception as e:
            os.unlink(target)  # Clean up partially downloaded file
            raise Exception(f"Failed to extract {target}: {str(e)}")

        # Rename the extracted directory
        extracted_dir = os.path.join(target_dir, f"{app_name}-master")
        try:
            shutil.move(extracted_dir, archive_dir)
        except Exception as e:
            shutil.rmtree(extracted_dir)  # Clean up partially extracted directory
            raise Exception(f"Failed to rename {extracted_dir} to {archive_dir}: {str(e)}")

        # Clean up the archive file
        os.unlink(target)

        return archive_dir

    def post_run(self):
        """Additionnal tasks."""
        install_dir = "/usr/local/bin"
        self.install_from_archive(SPF_TOOLS_REPOSITORY, install_dir)
        self.postw_dir = self.install_from_archive(
            POSTWHITE_REPOSITORY, install_dir)
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

    def download_file(self, url, destination):
        urllib.request.urlretrieve(url, destination)
