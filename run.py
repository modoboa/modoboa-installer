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
from modoboa_installer import utils


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
    parser.add_argument("domain", type=str,
                        help="The main domain of your future mail server")
    args = parser.parse_args(input_args)

    if args.debug:
        utils.ENV["debug"] = True
    utils.printcolor("Welcome to Modoboa installer!", utils.GREEN)
    utils.check_config_file(args.configfile, args.interactive)
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
    utils.printcolor(
        "Your mail server will be installed with the following components:",
        utils.BLUE)
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
    if ssl_backend:
        ssl_backend.create()
    scripts.install("amavis", config)
    scripts.install("modoboa", config)
    scripts.install("automx", config)
    scripts.install("uwsgi", config)
    scripts.install("nginx", config)
    scripts.install("postfix", config)
    scripts.install("dovecot", config)
    utils.printcolor(
        "Congratulations! You can enjoy Modoboa at https://{} (admin:password)"
        .format(config.get("general", "hostname")),
        utils.GREEN)


if __name__ == "__main__":
    main(sys.argv[1:])
