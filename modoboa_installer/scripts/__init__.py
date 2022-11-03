"""Installation scripts management."""

import importlib
import sys

from .. import utils


def install(appname, config, upgrade, restore):
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
        getattr(script, appname.capitalize())(config, upgrade, restore).run()
    except utils.FatalError as inst:
        utils.printcolor(u"{}".format(inst), utils.RED)
        sys.exit(1)


def backup(config, silent_backup, backup_path, nomail):
    """Backup instance"""
    script = importlib.import_module(
        "modoboa_installer.scripts.backup")
    try:
        getattr(script, "Backup")(
            config, silent_backup, backup_path, nomail).run()
    except utils.FatalError as inst:
        utils.printcolor(u"{}".format(inst), utils.RED)
        sys.exit(1)


def restore_prep(restore):
    """Restore instance"""
    script = importlib.import_module(
        "modoboa_installer.scripts.restore")
    getattr(script, "Restore")(restore)
