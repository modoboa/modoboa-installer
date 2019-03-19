#!/usr/bin/env python

"""An installer for Modoboa."""

import argparse
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
    parser.add_argument("domain", type=str,
                        help="The main domain of your future mail server")
    args = parser.parse_args(input_args)

    if args.debug:
        utils.ENV["debug"] = True
    utils.printcolor("Welcome to Modoboa installer!\n", utils.GREEN)
    utils.check_config_file(args.configfile, args.interactive, args.upgrade)
    if args.stop_after_configfile_check:
        return
    config = configparser.SafeConfigParser()
    with open(args.configfile) as fp:
        config.readfp(fp)
    if not config.has_section("general"):
        config.add_section("general")
    config.set("general", "domain", args.domain)
    config.set("dovecot", "domain", args.domain)
    config.set("modoboa", "version", args.version)
    # Display disclaimer
    if not args.upgrade:
        installation_disclaimer(args, config)
    else:
        upgrade_disclaimer(config)
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
    package.backend.install_many(["sudo", "wget"])
    ssl_backend = ssl.get_backend(config)
    if ssl_backend and not args.upgrade:
        ssl_backend.generate_cert()
    scripts.install("amavis", config, args.upgrade)
    scripts.install("modoboa", config, args.upgrade)
    scripts.install("automx", config, args.upgrade)
    scripts.install("radicale", config, args.upgrade)
    scripts.install("uwsgi", config, args.upgrade)
    scripts.install("nginx", config, args.upgrade)
    scripts.install("opendkim", config, args.upgrade)
    scripts.install("postfix", config, args.upgrade)
    scripts.install("dovecot", config, args.upgrade)
    system.restart_service("cron")
    utils.printcolor(
        "Congratulations! You can enjoy Modoboa at https://{} (admin:password)"
        .format(config.get("general", "hostname")),
        utils.GREEN)


if __name__ == "__main__":
    main(sys.argv[1:])
