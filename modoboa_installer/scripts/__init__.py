"""Installation scripts management."""

import importlib
import sys

from .. import utils


def load_app_script(appname):
    """Load module corresponding to the given appname."""
    try:
        script = importlib.import_module(
            "modoboa_installer.scripts.{}".format(appname))
    except ImportError:
        print("Unknown application {}".format(appname))
        sys.exit(1)
    return script


def install(appname: str, config, upgrade: bool, archive_path: str):
    """Install an application."""
    if (config.has_option(appname, "enabled") and
            not config.getboolean(appname, "enabled")):
        return

    utils.printcolor("Installing {}".format(appname), utils.MAGENTA)
    script = load_app_script(appname)
    try:
        getattr(script, appname.capitalize())(config, upgrade, archive_path).run()
    except utils.FatalError as inst:
        utils.error("{}".format(inst))
        sys.exit(1)


def backup(appname, config, path):
    """Backup an application."""
    if (config.has_option(appname, "enabled") and
            not config.getboolean(appname, "enabled")):
        return

    utils.printcolor("Backing up {}".format(appname), utils.MAGENTA)
    script = load_app_script(appname)
    try:
        getattr(script, appname.capitalize())(config, False, False).backup(path)
    except utils.FatalError as inst:
        utils.error("{}".format(inst))
        sys.exit(1)


def restore_prep(restore):
    """Restore instance"""
    script = importlib.import_module(
        "modoboa_installer.scripts.restore")
    getattr(script, "Restore")(restore)
