"""Python related tools."""

import json
import os
import sys

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


def get_package_version(name, venv=None, **kwargs):
    """Returns the version of an installed package."""
    cmd = f"{get_pip_path(venv)} list --format json"
    exit_code, output = utils.exec_cmd(cmd, **kwargs)
    if exit_code != 0:
        utils.error(f"Failed to get version of {name}. "
                    f"Output is: {output}")
        sys.exit(1)

    print(f"name: {name}, venv: {venv}, cmd: {cmd}, exit_code: {exit_code}, output: {output.decode()}")
    list_dict = json.loads(output.decode())
    version_list = []
    for element in list_dict:
        if element["name"] == name:
            version_list = element["version"].split(".")
            break
    version_list_clean = []
    for element in version_list:
        try:
            version_list_clean.append(int(element))
        except ValueError:
            utils.printcolor(
                f"Failed to decode some part of the version of {name}",
                utils.YELLOW)
            version_list_clean.append(element)
    return version_list_clean


def install_package_from_repository(name, url, vcs="git", venv=None, **kwargs):
    """Install a Python package from its repository."""
    if vcs == "git":
        package.backend.install("git")
    cmd = "{} install -e {}+{}#egg={}".format(
        get_pip_path(venv), vcs, url, name)
    utils.exec_cmd(cmd, **kwargs)


def install_package_from_remote_requirements(url, venv=None, **kwargs):
    """Install a Python package from a file."""
    cmd = "{} install {} {}".format(
        get_pip_path(venv),
        "-r",
        url
    )
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
        install_packages(["pip", "setuptools\<58.0.0"], venv=path, upgrade=True)
