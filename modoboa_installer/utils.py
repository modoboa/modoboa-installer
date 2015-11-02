"""Utility functions."""

import contextlib
import datetime
import glob
import os
import shutil
import string
import subprocess
import sys


ENV = {}
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)


class FatalError(Exception):

    """A simple exception."""

    pass


def user_input(message):
    """Ask something to the user."""
    try:
        from builtins import input
    except ImportError:
        answer = raw_input(message)
    else:
        answer = input(message)
    return answer


def exec_cmd(cmd, sudo_user=None, pinput=None, **kwargs):
    """Execute a shell command.
    Run a command using the current user. Set :keyword:`sudo_user` if
    you need different privileges.
    :param str cmd: the command to execute
    :param str sudo_user: a valid system username
    :param str pinput: data to send to process's stdin
    :rtype: tuple
    :return: return code, command output
    """
    sudo_user = ENV.get("sudo_user", sudo_user)
    if sudo_user is not None:
        cmd = "sudo -i -u %s %s" % (sudo_user, cmd)
    if "shell" not in kwargs:
        kwargs["shell"] = True
    if pinput is not None:
        kwargs["stdin"] = subprocess.PIPE
    capture_output = False
    if "capture_output" in kwargs:
        capture_output = kwargs.pop("capture_output")
    elif not ENV.get("debug"):
        capture_output = True
    if capture_output:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = None
    process = subprocess.Popen(cmd, **kwargs)
    if pinput or capture_output:
        c_args = [pinput] if pinput is not None else []
        output = process.communicate(*c_args)[0]
    else:
        process.wait()
    return process.returncode, output


def install_system_package(name, update=False):
    """Install a package system-wide."""
    if update:
        exec_cmd("apt-get update --quiet")
    exec_cmd("apt-get install --quiet --assume-yes {}".format(name))


def install_system_packages(names):
    """Install some packages system-wide."""
    exec_cmd("apt-get install --quiet --assume-yes {}".format(" ".join(names)))


def mkdir(path, mode, uid, gid):
    """Create a directory."""
    if not os.path.exists(path):
        os.mkdir(path, mode)
    else:
        os.chmod(path, mode)
    os.chown(path, uid, gid)


@contextlib.contextmanager
def settings(**kwargs):
    """Context manager to declare temporary settings."""
    for key, value in kwargs.items():
        ENV[key] = value
    yield
    for key in kwargs.keys():
        del ENV[key]


class ConfigFileTemplate(string.Template):

    """Custom class for configuration files."""

    delimiter = "%"


def backup_file(fname):
    """Create a backup of a given file."""
    for f in glob.glob("{}.old.*".format(fname)):
        os.unlink(f)
    bak_name = "{}.old.{}".format(
        fname, datetime.datetime.now().isoformat())
    shutil.copy(fname, bak_name)


def copy_file(src, dest):
    """Copy a file to a destination and make a backup before."""
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(src))
    if os.path.isfile(dest):
        backup_file(dest)
    shutil.copy(src, dest)


def copy_from_template(template, dest, context):
    """Create and copy a configuration file from a template."""
    now = datetime.datetime.now().isoformat()
    with open(template) as fp:
        buf = fp.read()
    if os.path.isfile(dest):
        backup_file(dest)
    with open(dest, "w") as fp:
        fp.write(
            "# This file was automatically installed on {}\n"
            .format(now))
        fp.write(ConfigFileTemplate(buf).substitute(context))


def has_colours(stream):
    """Check if terminal supports colors."""
    if not hasattr(stream, "isatty"):
        return False
    if not stream.isatty():
        return False  # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False
has_colours = has_colours(sys.stdout)


def printcolor(message, color):
    """Print a message using a green color."""
    if has_colours:
        message = "\x1b[1;{}m{}\x1b[0m".format(30 + color, message)
    print(message)
