"""SSL tools."""

import os
import sys

from . import package
from . import utils


class CertificateBackend(object):
    """Base class."""

    def __init__(self, config):
        """Set path to certificates."""
        self.config = config

    def overwrite_existing_certificate(self):
        """Check if certificate already exists."""
        if os.path.exists(self.config.get("general", "tls_key_file")):
            if not self.config.getboolean("general", "force"):
                answer = utils.user_input(
                    "Overwrite the existing SSL certificate? (y/N) ")
                if not answer.lower().startswith("y"):
                    return False
        return True


class ManualCertification(CertificateBackend):
    """Use certificate provided."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path_correct = True
        self.tls_cert_file_path = self.config.get("certificate",
                                                  "tls_key_file_path")
        self.tls_key_file_path = self.config.get("certificate",
                                                 "tls_cert_file_path")

        if not os.path.exists(self.tls_key_file_path):
            utils.error("'tls_key_file_path' path is not accessible")
            path_correct = False
        if not os.path.exists(self.tls_cert_file_path):
            utils.error("'tls_cert_file_path' path is not accessible")
            path_correct = False

        if not path_correct:
            sys.exit(1)

    def generate_cert(self):
        self.config.set("general", "tls_key_file",
                        self.tls_key_file_path)
        self.config.set("general", "tls_cert_file",
                        self.tls_cert_file_path)


class SelfSignedCertificate(CertificateBackend):
    """Create a self signed certificate."""

    def __init__(self, *args, **kwargs):
        """Sanity checks."""
        super(SelfSignedCertificate, self).__init__(*args, **kwargs)
        if self.config.has_option("general", "tls_key_file"):
            # Compatibility
            return
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

    def generate_cert(self):
        """Create a certificate."""
        if not self.overwrite_existing_certificate():
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


class LetsEncryptCertificate(CertificateBackend):
    """Create a certificate using letsencrypt."""

    def __init__(self, *args, **kwargs):
        """Update config."""
        super(LetsEncryptCertificate, self).__init__(*args, **kwargs)
        self.hostname = self.config.get("general", "hostname")
        self.config.set("general", "tls_cert_file", (
            "/etc/letsencrypt/live/{}/fullchain.pem".format(self.hostname)))
        self.config.set("general", "tls_key_file", (
            "/etc/letsencrypt/live/{}/privkey.pem".format(self.hostname)))

    def install_certbot(self):
        """Install certbot script to generate cert."""
        name, version = utils.dist_info()
        name = name.lower()
        if name == "ubuntu":
            package.backend.update()
            package.backend.install("software-properties-common")
            utils.exec_cmd("add-apt-repository -y universe")
            if version == "18.04":
                utils.exec_cmd("add-apt-repository -y ppa:certbot/certbot")
            package.backend.update()
            package.backend.install("certbot")
        elif name.startswith("debian"):
            package.backend.update()
            package.backend.install("certbot")
        elif "centos" in name:
            package.backend.install("certbot")
        else:
            utils.printcolor("Failed to install certbot, aborting.")
            sys.exit(1)
        # Nginx plugin certbot
        if (
                self.config.has_option("nginx", "enabled") and
                self.config.getboolean("nginx", "enabled")
        ):
            if name == "ubuntu" or name.startswith("debian"):
                package.backend.install("python3-certbot-nginx")

    def generate_cert(self):
        """Create a certificate."""
        utils.printcolor(
            "Generating new certificate using letsencrypt", utils.YELLOW)
        self.install_certbot()
        utils.exec_cmd(
            "certbot certonly -n --standalone -d {} -m {} --agree-tos"
            .format(
                self.hostname, self.config.get("letsencrypt", "email")))
        with open("/etc/cron.d/letsencrypt", "w") as fp:
            fp.write("0 */12 * * * root certbot renew "
                     "--quiet\n")
        cfg_file = "/etc/letsencrypt/renewal/{}.conf".format(self.hostname)
        pattern = "s/authenticator = standalone/authenticator = nginx/"
        utils.exec_cmd("perl -pi -e '{}' {}".format(pattern, cfg_file))


def get_backend(config):
    """Return the appropriate backend."""
    cert_type = config.get("certificate", "type")
    if cert_type == "letsencrypt":
        return LetsEncryptCertificate(config)
    if cert_type == "manual":
        return ManualCertification(config)
    return SelfSignedCertificate(config)
