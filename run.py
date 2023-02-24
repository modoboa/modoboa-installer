#!/usr/bin/env python3

"""An installer for Modoboa."""

import argparse
import datetime
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import sys

from modoboa_installer import compatibility_matrix
from modoboa_installer import constants
from modoboa_installer import package
from modoboa_installer import scripts
from modoboa_installer import ssl
from modoboa_installer import system
from modoboa_installer import utils


PRIMARY_APPS = [
    "amavis",
    "fail2ban",
    "modoboa",
    "automx",
    "radicale",
    "uwsgi",
    "nginx",
    "opendkim",
    "postfix",
    "dovecot"
]


def installation_disclaimer(args, config):
    """Display installation disclaimer."""
    hostname = config.get("general", "hostname")
    utils.printcolor(
        "Warning:\n"
        "Before you start the installation, please make sure the following "
        "DNS records exist for domain '{}':\n"
        "  {} IN A   <IP ADDRESS OF YOUR SERVER>\n"
        "       IN MX  {}.\n".format(
            args.domain,
            hostname.replace(".{}".format(args.domain), ""),
            hostname
        ),
        utils.CYAN
    )
    utils.printcolor(
        "Your mail server will be installed with the following components:",
        utils.BLUE)


def upgrade_disclaimer(config):
    """Display upgrade disclaimer."""
    utils.printcolor(
        "Your mail server is about to be upgraded and the following components"
        " will be impacted:", utils.BLUE
    )


def backup_disclaimer():
    """Display backup disclamer. """
    utils.printcolor(
        "Your mail server will be backed up locally.\n"
        " !! You should really transfer the backup somewhere else...\n"
        " !! Custom configuration (like for postfix) won't be saved.", utils.BLUE)


def restore_disclaimer():
    """Display restore disclamer. """
    utils.printcolor(
        "You are about to restore a previous installation of Modoboa.\n"
        "If a new version has been released in between, please update your database!",
        utils.BLUE)


def backup_system(config, args):
    """Launch backup procedure."""
    backup_disclaimer()
    backup_path = None
    if args.silent_backup:
        if not args.backup_path:
            if config.has_option("backup", "default_path"):
                path = config.get("backup", "default_path")
            else:
                path = constants.DEFAULT_BACKUP_DIRECTORY
            date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M")
            path = os.path.join(path, f"backup_{date}")
        else:
            path = args.backup_path
        backup_path = utils.validate_backup_path(path, args.silent_backup)
        if not backup_path:
            utils.printcolor(f"Path provided: {path}", utils.BLUE)
            return
    else:
        user_value = None
        while not user_value or not backup_path:
            utils.printcolor(
                "Enter backup path (it must be an empty directory)",
                utils.MAGENTA
            )
            utils.printcolor("CTRL+C to cancel", utils.MAGENTA)
            user_value = utils.user_input("-> ")
            if not user_value:
                continue
            backup_path = utils.validate_backup_path(user_value, args.silent_backup)

    # Backup configuration file
    utils.copy_file(args.configfile, backup_path)
    # Backup applications
    for app in PRIMARY_APPS:
        scripts.backup(app, config, backup_path)


