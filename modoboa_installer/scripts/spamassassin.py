"""Spamassassin related functions."""

from .. import utils

from . import base
from . import install


class Spamassassin(base.Installer):

    """SpamAssassin installer."""

    appname = "spamassassin"
    no_daemon = True
    packages = ["spamassassin", "pyzor"]
    with_db = True
    config_files = ["v310.pre", "local.cf"]

    def get_sql_schema_path(self):
        """Return SQL schema."""
        if self.dbengine == "postgres":
            schema = "/usr/share/doc/spamassassin/sql/bayes_pg.sql"
        else:
            schema = "/usr/share/doc/spamassassin/sql/bayes_mysql.sql"
        return schema

    def get_template_context(self):
        """Add additional variables to context."""
        context = super(Spamassassin, self).get_template_context()
        if self.dbengine == "postgres":
            store_module = "Mail::SpamAssassin::BayesStore::PgSQL"
            dsn = "DBI:Pg:db_name={};host={}".format(self.dbname, self.dbhost)
        else:
            store_module = "Mail::SpamAssassin::BayesStore::MySQL"
            dsn = "DBI:mysql:{}:{}".format(self.dbname, self.dbhost)
        context.update({
            "store_module": store_module, "dsn": dsn, "dcc_enabled": "#"})
        return context

    def post_run(self):
        """Additional tasks."""
        utils.exec_cmd(
            "pyzor discover", sudo_user=self.config.get("amavis", "user"))
        install("razor", self.config)
