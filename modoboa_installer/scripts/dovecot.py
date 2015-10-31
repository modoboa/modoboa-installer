"""Dovecot related tools."""

import glob
import pwd
import shutil

from .. import database
from .. import utils

from . import base


class Dovecot(base.Installer):

    """Dovecot installer."""

    appname = "dovecot"
    packages = [
        "dovecot-imapd", "dovecot-lmtpd", "dovecot-managesieved",
        "dovecot-sieve"
    ]
    config_files = [
        "dovecot.conf", "dovecot-dict-sql.conf.ext", "conf.d/10-ssl.conf"]
    with_user = True

    def get_config_files(self):
        """Additional config files."""
        return self.config_files + [
            "dovecot-sql-{}.conf.ext=dovecot-sql.conf.ext"
            .format(self.dbengine)
        ]

    def get_packages(self):
        """Additional packages."""
        return self.packages + ["dovecot-{}".format(self.db_driver)]

    def get_template_context(self):
        """Additional variables."""
        context = super(Dovecot, self).get_template_context()
        pw = pwd.getpwnam(self.user)
        context.update({
            "db_driver": self.db_driver,
            "mailboxes_owner_uid": pw[2],
            "mailboxes_owner_gid": pw[3],
            "modoboa_dbname": self.config.get("modoboa", "dbname"),
            "modoboa_dbuser": self.config.get("modoboa", "dbuser"),
            "modoboa_dbpassword": self.config.get("modoboa", "dbpassword"),
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
            shutil.copy(f, "{}/conf.d".format(self.config_dir))

    def restart_daemon(self):
        """Restart daemon process.

        Note: we don't capture output and manually redirect stdout to
        /dev/null since this command may hang depending on the process
        being restarted (dovecot for example)...

        """
        code, output = utils.exec_cmd("service dovecot status")
        action = "start" if code else "restart"
        utils.exec_cmd(
            "service dovecot {} > /dev/null 2>&1".format(action),
            capture_output=False)
