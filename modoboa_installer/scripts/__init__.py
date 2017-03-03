"""Installation scripts management."""

import importlib
import sys

from .. import utils


def install(appname, config):
    """Install an application."""
    if (config.has_option(appname, "enabled") and
            not config.getboolean(appname, "enabled")):
        return
    utils.printcolor("Installing {}".format(appname), utils.MAGENTA)
    try:
        script = importlib.import_module(
            "modoboa_installer.scripts.{}".format(appname))
    except ImportError:
        print("Unknown application {}".format(appname))
        sys.exit(1)
    try:
        getattr(script, appname.capitalize())(config).run()
    except utils.FatalError as inst:
        utils.printcolor(utils.RED, "Failure")
        print(inst)
        sys.exit(1)
