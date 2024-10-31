"""Checks to be performed before any install or upgrade"""

import sys
from urllib.request import urlopen

from modoboa_installer import utils


def check_version():
    local_version = ""
    with open("version.txt", "r") as version:
        local_version = version.readline()
    remote_version = ""
    with urlopen("https://raw.githubusercontent.com/modoboa/modoboa-installer/master/version.txt") as r_version:
        remote_version = r_version.read().decode()
    if local_version == "" or remote_version == "":
        utils.printcolor(
            "Could not check that your installer is up-to-date: "
            f"local version: {local_version}, "
            f"remote version: {remote_version}",
            utils.YELLOW
        )
    if remote_version != local_version:
        utils.error(
            "Your installer seems outdated.\n"
            "Check README file for instructions about how to update.\n"
            "No support will be provided without an up-to-date installer!"
        )
        answer = utils.user_input("Continue anyway? (Y/n) ")
        if not answer.lower().startswith("y"):
            sys.exit(0)
    else:
        utils.success("Installer seems up to date!")


def handle():
    check_version()
