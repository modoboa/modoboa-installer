"""fail2ban related functions."""

from . import base


class Fail2ban(base.Installer):
    """Fail2ban installer."""

    appname = "fail2ban"
    packages = ["fail2ban"]
    config_files = [
        "jail.d/modoboa.conf",
        "filter.d/modoboa-auth.conf",
    ]
