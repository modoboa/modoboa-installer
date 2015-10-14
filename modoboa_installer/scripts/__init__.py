"""Installation scripts management."""

import importlib
import sys

from .. import utils


def install(appname, config):
    """Install an application."""
    if (config.has_option(appname, "enabled") and
            not config.getboolean(appname, "enabled")):
        return
    utils.printcolor("Installing {}".format(appname), utils.YELLOW)
    try:
        script = importlib.import_module(
            "modoboa_installer.scripts.{}".format(appname))
    except ImportError:
        print("Unknown application {}".format(appname))
        sys.exit(1)
    getattr(script, appname.capitalize())(config).run()
