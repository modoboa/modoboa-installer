"""Python related tools."""

import os
import sys

from . import package
from . import utils


def get_pip_path(venv):
    """Return the full path to pip command."""
    binpath = "pip"
    if venv:
        binpath = os.path.join(venv, "bin", binpath)
    return binpath


def install_packages(names, venv=None, upgrade=False, **kwargs):
    """Install a Python package using pip."""
    cmd = "{} install{}{} {}".format(
        get_pip_path(venv),
        " -U " if upgrade else "",
        " --pre" if kwargs.pop("beta", False) else "",
        " ".join(names)
    )
    utils.exec_or_fail(cmd, "Failed to install Python packages", **kwargs)


def get_package_version(name, venv=None, **kwargs):
    """Returns the version of an installed package."""
    cmd = "{} show {}".format(
        get_pip_path(venv),
        name
    )
    exit_code, output = utils.exec_cmd(cmd, **kwargs)
    if exit_code != 0:
        utils.error(f"Failed to get version of {name}. "
                    f"Output is: {output}")
        sys.exit(1)

    version_list_clean = []
    for line in output.decode().split("\n"):
        if not line.startswith("Version:"):
            continue
        version_item_list = line.split(":")
        version_list = version_item_list[1].split(".")
        for element in version_list:
            try:
                version_list_clean.append(int(element))
            except ValueError:
                utils.printcolor(
                    f"Failed to decode some part of the version of {name}",
                    utils.YELLOW)
                version_list_clean.append(element)
    if len(version_list_clean) == 0:
        utils.printcolor(
            f"Failed to find the version of {name}",
            utils.RED)
        sys.exit(1)
    return version_list_clean


def setup_virtualenv(path, sudo_user=None):
    """Install a virtualenv if needed."""
    if os.path.exists(path):
        return
    package.backend.install_many(["python3-venv"])
    with utils.settings(sudo_user=sudo_user):
        utils.exec_cmd("python3 -m venv {}".format(path))
        install_packages(["pip", "setuptools"], venv=path, upgrade=True)
