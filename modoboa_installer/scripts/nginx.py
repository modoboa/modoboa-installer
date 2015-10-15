"""Nginx related tools."""

import os

from .. import system
from .. import utils

from . import base


class Nginx(base.Installer):

    """Nginx installer."""

    appname = "nginx"
    packages = ["nginx", "ssl-cert"]

    def get_template_context(self):
        """Additionnal variables."""
        context = super(Nginx, self).get_template_context()
        context.update({
            "modoboa_instance_path": (
                self.config.get("modoboa", "instance_path")),
            "uwsgi_socket_path": self.config.get("uwsgi", "socket_path")
        })
        return context

    def post_run(self):
        """Additionnal tasks."""
        hostname = self.config.get("general", "hostname")
        context = self.get_template_context()
        src = self.get_file_path("nginx.conf.tpl")
        dst = os.path.join(
            self.config_dir, "sites-available", "{}.conf".format(hostname))
        utils.copy_from_template(src, dst, context)
        link = os.path.join(
            self.config_dir, "sites-enabled", os.path.basename(dst))
        if os.path.exists(link):
            return
        os.symlink(dst, link)
        system.add_user_to_group(
            "www-data", self.config.get("modoboa", "user"))
