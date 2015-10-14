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
        return
    cmd = "useradd -m "
    if home:
        cmd += "-d {} ".format(home)
    utils.exec_cmd("{} {}".format(cmd, name))


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
