"""Backup script for pre-installed instance."""

import os
import pwd
import shutil
import stat
import datetime
import sys

from .. import database
from .. import utils


class Backup:
    """
    Backup structure ( {optional} ):
    {{backup_folder}}
    ||
    ||--> installer.cfg
    ||--> custom
        |--> { (copy of) /etc/amavis/conf.d/99-custom }
        |--> { (copy of) /etc/postfix/custom_whitelist.cidr }
    ||--> databases
        |--> modoboa.sql
        |--> { amavis.sql }
        |--> { spamassassin.sql }
    ||--> mails
        |--> vmails
    """

    def __init__(self, config, silent_backup, backup_path, nomail):
        self.config = config
        self.destinationPath = backup_path
        self.nomail = nomail
        self.silent_backup = silent_backup

    def preparePath(self):
        pw = pwd.getpwnam("root")
        for dir in ["custom/", "databases/"]:
            utils.mkdir_safe(os.path.join(self.destinationPath, dir),
                             stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])

    def validatePath(self, path):
        """Check basic condition for backup directory."""

        path_exists = os.path.exists(path)

        if path_exists and os.path.isfile(path):
            utils.printcolor(
                "Error, you provided a file instead of a directory!", utils.RED)
            return False

        if not path_exists:
            if not self.silent_backup:
                createDir = input(
                    f"\"{path}\" doesn't exists, would you like to create it ? [Y/n]\n").lower()

            if self.silent_backup or (not self.silent_backup and (createDir == "y" or createDir == "yes")):
                pw = pwd.getpwnam("root")
                utils.mkdir_safe(path, stat.S_IRWXU |
                                 stat.S_IRWXG, pw[2], pw[3])
            else:
                return False

        if len(os.listdir(path)) != 0:
            if not self.silent_backup:
                delDir = input(
                    "Warning : backup folder is not empty, it will be purged if you continue... [Y/n]\n").lower()
            if self.silent_backup or (not self.silent_backup and (delDir == "y" or delDir == "yes")):
                shutil.rmtree(path)
            else:
                return False

        self.destinationPath = path

        self.preparePath()
        return True

    def set_path(self):
        """Setup backup directory."""
        if self.silent_backup:
            if self.destinationPath is None:
                date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M")
                path = f"./modoboa_backup/backup_{date}/"
                self.validatePath(path)
            else:
                if not self.validatePath(self.destinationPath):
                    utils.printcolor(
                        f"Path provided : {self.destinationPath}", utils.BLUE)
                    sys.exit(1)
        else:
            user_value = None
            while user_value == "" or user_value is None or not self.validatePath(user_value):
                utils.printcolor(
                    "Enter backup path, please provide an empty folder.", utils.MAGENTA)
                utils.printcolor("CTRL+C to cancel", utils.MAGENTA)
                user_value = utils.user_input("-> ")

    def config_file_backup(self):
        utils.copy_file("installer.cfg", self.destinationPath)

    def mail_backup(self):
        if self.nomail:
            utils.printcolor(
                "Skipping mail backup, no-mail argument provided", utils.MAGENTA)
            return

        utils.printcolor("Backing up mails", utils.MAGENTA)

        home_path = self.config.get("dovecot", "home_dir")

        if not os.path.exists(home_path) or os.path.isfile(home_path):
            utils.printcolor("Error backing up Email, provided path "
                             f" ({home_path}) seems not right...", utils.RED)

        else:
            dst = os.path.join(self.destinationPath, "mails/")

            if os.path.exists(dst):
                shutil.rmtree(dst)

            shutil.copytree(home_path, dst)
            utils.printcolor("Mail backup complete!", utils.GREEN)

    def custom_config_backup(self):
        """Custom config :
        - Amavis : /etc/amavis/conf.d/99-custom
        - Postwhite : /etc/postwhite.conf
        Feel free to suggest to add others!"""
        utils.printcolor(
            "Backing up some custom configuration...", utils.MAGENTA)

        custom_path = os.path.join(
            self.destinationPath, "custom")

        # AMAVIS
        if (self.config.has_option("amavis", "enabled") and
                self.config.getboolean("amavis", "enabled")):
            amavis_custom = "/etc/amavis/conf.d/99-custom"
            if os.path.isfile(amavis_custom):
                utils.copy_file(amavis_custom, custom_path)
                utils.printcolor(
                    "Amavis custom configuration saved!", utils.GREEN)

        # POSTWHITE
        if (self.config.has_option("postwhite", "enabled") and
                self.config.getboolean("postwhite", "enabled")):
            postswhite_custom = os.path.join(self.config.get(
                "postwhite", "config_dir", "postwhite.conf"))
            if os.path.isfile(postswhite_custom):
                utils.copy_file(postswhite_custom, custom_path)
                utils.printcolor(
                    "Postwhite configuration saved!", utils.GREEN)

    def database_backup(self):
        """Backing up databases"""

        utils.printcolor("Backing up databases...", utils.MAGENTA)

        self.database_dump("modoboa")
        self.database_dump("amavis")
        self.database_dump("spamassassin")

    def database_dump(self, app_name):

        dump_path = os.path.join(self.destinationPath, "backup")
        backend = database.get_backend(self.config)

        if app_name == "modoboa" or (self.config.has_option(app_name, "enabled") and
                                     self.config.getboolean(app_name, "enabled")):
            dbname = self.config.get(app_name, "dbname")
            dbuser = self.config.get(app_name, "dbuser")
            dbpasswd = self.config.get(app_name, "dbpassword")
            backend.dump_database(dbname, dbuser, dbpasswd,
                                  os.path.join(dump_path, f"{app_name}.sql"))

    def backup_completed(self):
        utils.printcolor("Backup process done, your backup is availible here:"
                         f"--> {self.destinationPath}", utils.GREEN)

    def run(self):
        self.set_path()
        self.config_file_backup()
        self.mail_backup()
        self.custom_config_backup()
        self.database_backup()
        self.backup_completed()
