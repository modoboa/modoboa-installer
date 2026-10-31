"""Package management related tools."""

import re

from . import utils


class DEBPackage:
    """DEB based operations."""

    def __init__(self):
        self.index_updated = False
        self.policy_file = "/usr/sbin/policy-rc.d"

    def enable_backports(self, codename):
        code, output = utils.exec_cmd(f"grep {codename}-backports /etc/apt/sources.list")
        if code:
            with open(f"/etc/apt/sources.list.d/backports.list", "w") as fp:
                fp.write(f"deb http://deb.debian.org/debian {codename}-backports main\n")
            self.update(force=True)

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
        with open(f"/etc/apt/sources.list.d/{name}.list", "w") as fp:
            for line_type in line_types:
                fp.write(
                    f"{line_type} [arch=amd64 signed-by={key_file}] "
                    f"{url} {codename} main\n"
                )
        self.index_updated = False

    def update(self, force=False):
        """Update local cache."""
        if self.index_updated and not force:
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
        utils.exec_cmd("apt-get -o Dpkg::Progress-Fancy=0 install --quiet --assume-yes -o DPkg::options::=--force-confold {}".format(name))

    def install_many(self, names):
        """Install many packages."""
        self.update()
        return utils.exec_cmd("apt-get -o Dpkg::Progress-Fancy=0 install --quiet --assume-yes -o DPkg::options::=--force-confold {}".format(
            " ".join(names)))

    def get_installed_version(self, name):
        """Get installed package version."""
        code, output = utils.exec_cmd(
            "dpkg -s {} | grep Version".format(name))
        match = re.match(r"Version: (\d:)?(.+)-\d", output.decode())
        if match:
            return match.group(2)
        return None


def get_backend():
    """Return the appropriate package backend."""
    if utils.dist_name() not in ["debian", "debian gnu/linux", "ubuntu"]:
        raise NotImplementedError(
            "Sorry, this distribution is not supported yet.")
    return DEBPackage()


backend = get_backend()
