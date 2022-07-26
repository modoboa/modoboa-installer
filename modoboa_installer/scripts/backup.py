"""Backup script for pre-installed instance"""

import os
import pwd
import shutil
import stat
import datetime
import sys

from .. import database
from .. import utils

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

    def __init__(self, config, bashArg, nomail):
        self.config = config
        self.destinationPath = ""
        self.BACKUPDIRECTORY = ["mails/", "custom/", "databases/"]
        self.nomail = nomail
        self.isBash = False
        self.bash = ""
        if bashArg != "NOBASH":
            self.isBash = True
            self.bash = bashArg


    def preparePath(self):
        pw = pwd.getpwnam("root")
        for dir in self.BACKUPDIRECTORY:
            utils.mkdir_safe(self.destinationPath + dir, stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])


    def validatePath(self, path):
        """Check basic condition for backup directory"""

        if path[-1] != "/":
            path += "/"

        try :
            pathExists = os.path.exists(path)
        except:
            print("Provided path is not recognized...")
            return False
        
        if pathExists and os.path.isfile(path):
                print("Error, you provided a file instead of a directory!")
                return False

        if not pathExists:
            if not self.isBash:
                createDir = input(f"\"{path}\" doesn't exists, would you like to create it ? [Y/n]\n").lower()

            if self.isBash or (not self.isBash and (createDir == "y" or createDir == "yes")):
                pw = pwd.getpwnam("root")
                utils.mkdir_safe(path, stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])
            else:
                return False

        if len(os.listdir(path)) != 0:
            if not self.isBash:
                delDir = input("Warning : backup folder is not empty, it will be purged if you continue... [Y/n]\n").lower()
            if self.isBash or (not self.isBash and (delDir == "y" or delDir == "yes")):
                shutil.rmtree(path)
            else:
                return False

        self.destinationPath = path

        self.preparePath()
        return True


    def setPath(self):
        """Setup backup directory"""
        if self.isBash:
            if self.bash == "TRUE":
                date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M")
                path = f"/modoboa_backup/backup_{date}/"
                self.validatePath(path)
            else :
                validate = self.validatePath(self.bash)
                if not validate:
                    print("provided bash is not right, exiting...")
                    print(f"Path provided : {self.bash}")
                    sys.exit(1)
        else:
            user_value = None
            while (user_value == '' or user_value == None or not self.validatePath(user_value)):
                print("Enter backup path, please provide an empty folder.")
                print("CTRL+C to cancel")
                user_value = utils.user_input("-> ")
    

    def backupConfigFile(self):
        utils.copy_file("installer.cfg", self.destinationPath)


    def backupMails(self):

        if self.nomail:
            utils.printcolor("Skipping mail backup, no-mail argument provided", utils.MAGENTA)
            return

        utils.printcolor("Backing up mails", utils.MAGENTA)

        home_path = self.config.get("dovecot", "home_dir")

        if not os.path.exists(home_path) or os.path.isfile(home_path):
            utils.printcolor("Error backing up Email, provided path "
            f" ({home_path}) seems not right...", utils.RED)
        
        else:
            dst = self.destinationPath + self.BACKUPDIRECTORY[0] + "vmail/"

            if os.path.exists(dst):
                shutil.rmtree(dst)
            
            shutil.copytree(home_path, dst)
            utils.printcolor("Mail backup complete!", utils.GREEN)


    def backupCustomConfig(self):
        """Custom config :
        - Amavis : /etc/amavis/conf.d/99-custom
        - Postwhite : /etc/postwhite.conf
        Feel free to suggest to add others!"""
        utils.printcolor("Backing up some custom configuration...", utils.MAGENTA)

        custom_path = self.destinationPath + self.BACKUPDIRECTORY[1]

        """AMAVIS"""
        amavis_custom = "/etc/amavis/conf.d/99-custom"
        if os.path.isfile(amavis_custom):
            utils.copy_file(amavis_custom, custom_path)
            utils.printcolor("Amavis custom configuration saved!", utils.GREEN)

        """POSTWHITE"""
        postswhite_custom = "/etc/postwhite.conf"
        if os.path.isfile(postswhite_custom):
            utils.copy_file(postswhite_custom, custom_path)
            utils.printcolor("Postwhite configuration saved!", utils.GREEN)


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
            self.config.getboolean("amavis", "enabled")):
            dbname = self.config.get("amavis", "dbname")
            dbuser = self.config.get("amavis", "dbuser")
            dbpasswd = self.config.get("amavis", "dbpassword")
            backend.dumpDatabase(dbname, dbuser, dbpasswd, dump_path+"amavis.sql")

        """SpamAssassin"""
        if (self.config.has_option("spamassassin", "enabled") and
            self.config.getboolean("spamassassin", "enabled")):
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

        
