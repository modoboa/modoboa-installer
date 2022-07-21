"""Installation scripts management."""

import importlib
import sys

from .. import utils


def install(appname, config, upgrade, backup):
    """Install an application."""
    if (config.has_option(appname, "enabled") and
            not config.getboolean(appname, "enabled")):
        return
    if backup:
        utils.printcolor("Starting up backup...", utils.MAGENTA)
        script = importlib.import_module("modoboa_installer.backup")
        getattr(script, "BACKUP"())(config).run()
        return
    utils.printcolor("Installing {}".format(appname), utils.MAGENTA)
    try:
        script = importlib.import_module(
            "modoboa_installer.scripts.{}".format(appname))
    except ImportError:
        print("Unknown application {}".format(appname))
        sys.exit(1)
    try:
        getattr(script, appname.capitalize())(config, upgrade).run()
    except utils.FatalError as inst:
        utils.printcolor(u"{}".format(inst), utils.RED)
        sys.exit(1)
