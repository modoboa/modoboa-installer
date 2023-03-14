import os
import sys
from .. import utils


class Restore:
    def __init__(self, restore):
        """
        Restoring pre-check (backup integriety)
        REQUIRED : modoboa.sql
        OPTIONAL : mails/, custom/, amavis.sql, spamassassin.sql
        Only checking required
        """

        if not os.path.isdir(restore):
            utils.error(
                "Provided path is not a directory !")
            sys.exit(1)

        modoba_sql_file = os.path.join(restore, "databases/modoboa.sql")
        if not os.path.isfile(modoba_sql_file):
            utils.error(
                modoba_sql_file + " not found, please check your backup")
            sys.exit(1)

        # Everything seems alright here, proceeding...
