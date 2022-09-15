#!/usr/bin/env python3

"""An installer for Modoboa."""

import argparse
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import sys

from modoboa_installer import compatibility_matrix
from modoboa_installer import package
from modoboa_installer import scripts
from modoboa_installer import ssl
from modoboa_installer import system
from modoboa_installer import utils


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


def backup_disclamer():
    """Display backup disclamer. """
    utils.printcolor(
        "Your mail server will be backed up (messages and databases) locally."
        " !! You should really transfer the backup somewhere else..."
        " Custom configuration (like to postfix) won't be saved.", utils.BLUE)


def restore_disclamer():
    """Display restore disclamer. """
    utils.printcolor(
        "You are about to restore a previous installation of Modoboa."
        "If a new version has been released in between, please update your database !",
        utils.BLUE)


def main(input_args):
    """Install process."""
    parser = argparse.ArgumentParser()
    versions = (
        ["latest"] + list(compatibility_matrix.COMPATIBILITY_MATRIX.keys())
    )
    parser.add_argument("--backup", action="store_true", default=False,
                        help="Backing up previously installed instance")
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
        "--bash", type=str, metavar="path",
        help="(backup only) - For script usage, No interaction will be required, you must provide a path")
    parser.add_argument(
        "--sbash", action="store_true", default=False,
        help="same as --bash but backup will be at /modoboa_backup/Backup_M_Y_d_H_M")
    parser.add_argument(
        "--no-mail", action="store_true", default=False,
        help="Disable mail backup (save space)")
    parser.add_argument(
        "--restore", type=str, metavar="path",
        help="Restore a previously backup up modoboa instance on a NEW machine. You Must provide backup directory"
    )
    parser.add_argument("domain", type=str,
                        help="The main domain of your future mail server")
    args = parser.parse_args(input_args)

    if args.debug:
        utils.ENV["debug"] = True

    if not args.backup and (args.bash != None or args.sbash or args.no_mail):
        utils.printcolor("You provided --bash or --sbash without --backup, "
                         "if you want to do a backup, please provide --backup!", utils.RED)
        return
    elif args.bash != None and args.sbash:
        utils.printcolor("You provided --bash PATH and --sbash at the same time. "
                         "Please provided only one!", utils.RED)
        return
    elif args.bash == "TRUE":
        utils.printcolor(
            "You can't pick *TRUE* as backup directory !", utils.RED)

    # Restore prep
    isRestoring = False
    if args.restore != None:
        isRestoring = True
        args.configfile = os.path.join(args.restore, "installer.cfg")
        if not os.path.exists(args.configfile):
            utils.printcolor("installer.cfg from backup not found!", utils.RED)
            sys.exit(1)

    utils.printcolor("Welcome to Modoboa installer!\n", utils.GREEN)
    wasConfigFileAlreadyThere = utils.check_config_file(
        args.configfile, args.interactive, args.upgrade, args.backup, isRestoring)

    if args.stop_after_configfile_check or (not wasConfigFileAlreadyThere and args.backup):
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
    # Display disclaimer python 3 linux distribution
    if args.upgrade:
        upgrade_disclaimer(config)
    elif args.backup:
        backup_disclamer()
        bashArg = "NOBASH"
        if args.bash != None:
            bashArg = args.bash
        elif args.sbash:
            bashArg = "TRUE"
        scripts.backup(config, bashArg, args.no_mail)
        return
    elif args.restore:
        restore_disclamer()
        scripts.restore(args.restore)
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
    utils.printcolor("Starting...", utils.GREEN)
    package.backend.prepare_system()
    package.backend.install_many(["sudo", "wget"])
    ssl_backend = ssl.get_backend(config)
    if ssl_backend and not args.upgrade:
        ssl_backend.generate_cert()
    scripts.install("amavis", config, args.upgrade, args.restore)
    scripts.install("modoboa", config, args.upgrade, args.restore)
    scripts.install("automx", config, args.upgrade, args.restore)
    scripts.install("radicale", config, args.upgrade, args.restore)
    scripts.install("uwsgi", config, args.upgrade, args.restore)
    scripts.install("nginx", config, args.upgrade, args.restore)
    scripts.install("opendkim", config, args.upgrade, args.restore)
    scripts.install("postfix", config, args.upgrade, args.restore)
    scripts.install("dovecot", config, args.upgrade, args.restore)
    system.restart_service("cron")
    package.backend.restore_system()
    if not args.restore:
        utils.printcolor(
            "Congratulations! You can enjoy Modoboa at https://{} (admin:password)"
            .format(config.get("general", "hostname")),
            utils.GREEN)
    else:
        utils.printcolor(
            "Resotre complete! You can enjoy Modoboa at https://{} (same credentials as before)"
            .format(config.get("general", "hostname")),
            utils.GREEN)


if __name__ == "__main__":
    main(sys.argv[1:])
