"""SSL tools."""

import os

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

    def create(self):
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

    def create(self):
        """Create a certificate."""
        utils.printcolor(
            "Generating new certificate using letsencrypt", utils.YELLOW)
        hostname = self.config.get("general", "hostname")
        utils.exec_cmd(
            "wget https://dl.eff.org/certbot-auto; chmod a+x certbot-auto",
            cwd="/opt")
        utils.exec_cmd(
            "/opt/certbot-auto certonly -n --standalone -d {} "
            "-m {} --agree-tos".format(
                hostname, self.config.get("letsencrypt", "email")))
        self.config.set("general", "tls_cert_file", (
            "/etc/letsencrypt/live/{}/fullchain.pem".format(hostname)))
        self.config.set("general", "tls_key_file", (
            "/etc/letsencrypt/live/{}/privkey.pem".format(hostname)))
        with open("/etc/cron.d/letsencrypt", "w") as fp:
            fp.write("0 */12 * * * root /opt/certbot-auto renew "
                     "--quiet --no-self-upgrade --force-renewal\n")
        cfg_file = "/etc/letsencrypt/renewal/{}.conf".format(hostname)
        pattern = "s/authenticator = standalone/authenticator = nginx/"
        utils.exec_cmd("perl -pi -e '{}' {}".format(pattern, cfg_file))


def get_backend(config):
    """Return the appropriate backend."""
    if not config.getboolean("certificate", "generate"):
        return None
    if config.get("certificate", "type") == "letsencrypt":
        return LetsEncryptCertificate(config)
    return SelfSignedCertificate(config)
