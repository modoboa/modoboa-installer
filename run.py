#!/usr/bin/env python

"""An installer for Modoboa."""

import argparse
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from modoboa_installer import scripts
from modoboa_installer import utils


def main():
    """Install process."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Enable debug output")
    parser.add_argument("--force", action="store_true", default=False,
                        help="Force installation")
    parser.add_argument("hostname", type=str,
                        help="The hostname of your future mail server")
    args = parser.parse_args()

    if args.debug:
        utils.ENV["debug"] = True
    utils.printcolor("Welcome to Modoboa installer!", utils.GREEN)
    config = configparser.SafeConfigParser()
    with open("installer.cfg") as fp:
        config.readfp(fp)
    config.set("general", "hostname", args.hostname)
    utils.printcolor(
        "Your mail server {} will be installed with the following components:"
        .format(args.hostname), utils.BLUE)
    components = []
    for section in config.sections():
        if section in ["general", "database", "mysql", "postgres"]:
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
    utils.printcolor(
        "The process can be long, feel free to take a coffee "
        "and come back later ;)", utils.BLUE)
    utils.printcolor("Starting...", utils.GREEN)
    utils.install_system_package("sudo", update=True)
    scripts.install("modoboa", config)
    scripts.install("postfix", config)
    scripts.install("amavis", config)
    scripts.install("dovecot", config)
    utils.printcolor(
        "Congratulations! You can enjoy Modoboa at https://{}"
        .format(args.hostname),
        utils.GREEN)

if __name__ == "__main__":
    main()
