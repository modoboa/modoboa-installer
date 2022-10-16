"""Package management related tools."""

import re

from . import utils


class Package(object):
    """Base classe."""

    def __init__(self, dist_name):
        """Constructor."""
        self.dist_name = dist_name

    def preconfigure(self, name, question, qtype, answer):
        """Empty method."""
        pass

    def prepare_system(self):
        pass

    def restore_system(self):
        pass


class DEBPackage(Package):
    """DEB based operations."""

    FORMAT = "deb"

    def __init__(self, dist_name):
        super(DEBPackage, self).__init__(dist_name)
        self.index_updated = False
        self.policy_file = "/usr/sbin/policy-rc.d"

    def prepare_system(self):
        """Make sure services don't start at installation."""
        with open(self.policy_file, "w") as fp:
            fp.write("exit 101\n")
        utils.exec_cmd("chmod +x {}".format(self.policy_file))

    def restore_system(self):
        utils.exec_cmd("rm -f {}".format(self.policy_file))

    def update(self):
        """Update local cache."""
        if self.index_updated:
            return
        utils.exec_cmd("apt-get update --quiet")
        self.index_updated = True

    def preconfigure(self, name, question, qtype, answer):
        """Pre-configure a package before installation."""
        line = "{0} {0}/{1} {2} {3}".format(name, question, qtype, answer)
        utils.exec_cmd("echo '{}' | debconf-set-selections".format(line))

    def install(self, name):
        """Install a package."""
        self.update()
        utils.exec_cmd("apt-get install --quiet --assume-yes {}".format(name))

    def install_many(self, names):
        """Install many packages."""
        self.update()
        return utils.exec_cmd("apt-get install --quiet --assume-yes {}".format(
            " ".join(names)))

    def get_installed_version(self, name):
        """Get installed package version."""
        code, output = utils.exec_cmd(
            "dpkg -s {} | grep Version".format(name), capture_output=True)
        match = re.match(r"Version: (\d:)?(.+)-\d", output.decode())
        if match:
            return match.group(2)
        return None


class RPMPackage(Package):
    """RPM based operations."""

    FORMAT = "rpm"

    def __init__(self, dist_name):
        """Initialize backend."""
        self.dist_name = dist_name
        super(RPMPackage, self).__init__(dist_name)

    def prepare_system(self):
        if "centos" in self.dist_name:
            utils.exec_cmd("dnf config-manager --set-enabled crb")
            self.install("epel-release")
        self.update()

    def update(self):
        """Update the database repo."""
        utils.exec_cmd("dnf update -y --quiet")

    def install(self, name):
        """Install a package."""
        """Need to add check for rrdtool, sendmail-milter, libmemcached and --enablerepo=crb"""
        utils.exec_cmd("dnf install -y --quiet {}".format(name))

    def install_many(self, names):
        """Install many packages."""
        return utils.exec_cmd("dnf install -y --quiet {}".format(" ".join(names)))

    def get_installed_version(self, name):
        """Get installed package version."""
        code, output = utils.exec_cmd(
            "rpm -qi {} | grep Version".format(name), capture_output=True)
        match = re.match(r"Version\s+: (.+)", output.decode())
        if match:
            return match.group(1)
        return None


def get_backend():
    """Return the appropriate package backend."""
    distname = utils.dist_name()
    backend = None
    if distname in ["debian", "debian gnu/linux", "ubuntu"]:
        backend = DEBPackage
    elif "centos" in distname:
        backend = RPMPackage
    else:
        raise NotImplementedError(
            "Sorry, this distribution is not supported yet.")
    return backend(distname)


backend = get_backend()
