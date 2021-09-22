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


def install_package(name, venv=None, upgrade=False, binary=True, **kwargs):
    """Install a Python package using pip."""
    cmd = "{} install{}{}{} {}".format(
        get_pip_path(venv),
        " -U" if upgrade else "",
        " --no-binary :all:" if not binary else "",
        " --pre" if kwargs.pop("beta", False) else "",
        name
    )
    utils.exec_cmd(cmd, **kwargs)


def install_packages(names, venv=None, upgrade=False, **kwargs):
    """Install a Python package using pip."""
    cmd = "{} install{}{} {}".format(
        get_pip_path(venv),
        " -U " if upgrade else "",
        " --pre" if kwargs.pop("beta", False) else "",
        " ".join(names)
    )
    utils.exec_cmd(cmd, **kwargs)


def install_package_from_repository(name, url, vcs="git", venv=None, **kwargs):
    """Install a Python package from its repository."""
    if vcs == "git":
        package.backend.install("git")
    cmd = "{} install -e {}+{}#egg={}".format(
        get_pip_path(venv), vcs, url, name)
    utils.exec_cmd(cmd, **kwargs)


def setup_virtualenv(path, sudo_user=None, python_version=2):
    """Install a virtualenv if needed."""
    if os.path.exists(path):
        return
    if python_version == 2:
        python_binary = "python"
        packages = ["python-virtualenv"]
        if utils.dist_name() == "debian":
            packages.append("virtualenv")
    else:
        if utils.dist_name().startswith("centos"):
            python_binary = "python3"
            packages = ["python3"]
        else:
            python_binary = "python3"
            packages = ["python3-venv"]
    package.backend.install_many(packages)
    with utils.settings(sudo_user=sudo_user):
        if python_version == 2:
            utils.exec_cmd("virtualenv {}".format(path))
        else:
            utils.exec_cmd("{} -m venv {}".format(python_binary, path))
        install_packages(["pip", "setuptools"], venv=path, upgrade=True)
