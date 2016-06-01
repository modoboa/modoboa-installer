"""SSL tools."""

import os

from . import utils


class CertificateBackend(object):
    """Base class."""

    def __init__(self, config):
        """Set path to certificates."""
        self.config = config
        for base_dir in ["/etc/pki/tls", "/etc/ssl"]:
            if os.path.exists(base_dir):
                self.config.set(
                    "general", "tls_key_file",
                    "{}/private/%(hostname)s.key".format(base_dir))
                self.config.set(
                    "general", "tls_cert_file",
                    "{}/certs/%(hostname)s.cert".format(base_dir))
                return
        raise RuntimeError("Cannot find a directory to store certificate")


class SelfSignedCertificate(CertificateBackend):
    """Create a self signed certificate."""

    def create(self):
        """Create a certificate."""
        if os.path.exists(self.config.get("general", "tls_key_file")):
            answer = utils.user_input(
                "Overwrite the existing SSL certificate? (y/N) ")
            if not answer.lower().startswith("y"):
                return
        utils.printcolor(
            "Generating new self-signed certificate", utils.YELLOW)
        utils.exec_cmd(
            "openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 "
            "-subj '/CN={}' -keyout {} -out {}".format(
                self.config.get("general", "hostname"),
                self.config.get("general", "tls_key_file"),
                self.config.get("general", "tls_cert_file"))
        )


def get_backend(config):
    """Return the appropriate backend."""
    return SelfSignedCertificate(config)
