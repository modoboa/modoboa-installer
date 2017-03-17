"""System related functions."""

import grp
import pwd
import sys

from . import utils


def create_user(name, home=None):
    """Create a new system user."""
    try:
        pwd.getpwnam(name)
    except KeyError:
        pass
    else:
        extra_message = "."
        if home:
            extra_message = (
                " but please make sure the {} directory exists.".format(
                    home))
        utils.printcolor(
            "User {} already exists, skipping creation{}".format(
                name, extra_message), utils.YELLOW)
        return
    cmd = "useradd -m "
    if home:
        cmd += "-d {} ".format(home)
    utils.exec_cmd("{} {}".format(cmd, name))
    if home:
        utils.exec_cmd("chmod 755 {}".format(home))


def add_user_to_group(user, group):
    """Add system user to group."""
    try:
        pwd.getpwnam(user)
    except KeyError:
        print("User {} does not exist".format(user))
        sys.exit(1)
    try:
        grp.getgrnam(group)
    except KeyError:
        print("Group {} does not exist".format(group))
        sys.exit(1)
    utils.exec_cmd("usermod -a -G {} {}".format(group, user))


def enable_service(name):
    """Enable a service at startup."""
    utils.exec_cmd("systemctl enable {}".format(name))


def enable_and_start_service(name):
    """Enable a start a service."""
    enable_service(name)
    code, output = utils.exec_cmd("service {} status".format(name))
    action = "start" if code else "restart"
    utils.exec_cmd("service {} {}".format(name, action))
