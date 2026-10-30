"""uWSGI related tools."""

import os

from .. import utils

from . import base

# Instance serving the OAuth2 introspection endpoint only
INTROSPECTION_INSTANCE = "modoboa_introspect"


class Uwsgi(base.Installer):
    """uWSGI installer."""

    appname = "uwsgi"
    packages = ["uwsgi", "uwsgi-plugin-python3"]

    def get_socket_path(self, app):
        """Return socket path."""
        return "/run/uwsgi/app/{}_instance/socket".format(app)

    def get_template_context(self, app):
        """Additionnal variables."""
        context = super(Uwsgi, self).get_template_context()
        context.update({
            "app_user": self.config.get(app, "user"),
            "app_venv_path": self.config.get(app, "venv_path"),
            "app_instance_path": (
                self.config.get(app, "instance_path")),
            "uwsgi_socket_path": self.get_socket_path(app),
            "uwsgi_plugin": "python3",
        })
        return context

    def get_config_dir(self):
        """Return appropriate configuration directory."""
        return os.path.join(self.config_dir, "apps-available")

    def _enable_config_debian(self, dst):
        """Enable config file."""
        link = os.path.join(
            self.config_dir, "apps-enabled", os.path.basename(dst))
        if os.path.exists(link):
            return
        os.symlink(dst, link)

    def _setup_config(self, app, name=None):
        """Common setup code.

        :param app: the application section to read settings from
        :param name: the instance name, when an application runs more
                     than one instance (defaults to ``app``)
        """
        name = name or app
        context = self.get_template_context(app)
        context["uwsgi_socket_path"] = self.get_socket_path(name)
        src = self.get_file_path("{}.ini.tpl".format(name))
        dst = os.path.join(
            self.get_config_dir(), "{}_instance.ini".format(name))
        utils.copy_from_template(src, dst, context)
        return dst

    def _setup_modoboa_config(self):
        """Custom modoboa configuration."""
        dst = self._setup_config("modoboa")
        # The OAuth2 introspection endpoint, called by Dovecot while
        # the main instance waits for it, gets its own workers
        introspection_dst = self._setup_config("modoboa", INTROSPECTION_INSTANCE)
        self._enable_config_debian(dst)
        self._enable_config_debian(introspection_dst)

    def post_run(self):
        """Additionnal tasks."""
        self._setup_modoboa_config()
