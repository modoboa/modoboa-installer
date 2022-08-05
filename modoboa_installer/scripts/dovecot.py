"""Dovecot related tools."""

import glob
import os
import pwd
import shutil

from .. import database
from .. import package
from .. import system
from .. import utils

from . import base


class Dovecot(base.Installer):

    """Dovecot installer."""

    appname = "dovecot"
    packages = {
        "deb": [
            "dovecot-imapd", "dovecot-lmtpd", "dovecot-managesieved",
            "dovecot-sieve"],
        "rpm": [
            "dovecot", "dovecot-pigeonhole"]
    }
    config_files = [
        "dovecot.conf", "dovecot-dict-sql.conf.ext", "conf.d/10-ssl.conf",
        "conf.d/10-master.conf", "conf.d/20-lmtp.conf"]
    with_user = True

    def get_config_files(self):
        """Additional config files."""
        return self.config_files + [
            "dovecot-sql-{}.conf.ext=dovecot-sql.conf.ext"
            .format(self.dbengine),
            "dovecot-sql-master-{}.conf.ext=dovecot-sql-master.conf.ext"
            .format(self.dbengine),
            "postlogin-{}.sh=/usr/local/bin/postlogin.sh"
            .format(self.dbengine),
        ]

    def get_packages(self):
        """Additional packages."""
        packages = ["dovecot-{}".format(self.db_driver)]
        if package.backend.FORMAT == "deb":
            if "pop3" in self.config.get("dovecot", "extra_protocols"):
                packages += ["dovecot-pop3d"]
        return super(Dovecot, self).get_packages() + packages

    def install_packages(self):
        """Preconfigure Dovecot if needed."""
        package.backend.preconfigure(
            "dovecot-core", "create-ssl-cert", "boolean", "false")
        super(Dovecot, self).install_packages()

    def get_template_context(self):
        """Additional variables."""
        context = super(Dovecot, self).get_template_context()
        pw = pwd.getpwnam(self.user)
        ssl_protocols = "!SSLv2 !SSLv3"
        if package.backend.get_installed_version("openssl").startswith("1.1"):
            ssl_protocols = "!SSLv3"
        if "centos" in utils.dist_name():
            protocols = "protocols = imap lmtp sieve"
            extra_protocols = self.config.get("dovecot", "extra_protocols")
            if extra_protocols:
                protocols += " {}".format(extra_protocols)
        else:
            # Protocols are automatically guessed on debian/ubuntu
            protocols = ""
        context.update({
            "db_driver": self.db_driver,
            "mailboxes_owner_uid": pw[2],
            "mailboxes_owner_gid": pw[3],
            "modoboa_user": self.config.get("modoboa", "user"),
            "modoboa_dbname": self.config.get("modoboa", "dbname"),
            "modoboa_dbuser": self.config.get("modoboa", "dbuser"),
            "modoboa_dbpassword": self.config.get("modoboa", "dbpassword"),
            "protocols": protocols,
            "ssl_protocols": ssl_protocols,
            "radicale_user": self.config.get("radicale", "user"),
            "radicale_auth_socket_path": os.path.basename(
                self.config.get("dovecot", "radicale_auth_socket_path"))
        })
        return context

    def post_run(self):
        """Additional tasks."""
        mail_dir = os.path.join(self.restore, "mails/")
        if self.restore and len(os.listdir(mail_dir)) > 0:
            utils.printcolor("Copying mail backup over dovecot directory", utils.GREEN)
            
            if os.path.exists(self.home_dir):
                shutil.rmtree(self.home_dir)

            shutil.copytree(mail_dir, self.home_dir)
            #Resetting permission for vmail
            for dirpath, dirnames, filenames in os.walk(self.home_dir):
                shutil.chown(dirpath, self.user, self.user)
                for filename in filenames:
                    shutil.chown(os.path.join(dirpath, filename), self.user, self.user)
        elif self.restore:
            utils.printcolor("It seems that mails were not backed up, skipping mail restoration.", utils.MAGENTA)

        if self.dbengine == "postgres":
            dbname = self.config.get("modoboa", "dbname")
            dbuser = self.config.get("modoboa", "dbuser")
            dbpassword = self.config.get("modoboa", "dbpassword")
            backend = database.get_backend(self.config)
            backend.load_sql_file(
                dbname, dbuser, dbpassword,
                self.get_file_path("install_modoboa_postgres_trigger.sql")
            )
            backend.load_sql_file(
                dbname, dbuser, dbpassword,
                self.get_file_path("fix_modoboa_postgres_schema.sql")
            )
        for f in glob.glob("{}/*".format(self.get_file_path("conf.d"))):
            utils.copy_file(f, "{}/conf.d".format(self.config_dir))
        # Make postlogin script executable
        utils.exec_cmd("chmod +x /usr/local/bin/postlogin.sh")

    def restart_daemon(self):
        """Restart daemon process.

        Note: we don't capture output and manually redirect stdout to
        /dev/null since this command may hang depending on the process
        being restarted (dovecot for example)...

        """
        code, output = utils.exec_cmd("service dovecot status")
        action = "start" if code else "restart"
        utils.exec_cmd(
            "service {} {} > /dev/null 2>&1".format(self.appname, action),
            capture_output=False)
        system.enable_service(self.get_daemon_name())
