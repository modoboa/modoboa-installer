"""uWSGI related tools."""

import os

from .. import package
from .. import system
from .. import utils

from . import base


class Uwsgi(base.Installer):

    """uWSGI installer."""

    appname = "uwsgi"
    packages = {
        "deb": ["uwsgi", "uwsgi-plugin-python"],
        "rpm": ["uwsgi", "uwsgi-plugin-python"],
    }

    @property
    def socket_path(self):
        """Return socket path."""
        if package.backend.FORMAT == "deb":
            return "/run/uwsgi/app/modoboa_instance/socket"
        return "/run/uwsgi/modoboa_instance.sock"

    def get_template_context(self):
        """Additionnal variables."""
        context = super(Uwsgi, self).get_template_context()
        context.update({
            "modoboa_user": self.config.get("modoboa", "user"),
            "modoboa_venv_path": self.config.get("modoboa", "venv_path"),
            "modoboa_instance_path": (
                self.config.get("modoboa", "instance_path")),
            "uwsgi_socket_path": self.socket_path,
        })
        return context

    def get_config_dir(self):
        """Return appropriate configuration directory."""
        if package.backend.FORMAT == "deb":
            return os.path.join(self.config_dir, "apps-available")
        return "{}.d".format(self.config_dir)

    def post_run(self):
        """Additionnal tasks."""
        context = self.get_template_context()
        src = self.get_file_path("uwsgi.ini.tpl")
        dst = os.path.join(self.get_config_dir(), "modoboa_instance.ini")
        utils.copy_from_template(src, dst, context)
        if package.backend.FORMAT == "deb":
            link = os.path.join(
                self.config_dir, "apps-enabled", os.path.basename(dst))
            if os.path.exists(link):
                return
            os.symlink(dst, link)
        else:
            system.add_user_to_group(
                "uwsgi", self.config.get("modoboa", "user"))
            utils.exec_cmd("chmod -R g+w {}/media".format(
                self.config.get("modoboa", "instance_path")))
            utils.exec_cmd("chmod -R g+w {}/pdfcredentials".format(
                self.config.get("modoboa", "home_dir")))
            pattern = (
                "s/emperor-tyrant = true/emperor-tyrant = false/")
            utils.exec_cmd(
                "perl -pi -e '{}' /etc/uwsgi.ini".format(pattern))

    def restart_daemon(self):
        """Restart daemon process."""
        code, output = utils.exec_cmd("service uwsgi status modoboa_instance")
        action = "start" if code else "restart"
        utils.exec_cmd("service uwsgi {}".format(action))
