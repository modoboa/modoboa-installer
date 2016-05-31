"""Spamassassin related functions."""

import os

from .. import package
from .. import utils

from . import base
from . import install


class Spamassassin(base.Installer):

    """SpamAssassin installer."""

    appname = "spamassassin"
    no_daemon = True
    packages = {
        "deb": ["spamassassin", "pyzor"],
        "rpm": ["spamassassin", "pyzor"]
    }
    with_db = True
    config_files = ["v310.pre", "local.cf"]

    def get_sql_schema_path(self):
        """Return SQL schema."""
        if self.dbengine == "postgres":
            fname = "bayes_pg.sql"
        else:
            fname = "bayes_mysql.sql"
        schema = "/usr/share/doc/spamassassin/sql/{}".format(fname)
        if not os.path.exists(schema):
            version = package.backend.get_installed_version("spamassassin")
            version = version.replace(".", "_")
            url = (
                "http://svn.apache.org/repos/asf/spamassassin/tags/"
                "spamassassin_release_{}/sql/{}".format(version, fname))
            schema = "/tmp/{}".format(fname)
            utils.exec_cmd("wget {} -O {}".format(url, schema))
        return schema

    def get_template_context(self):
        """Add additional variables to context."""
        context = super(Spamassassin, self).get_template_context()
        if self.dbengine == "postgres":
            store_module = "Mail::SpamAssassin::BayesStore::PgSQL"
            dsn = "DBI:Pg:dbname={};host={}".format(self.dbname, self.dbhost)
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
