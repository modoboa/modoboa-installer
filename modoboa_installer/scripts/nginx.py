"""Nginx related tools."""

import os

from .. import package
from .. import system
from .. import utils

from . import base
from .uwsgi import Uwsgi


class Nginx(base.Installer):

    """Nginx installer."""

    appname = "nginx"
    packages = {
        "deb": ["nginx", "ssl-cert"],
        "rpm": ["nginx"]
    }

    def get_template_context(self):
        """Additionnal variables."""
        context = super(Nginx, self).get_template_context()
        context.update({
            "modoboa_instance_path": (
                self.config.get("modoboa", "instance_path")),
            "uwsgi_socket_path": Uwsgi(self.config).socket_path
        })
        return context

    def post_run(self):
        """Additionnal tasks."""
        hostname = self.config.get("general", "hostname")
        context = self.get_template_context()
        src = self.get_file_path("nginx.conf.tpl")
        if package.backend.FORMAT == "deb":
            dst = os.path.join(
                self.config_dir, "sites-available", "{}.conf".format(hostname))
            utils.copy_from_template(src, dst, context)
            link = os.path.join(
                self.config_dir, "sites-enabled", os.path.basename(dst))
            if os.path.exists(link):
                return
            os.symlink(dst, link)
            group = self.config.get("modoboa", "user")
            user = "www-data"
        else:
            dst = os.path.join(
                self.config_dir, "conf.d", "{}.conf".format(hostname))
            utils.copy_from_template(src, dst, context)
            group = "uwsgi"
            user = "nginx"
        system.add_user_to_group(user, group)

        if not os.path.exists("{}/dhparam.pem".format(self.config_dir)):
            cmd = "openssl dhparam -dsaparam -out dhparam.pem 4096"
            utils.exec_cmd(cmd, cwd=self.config_dir)
