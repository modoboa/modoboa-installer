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

    def get_template_context(self, app):
        """Additionnal variables."""
        context = super(Nginx, self).get_template_context()
        context.update({
            "app_instance_path": (
                self.config.get(app, "instance_path")),
            "uwsgi_socket_path": Uwsgi(self.config).get_socket_path(app)
        })
        return context

    def _setup_config(self, app, hostname=None):
        """Custom app configuration."""
        if hostname is None:
            hostname = self.config.get("general", "hostname")
        context = self.get_template_context(app)
        context.update({"hostname": hostname})
        src = self.get_file_path("{}.conf.tpl".format(app))
        if package.backend.FORMAT == "deb":
            dst = os.path.join(
                self.config_dir, "sites-available", "{}.conf".format(hostname))
            utils.copy_from_template(src, dst, context)
            link = os.path.join(
                self.config_dir, "sites-enabled", os.path.basename(dst))
            if os.path.exists(link):
                return
            os.symlink(dst, link)
            group = self.config.get(app, "user")
            user = "www-data"
        else:
            dst = os.path.join(
                self.config_dir, "conf.d", "{}.conf".format(hostname))
            utils.copy_from_template(src, dst, context)
            group = "uwsgi"
            user = "nginx"
        system.add_user_to_group(user, group)

    def post_run(self):
        """Additionnal tasks."""
        self._setup_config("modoboa")
        if self.config.getboolean("automx", "enabled"):
            hostname = "autoconfig.{}".format(
                self.config.get("general", "domain"))
            self._setup_config("automx", hostname)
        if not os.path.exists("{}/dhparam.pem".format(self.config_dir)):
            cmd = "openssl dhparam -dsaparam -out dhparam.pem 4096"
            utils.exec_cmd(cmd, cwd=self.config_dir)
