"""Redis related functions."""

from urllib.parse import quote

from .. import system
from .. import utils

from . import base

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = "6379"
DEFAULT_URL = f"redis://{DEFAULT_HOST}:{DEFAULT_PORT}/0"


def get_settings(config) -> tuple[str, str, str]:
    """Return the host, port and password of the Redis server to use.

    Older configuration files may not have a [redis] section.
    """
    return (
        config.get("redis", "host", fallback=DEFAULT_HOST),
        config.get("redis", "port", fallback=DEFAULT_PORT),
        config.get("redis", "password", fallback=""),
    )


def format_host(host: str) -> str:
    """Return the host as it must be written in a "host:port" address."""
    return f"[{host}]" if ":" in host else host


def get_url(config) -> str:
    """Return the URL used to connect to Redis."""
    host, port, password = get_settings(config)
    auth = f":{quote(password, safe='')}@" if password else ""
    return f"redis://{auth}{format_host(host)}:{port}/0"


class Redis(base.Installer):
    """Redis installer.

    Nothing is installed if the section is disabled: the server described
    in the configuration is used as is.
    """

    appname = "redis"
    daemon_name = "redis-server"
    packages = ["redis-server"]

    def pre_run(self):
        """A local installation only provides a default local server."""
        host, port, password = get_settings(self.config)
        if host not in (DEFAULT_HOST, "localhost"):
            raise utils.FatalError(
                f"Redis is configured on {host} but the installer is "
                "asked to install it on this server. Set 'enabled = false' "
                "in the [redis] section to use an existing server."
            )
        if port != DEFAULT_PORT or password:
            raise utils.FatalError(
                "The local Redis server is installed with its default port "
                "and no password. Set 'enabled = false' in the [redis] "
                "section to use a server with other settings."
            )

    def post_run(self):
        """Make sure the server is running before it is used."""
        system.enable_and_start_service(self.get_daemon_name())
