"""Backup script for pre-installed instance."""

import os
import pwd
import shutil
import stat
import sys
import datetime

from .. import database
from .. import utils
from ..constants import DEFAULT_BACKUP_DIRECTORY


class Backup:
    """
    Backup structure ( {optional} ):
    {{backup_directory}}
    ||
    ||--> installer.cfg
    ||--> custom
        |--> { (copy of) /etc/amavis/conf.d/99-custom }
        |--> { (copy of) /etc/postfix/custom_whitelist.cidr }
        |--> { (copy of) dkim directory }
            |--> {dkim.pem}...
        |--> { (copy of) radicale home_dir }
    ||--> databases
        |--> modoboa.sql
        |--> { amavis.sql }
        |--> { spamassassin.sql }
    ||--> mails
        |--> vmails
    """

    def __init__(self, config, silent_backup, backup_path, nomail):
        self.config = config
        self.backup_path = backup_path
        self.nomail = nomail
        self.silent_backup = silent_backup

    def validate_path(self, path):
        """Check basic condition for backup directory."""

        path_exists = os.path.exists(path)

        if path_exists and os.path.isfile(path):
            utils.error("Error, you provided a file instead of a directory!")
            return False

        if not path_exists:
            if not self.silent_backup:
                create_dir = input(
                    f"\"{path}\" doesn't exist, would you like to create it? [Y/n]\n").lower()

            if self.silent_backup or (not self.silent_backup and create_dir.startswith("y")):
                pw = pwd.getpwnam("root")
                utils.mkdir_safe(path, stat.S_IRWXU |
                                 stat.S_IRWXG, pw[2], pw[3])
            else:
                utils.error("Error, backup directory not present.")
                return False

        if len(os.listdir(path)) != 0:
            if not self.silent_backup:
                delete_dir = input(
                    "Warning: backup directory is not empty, it will be purged if you continue... [Y/n]\n").lower()

            if self.silent_backup or (not self.silent_backup and delete_dir.startswith("y")):
                try:
                    os.remove(os.path.join(path, "installer.cfg"))
                except FileNotFoundError:
                    pass

                shutil.rmtree(os.path.join(path, "custom"),
                              ignore_errors=False)
                shutil.rmtree(os.path.join(path, "mails"), ignore_errors=False)
                shutil.rmtree(os.path.join(path, "databases"),
                              ignore_errors=False)
            else:
                utils.error("Error: backup directory not clean.")
                return False

        self.backup_path = path

        pw = pwd.getpwnam("root")
        for dir in ["custom/", "databases/"]:
            utils.mkdir_safe(os.path.join(self.backup_path, dir),
                             stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])
        return True

    def set_path(self):
        """Setup backup directory."""
        if self.silent_backup:
            if self.backup_path is None:
                if self.config.has_option("backup", "default_path"):
                    path = self.config.get("backup", "default_path")
                else:
                    path = DEFAULT_BACKUP_DIRECTORY
                date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M")
                path = os.path.join(path, f"backup_{date}")
                self.validate_path(path)
            else:
                if not self.validate_path(self.backup_path):
                    utils.printcolor(
                        f"Path provided: {self.backup_path}", utils.BLUE)
                    sys.exit(1)
        else:
            user_value = None
            while user_value == "" or user_value is None or not self.validate_path(user_value):
                utils.printcolor(
                    "Enter backup path (it must be an empty directory)", utils.MAGENTA)
                utils.printcolor("CTRL+C to cancel", utils.MAGENTA)
                user_value = utils.user_input("-> ")

    def config_file_backup(self):
        utils.copy_file("installer.cfg", self.backup_path)

    def mail_backup(self):
        if self.nomail:
            utils.printcolor(
                "Skipping mail backup, no-mail argument provided", utils.MAGENTA)
            return

        utils.printcolor("Backing up mails", utils.MAGENTA)

        home_path = self.config.get("dovecot", "home_dir")

        if not os.path.exists(home_path) or os.path.isfile(home_path):
            utils.error("Error backing up Email, provided path "
                        f" ({home_path}) seems not right...")

        else:
            dst = os.path.join(self.backup_path, "mails/")

            if os.path.exists(dst):
                shutil.rmtree(dst)

            shutil.copytree(home_path, dst)
            utils.printcolor("Mail backup complete!", utils.GREEN)

    def custom_config_backup(self):
        """
        Custom config :
        - DKIM keys: {{keys_storage_dir}}
        - Radicale collection (calendars, contacts): {{home_dir}}
        - Amavis : /etc/amavis/conf.d/99-custom
        - Postwhite : /etc/postwhite.conf
        Feel free to suggest to add others!
        """
        utils.printcolor(
            "Backing up some custom configuration...", utils.MAGENTA)

        custom_path = os.path.join(
            self.backup_path, "custom")

        # DKIM Key
        if (self.config.has_option("opendkim", "enabled") and
                self.config.getboolean("opendkim", "enabled")):
            dkim_keys = self.config.get(
                "opendkim", "keys_storage_dir", fallback="/var/lib/dkim")
            if os.path.isdir(dkim_keys):
                shutil.copytree(dkim_keys, os.path.join(custom_path, "dkim"))
                utils.printcolor(
                    "DKIM keys saved!", utils.GREEN)

        # Radicale Collections
        if (self.config.has_option("radicale", "enabled") and
                self.config.getboolean("radicale", "enabled")):
            radicale_backup = os.path.join(self.config.get(
                "radicale", "home_dir", fallback="/srv/radicale"), "collections")
            if os.path.isdir(radicale_backup):
                shutil.copytree(radicale_backup, os.path.join(
                    custom_path, "radicale"))
                utils.printcolor("Radicale files saved", utils.GREEN)

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
            postswhite_custom = "/etc/postwhite.conf"
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

        dump_path = os.path.join(self.backup_path, "databases")
        backend = database.get_backend(self.config)

        if app_name == "modoboa" or (self.config.has_option(app_name, "enabled") and
                                     self.config.getboolean(app_name, "enabled")):
            dbname = self.config.get(app_name, "dbname")
            dbuser = self.config.get(app_name, "dbuser")
            dbpasswd = self.config.get(app_name, "dbpassword")
            backend.dump_database(dbname, dbuser, dbpasswd,
                                  os.path.join(dump_path, f"{app_name}.sql"))

    def backup_completed(self):
        utils.printcolor("Backup process done, your backup is available here:"
                         f"--> {self.backup_path}", utils.GREEN)

    def run(self):
        self.set_path()
        self.config_file_backup()
        self.mail_backup()
        self.custom_config_backup()
        self.database_backup()
        self.backup_completed()
