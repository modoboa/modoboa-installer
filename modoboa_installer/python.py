"""Python related tools."""

import os

from . import package
from . import utils


def get_path(cmd, venv=None):
    """Return path to cmd."""
    path = cmd
    if venv:
        path = os.path.join(venv, "bin", path)
    return path


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


def install_package_from_repository(name, url, vcs="git", venv=None, **kwargs):
    """Install a Python package from its repository."""
    cmd = "{} install -e {}+{}#egg={}".format(
        get_pip_path(venv), vcs, url, name)
    utils.exec_cmd(cmd, **kwargs)


def setup_virtualenv(path, sudo_user=None, python_version=2):
    """Install a virtualenv if needed."""
    if os.path.exists(path):
        return
    if python_version == 2:
        packages = ["python-virtualenv"]
        if utils.dist_name() == "debian":
            packages.append("virtualenv")
    else:
        packages = ["python3-venv"]
    package.backend.install_many(packages)
    with utils.settings(sudo_user=sudo_user):
        if python_version == 2:
            utils.exec_cmd("virtualenv {}".format(path))
        else:
            utils.exec_cmd("python3 -m venv {}".format(path))
        install_package("pip", venv=path, upgrade=True)