def main(input_args):
    """Install process."""
    parser = argparse.ArgumentParser()
    versions = (
        ["latest"] + list(compatibility_matrix.COMPATIBILITY_MATRIX.keys())
    )
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Enable debug output")
    parser.add_argument("--force", action="store_true", default=False,
                        help="Force installation")
    parser.add_argument("--configfile", default="installer.cfg",
                        help="Configuration file to use")
    parser.add_argument(
        "--version", default="latest", choices=versions,
        help="Modoboa version to install")
    parser.add_argument(
        "--stop-after-configfile-check", action="store_true", default=False,
        help="Check configuration, generate it if needed and exit")
    parser.add_argument(
        "--interactive", action="store_true", default=False,
        help="Generate configuration file with user interaction")
    parser.add_argument(
        "--upgrade", action="store_true", default=False,
        help="Run the installer in upgrade mode")
    parser.add_argument(
        "--beta", action="store_true", default=False,
        help="Install latest beta release of Modoboa instead of the stable one")
    parser.add_argument(
        "--backup-path", type=str, metavar="path",
        help="To use with --silent-backup, you must provide a valid path")
    parser.add_argument(
        "--backup", action="store_true", default=False,
        help="Backing up interactively previously installed instance"
    )
    parser.add_argument(
        "--silent-backup", action="store_true", default=False,
        help="For script usage, do not require user interaction "
        "backup will be saved at ./modoboa_backup/Backup_M_Y_d_H_M if --backup-path is not provided")
    parser.add_argument(
        "--restore", type=str, metavar="path",
        help="Restore a previously backup up modoboa instance on a NEW machine. "
        "You MUST provide backup directory"
    )
    parser.add_argument("domain", type=str,
                        help="The main domain of your future mail server")
    args = parser.parse_args(input_args)

    if args.debug:
        utils.ENV["debug"] = True

    # Restore prep
    is_restoring = False
    if args.restore is not None:
        is_restoring = True
        args.configfile = os.path.join(args.restore, args.configfile)
        if not os.path.exists(args.configfile):
            utils.error(
                "Installer configuration file not found in backup!"
            )
            sys.exit(1)

    utils.success("Welcome to Modoboa installer!\n")
    is_config_file_available = utils.check_config_file(
        args.configfile, args.interactive, args.upgrade, args.backup, is_restoring)

    if not is_config_file_available and (
            args.upgrade or args.backup or args.silent_backup):
        utils.error("No config file found.")
        return

    if args.stop_after_configfile_check:
        return

    config = configparser.ConfigParser()
    with open(args.configfile) as fp:
        config.read_file(fp)
    if not config.has_section("general"):
        config.add_section("general")
    config.set("general", "domain", args.domain)
    config.set("dovecot", "domain", args.domain)
    config.set("modoboa", "version", args.version)
    config.set("modoboa", "install_beta", str(args.beta))

    if args.backup or args.silent_backup:
        backup_system(config, args)
        return

    # Display disclaimer python 3 linux distribution
    if args.upgrade:
        upgrade_disclaimer(config)
    elif args.restore:
        restore_disclaimer()
        scripts.restore_prep(args.restore)
    else:
        installation_disclaimer(args, config)

    # Show concerned components
    components = []
    for section in config.sections():
        if section in ["general", "database", "mysql", "postgres",
                       "certificate", "letsencrypt"]:
            continue
        if (config.has_option(section, "enabled") and
                not config.getboolean(section, "enabled")):
            continue
        components.append(section)
    utils.printcolor(" ".join(components), utils.YELLOW)
    if not args.force:
        answer = utils.user_input("Do you confirm? (Y/n) ")
        if answer.lower().startswith("n"):
            return
    config.set("general", "force", str(args.force))
    utils.printcolor(
        "The process can be long, feel free to take a coffee "
        "and come back later ;)", utils.BLUE)
    utils.success("Starting...")
    package.backend.prepare_system()
    package.backend.install_many(["sudo", "wget"])
    ssl_backend = ssl.get_backend(config)
    if ssl_backend and not args.upgrade:
        ssl_backend.generate_cert()
    for appname in PRIMARY_APPS:
        scripts.install(appname, config, args.upgrade, args.restore)
    system.restart_service("cron")
    package.backend.restore_system()
    if not args.restore:
        utils.success(
            "Congratulations! You can enjoy Modoboa at https://{} (admin:password)"
            .format(config.get("general", "hostname"))
        )
    else:
        utils.success(
            "Restore complete! You can enjoy Modoboa at https://{} (same credentials as before)"
            .format(config.get("general", "hostname"))
        )


if __name__ == "__main__":
    main(sys.argv[1:])
