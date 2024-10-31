"""Dovecot related tools."""

import glob
import os
import pwd
import shutil
import stat
import uuid

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
        "conf.d/10-master.conf", "conf.d/20-lmtp.conf", "conf.d/10-ssl-keys.try",
        "conf.d/dovecot-oauth2.conf.ext"
        ]
    with_user = True

    def setup_user(self):
        """Setup mailbox user."""
        super().setup_user()
        self.mailboxes_owner = self.app_config["mailboxes_owner"]
        system.create_user(self.mailboxes_owner, self.home_dir)

    def get_config_files(self):
        """Additional config files."""
        _config_files = self.config_files

        if self.app_config["move_spam_to_junk"]:
            _config_files += ["conf.d/custom_after_sieve/spam-to-junk.sieve"]

        return _config_files + [
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
        packages += super().get_packages()
        backports_codename = getattr(self, "backports_codename", None)
        if backports_codename:
            packages = [f"{package}/{backports_codename}-backports" for package in packages]
        return packages

    def install_packages(self):
        """Preconfigure Dovecot if needed."""
        name, version = utils.dist_info()
        name = name.lower()
        if name.startswith("debian") and version.startswith("12"):
            package.backend.enable_backports("bookworm")
            self.backports_codename = "bookworm"
        package.backend.preconfigure(
            "dovecot-core", "create-ssl-cert", "boolean", "false")
        super().install_packages()

    def get_template_context(self):
        """Additional variables."""
        context = super().get_template_context()
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
        if "centos" in utils.dist_name():
            protocols = "protocols = imap lmtp sieve"
            extra_protocols = self.config.get("dovecot", "extra_protocols")
            if extra_protocols:
                protocols += " {}".format(extra_protocols)
        else:
            # Protocols are automatically guessed on debian/ubuntu
            protocols = ""

        oauth2_client_id, oauth2_client_secret = utils.create_oauth2_app(
            "Dovecot", "dovecot", self.config)
        hostname = self.config.get("general", "hostname")
        oauth2_introspection_url = (
            f"https://{oauth2_client_id}:{oauth2_client_secret}"
            f"@{hostname}/api/o/introspect/"
        )

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
            "modoboa_2_2_or_greater": "" if self.modoboa_2_2_or_greater else "#",
            "not_modoboa_2_2_or_greater": "" if not self.modoboa_2_2_or_greater else "#",
            "do_move_spam_to_junk": "" if self.app_config["move_spam_to_junk"] else "#",
            "oauth2_introspection_url": oauth2_introspection_url
        })
        return context

    def install_config_files(self):
        """Create sieve dir if needed."""
        if self.app_config["move_spam_to_junk"]:
            utils.mkdir_safe(
                f"{self.config_dir}/conf.d/custom_after_sieve",
                stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP |
                stat.S_IROTH | stat.S_IXOTH,
                0, 0
                )
        super().install_config_files()

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
            if os.path.isfile(f):
                utils.copy_file(f, "{}/conf.d".format(self.config_dir))
        # Make postlogin script executable
        utils.exec_cmd("chmod +x /usr/local/bin/postlogin.sh")
        # Only root should have read access to the 10-ssl-keys.try
        # See https://github.com/modoboa/modoboa/issues/2570
        utils.exec_cmd("chmod 600 /etc/dovecot/conf.d/10-ssl-keys.try")
        # Add mailboxes user to dovecot group for modoboa mailbox commands.
        # See https://github.com/modoboa/modoboa/issues/2157.
        if self.app_config["move_spam_to_junk"]:
            # Compile sieve script
            sieve_file = f"{self.config_dir}/conf.d/custom_after_sieve/spam-to-junk.sieve"
            utils.exec_cmd(f"/usr/bin/sievec {sieve_file}")
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
