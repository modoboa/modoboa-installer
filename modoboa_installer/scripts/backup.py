"""Backup script for pre-installed instance"""

import shutil
import utils
import os
from .. import database

#TODO: have version of each modoboa componenents saved into the config file to restore the same version  

class Backup():

#Backup structure ( {optional} ): 
#{{backup_folder}}
#||
#||--> installer.cfg
#||--> custom
#      |--> { (copy of) /etc/amavis/conf.d/99-custom }
#      |--> { (copy of) /etc/postfix/custom_whitelist.cidr }
#||--> databases
#      |--> modoboa.sql
#      |--> { amavis.sql }
#      |--> { spamassassin.sql }
#||--> mails
#      |--> vmails

    def __init__(self, config):
        self.config = config
        self.destinationPath = ""
        self.BACKUPDIRECTORY = ["mails/", "custom/", "databases/"]


    def preparePath(self):
        for dir in self.BACKUPDIRECTORY:
            os.mkdir(self.destinationPath + dir)


    def validatePath(self, path):
        """Check basic condition for backup directory"""

        if os.path.isfile(path):
            print("Error, you provided a file instead of a directory!")
            return False

        if not os.path.exists(path):
            createDir = input(f"\"{path}\" doesn't exists, would you like to create it ? [Y/n]\n").lower()

            if createDir == "y" or createDir == "yes":
                os.mkdir(path)
            else:
                return False

        if len(os.listdir(path)) != 0:
            delDir = input("Warning : backup folder is not empty, it will be purged if you continue... [Y/n]").lower()
            if delDir == "y" or delDir == "yes":
                shutil.rmtree(path)
            else:
                return False

        self.destinationPath = path

        if self.destinationPath[-1] != "/":
            self.destinationPath += "/"

        self.preparePath()
        return True


    def setPath(self):
        """Setup backup directory"""
        user_value = None
        while (user_value != '' and not self.validatePath(user_value)):
            print("Enter backup path, please provide an empty folder.")
            print("CTRL+C to cancel")
            user_value = utils.user_input("-> ")
    

    def backupConfigFile(self):
        utils.copy_file("installer.cfg", self.destinationPath)


    def backupMails(self):

        utils.printcolor("Backing up mails", utils.MAGENTA)

        home_path = self.config.get("dovecot", "home_dir")

        if not os.path.exists(home_path) or os.path.isfile(home_path):
            utils.printcolor("Error backing up Email, provided path "
            f" ({home_path}) seems not right...", utils.RED)
        
        else:
            shutil.copytree(home_path, self.destinationPath + self.BACKUPDIRECTORY[0])
            utils.printcolor("Mail backup complete!", utils.GREEN)


    def backupCustomConfig(self):
        """Custom config :
        - Amavis : /etc/amavis/conf.d/99-custom
        - Postscreen : /etc/postfix/custom_whitelist.cidr
        Feel free to suggest to add others!"""
        utils.printcolor("Backing up some custom configuration...", utils.MAGENTA)

        custom_path = self.destinationPath + self.BACKUPDIRECTORY[1]

        """AMAVIS"""
        amavis_custom = "/etc/amavis/conf.d/99-custom"
        if os.path.isfile(amavis_custom):
            utils.copy_file(amavis_custom, custom_path)
            utils.printcolor("Amavis custom configuration saved!", utils.GREEN)

        """POSTSCREEN"""
        postscreen_custom = "/etc/postfix/custom_whitelist.cidr"
        if os.path.isfile(postscreen_custom):
            utils.copy_file(postscreen_custom, custom_path)
            utils.printcolor("Postscreen whitelist custom configuration saved!", utils.GREEN)


    def backupDBs(self):
        """Backing up databases"""

        utils.printcolor("Backing up databases...", utils.MAGENTA)

        dump_path = self.destinationPath + self.BACKUPDIRECTORY[2]
        backend = database.get_backend(self.config)

        """Modoboa"""
        dbname = self.config.get("modoboa", "dbname")
        dbuser = self.config.get("modoboa", "dbuser")
        dbpasswd = self.config.get("modoboa", "dbpassword")
        backend.dumpDatabase(dbname, dbuser, dbpasswd, dump_path+"modoboa.sql")

        """Amavis"""
        if (self.config.has_option("amavis", "enabled") and
            not self.config.getboolean("amavis", "enabled")):
            dbname = self.config.get("amavis", "dbname")
            dbuser = self.config.get("amavis", "dbuser")
            dbpasswd = self.config.get("amavis", "dbpassword")
            backend.dumpDatabase(dbname, dbuser, dbpasswd, dump_path+"amavis.sql")

        """SpamAssassin"""
        if (self.config.has_option("spamassassin", "enabled") and
            not self.config.getboolean("spamassassin", "enabled")):
            dbname = self.config.get("spamassassin", "dbname")
            dbuser = self.config.get("spamassassin", "dbuser")
            dbpasswd = self.config.get("spamassassin", "dbpassword")
            backend.dumpDatabase(dbname, dbuser, dbpasswd, dump_path+"spamassassin.sql")

    def backupCompletion(self):
        utils.printcolor("Backup process done, your backup is availible here:"
                        f"--> {self.destinationPath}", utils.GREEN)

    def run(self):
        self.setPath()
        self.backupConfigFile()
        self.backupMails()
        self.backupCustomConfig()
        self.backupDBs()
        self.backupCompletion()

        
