"""Package management related tools."""

import re

from os.path import isfile as file_exists

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
        super().__init__(dist_name)
        self.index_updated = False
        self.policy_file = "/usr/sbin/policy-rc.d"

    def prepare_system(self):
        """Make sure services don't start at installation."""
        with open(self.policy_file, "w") as fp:
            fp.write("exit 101\n")
        utils.exec_cmd("chmod +x {}".format(self.policy_file))

    def restore_system(self):
        utils.exec_cmd("rm -f {}".format(self.policy_file))

    def add_custom_repository(self,
                              name: str,
                              url: str,
                              key_url: str,
                              codename: str,
                              with_source: bool = True):
        key_file = f"/etc/apt/keyrings/{name}.gpg"
        utils.exec_cmd(
            f"wget -O - {key_url} | gpg --dearmor | tee {key_file} > /dev/null"
        )
        line_types = ["deb"]
        if with_source:
            line_types.append("deb-src")
        for line_type in line_types:
            line = (
                f"{line_type} [arch=amd64 signed-by={key_file}] "
                f"{url} {codename} main"
            )
            target_file = f"/etc/apt/sources.list.d/{name}.list"
            tee_option = "-a" if file_exists(target_file) else ""
            utils.exec_cmd(f'echo "{line}" | tee {tee_option} {target_file}')
        self.index_updated = False

    def update(self):
        """Update local cache."""
        if self.index_updated:
            return
        utils.exec_cmd("apt-get -o Dpkg::Progress-Fancy=0 update --quiet")
        self.index_updated = True

    def preconfigure(self, name, question, qtype, answer):
        """Pre-configure a package before installation."""
        line = "{0} {0}/{1} {2} {3}".format(name, question, qtype, answer)
        utils.exec_cmd("echo '{}' | debconf-set-selections".format(line))

    def install(self, name):
        """Install a package."""
        self.update()
        utils.exec_cmd("apt-get -o Dpkg::Progress-Fancy=0 install --quiet --assume-yes {}".format(name))

    def install_many(self, names):
        """Install many packages."""
        self.update()
        return utils.exec_cmd("apt-get -o Dpkg::Progress-Fancy=0 install --quiet --assume-yes {}".format(
            " ".join(names)))

    def get_installed_version(self, name):
        """Get installed package version."""
        code, output = utils.exec_cmd(
            "dpkg -s {} | grep Version".format(name))
        match = re.match(r"Version: (\d:)?(.+)-\d", output.decode())
        if match:
            return match.group(2)
        return None


class RPMPackage(Package):
    """RPM based operations."""

    FORMAT = "rpm"

    def __init__(self, dist_name):
        """Initialize backend."""
        super().__init__(dist_name)
        if "centos" in dist_name:
            self.install("epel-release")

    def install(self, name):
        """Install a package."""
        utils.exec_cmd("yum install -y --quiet {}".format(name))

    def install_many(self, names):
        """Install many packages."""
        return utils.exec_cmd("yum install -y --quiet {}".format(" ".join(names)))

    def get_installed_version(self, name):
        """Get installed package version."""
        code, output = utils.exec_cmd(
            "rpm -qi {} | grep Version".format(name))
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
