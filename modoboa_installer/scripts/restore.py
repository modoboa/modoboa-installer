import os
import sys
from .. import utils

class Restore:
    def __init__(self, restore):
        """Restoring pre-check (backup integriety)"""
        """REQUIRED : modoboa.sql"""
        """OPTIONAL : mails/, custom/, amavis.sql, spamassassin.sql"""
        """Only checking required"""

        try:
            if not os.path.isdir(restore):
                utils.printcolor("Provided path is not a directory !", utils.RED)
                sys.exit(1)
        except:
            utils.printcolor("Provided path is not right...", utils.RED)
            sys.exit(1)

        try:
            modobasql_file = os.path.join(restore, "databases/modoboa.sql")
            if not os.path.isfile(modobasql_file):
                utils.printcolor(modobasql_file +" not found, please check your backup", utils.RED)
                sys.exit(1)
        except:
            utils.printcolor(modobasql_file + " not found, please check your backup", utils.RED)
            sys.exit(1)

        #Everything seems allright here, proceding...