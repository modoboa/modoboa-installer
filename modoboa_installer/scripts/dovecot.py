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
        "conf.d/10-master.conf", "conf.d/20-lmtp.conf", "conf.d/10-ssl-keys.try"]
    with_user = True

    def setup_user(self):
        """Setup mailbox user."""
        super().setup_user()
        self.mailboxes_owner = self.app_config["mailboxes_owner"]
        system.create_user(self.mailboxes_owner, self.home_dir)

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
        pw_mailbox = pwd.getpwnam(self.mailboxes_owner)
        dovecot_package = {"deb": "dovecot-core", "rpm": "dovecot"}
        ssl_protocol_parameter = "ssl_protocols"
        if package.backend.get_installed_version(dovecot_package[package.backend.FORMAT]) > "2.3":
            ssl_protocol_parameter = "ssl_min_protocol"
        ssl_protocols = "!SSLv2 !SSLv3"
        if package.backend.get_installed_version("openssl").startswith("1.1") \
                or package.backend.get_installed_version("openssl").startswith("3"):
            ssl_protocols = "!SSLv3"
        if ssl_protocol_parameter == "ssl_min_protocol":
            ssl_protocols = "TLSv1"
        if utils.dist_name() in ["centos", "oracle linux server"]:
            protocols = "protocols = imap lmtp sieve"
            extra_protocols = self.config.get("dovecot", "extra_protocols")
            if extra_protocols:
                protocols += " {}".format(extra_protocols)
        else:
            # Protocols are automatically guessed on debian/ubuntu
            protocols = ""

        context.update({
            "db_driver": self.db_driver,
            "mailboxes_owner_uid": pw_mailbox[2],
            "mailboxes_owner_gid": pw_mailbox[3],
            "mailbox_owner": self.mailboxes_owner,
            "modoboa_user": self.config.get("modoboa", "user"),
            "modoboa_dbname": self.config.get("modoboa", "dbname"),
            "modoboa_dbuser": self.config.get("modoboa", "dbuser"),
            "modoboa_dbpassword": self.config.get("modoboa", "dbpassword"),
            "protocols": protocols,
            "ssl_protocols": ssl_protocols,
            "ssl_protocol_parameter": ssl_protocol_parameter,
            "radicale_user": self.config.get("radicale", "user"),
            "radicale_auth_socket_path": os.path.basename(
                self.config.get("dovecot", "radicale_auth_socket_path")),
            "modoboa_2_2_or_greater": "" if self.modoboa_2_2_or_greater else "#",
            "not_modoboa_2_2_or_greater": "" if not self.modoboa_2_2_or_greater else "#"
        })
        return context

    def post_run(self):
        """Additional tasks."""
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
        # Only root should have read access to the 10-ssl-keys.try
        # See https://github.com/modoboa/modoboa/issues/2570
        utils.exec_cmd("chmod 600 /etc/dovecot/conf.d/10-ssl-keys.try")
        # Add mailboxes user to dovecot group for modoboa mailbox commands.
        # See https://github.com/modoboa/modoboa/issues/2157.
        system.add_user_to_group(self.mailboxes_owner, 'dovecot')

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

    def backup(self, path):
        """Backup emails."""
        home_dir = self.config.get("dovecot", "home_dir")
        utils.printcolor("Backing up mails", utils.MAGENTA)
        if not os.path.exists(home_dir) or os.path.isfile(home_dir):
            utils.error("Error backing up emails, provided path "
                        f" ({home_dir}) seems not right...")
            return

        dst = os.path.join(path, "mails/")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(home_dir, dst)
        utils.success("Mail backup complete!")

    def restore(self):
        """Restore emails."""
        home_dir = self.config.get("dovecot", "home_dir")
        mail_dir = os.path.join(self.archive_path, "mails/")
        if len(os.listdir(mail_dir)) > 0:
            utils.success("Copying mail backup over dovecot directory.")
            if os.path.exists(home_dir):
                shutil.rmtree(home_dir)
            shutil.copytree(mail_dir, home_dir)
            # Resetting permission for vmail
            for dirpath, dirnames, filenames in os.walk(home_dir):
                shutil.chown(dirpath, self.mailboxes_owner, self.mailboxes_owner)
                for filename in filenames:
                    shutil.chown(os.path.join(dirpath, filename),
                                 self.mailboxes_owner, self.mailboxes_owner)
        else:
            utils.printcolor(
                "It seems that emails were not backed up, skipping restoration.",
                utils.MAGENTA
            )
