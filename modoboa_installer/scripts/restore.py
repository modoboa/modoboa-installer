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
            utils.printcolor(
                "Provided path is not a directory !", utils.RED)
            sys.exit(1)

        modoba_sql_file = os.path.join(restore, "databases/modoboa.sql")
        if not os.path.isfile(modoba_sql_file):
            utils.printcolor(
                modoba_sql_file + " not found, please check your backup", utils.RED)
            sys.exit(1)

        # Everything seems alright here, proceeding...
