"""Python related tools."""

import os

from . import package
from . import utils


def get_pip_path(venv):
    """Return the full path to pip command."""
    binpath = "pip"
    if venv:
        binpath = os.path.join(venv, "bin", binpath)
    return binpath


def install_package(name, venv=None, upgrade=False, **kwargs):
    """Install a Python package using pip."""
    cmd = "{} install {}{}".format(
        get_pip_path(venv), " -U " if upgrade else "", name)
    utils.exec_cmd(cmd, **kwargs)


def install_packages(names, venv=None, upgrade=False, **kwargs):
    """Install a Python package using pip."""
    cmd = "{} install {}{}".format(
        get_pip_path(venv), " -U " if upgrade else "", " ".join(names))
    utils.exec_cmd(cmd, **kwargs)


def setup_virtualenv(path, sudo_user=None):
    """Install a virtualenv if needed."""
    if os.path.exists(path):
        return
    package.backend.install("python-virtualenv")
    with utils.settings(sudo_user=sudo_user):
        utils.exec_cmd("virtualenv {}".format(path))
        install_package("pip", venv=path, upgrade=True)
