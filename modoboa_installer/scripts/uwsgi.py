"""uWSGI related tools."""

import os

from .. import utils

from . import base


class Uwsgi(base.Installer):

    """uWSGI installer."""

    appname = "uwsgi"
    packages = ["uwsgi", "uwsgi-plugin-python"]

    def get_template_context(self):
        """Additionnal variables."""
        context = super(Uwsgi, self).get_template_context()
        context.update({
            "modoboa_user": self.config.get("modoboa", "user"),
            "modoboa_venv_path": self.config.get("modoboa", "venv_path"),
            "modoboa_instance_path": (
                self.config.get("modoboa", "instance_path")),
            "uwsgi_socket_path": self.config.get("uwsgi", "socket_path")
        })
        return context

    def post_run(self):
        """Additionnal tasks."""
        context = self.get_template_context()
        src = self.get_file_path("uwsgi.ini.tpl")
        dst = os.path.join(
            self.config_dir, "apps-available", "modoboa_instance.ini")
        utils.copy_from_template(src, dst, context)
        link = os.path.join(
            self.config_dir, "apps-enabled", os.path.basename(dst))
        if os.path.exists(link):
            return
        os.symlink(dst, link)

    def restart_daemon(self):
        """Restart daemon process."""
        code, output = utils.exec_cmd("service uwsgi status modoboa_instance")
        action = "start" if code else "restart"
        utils.exec_cmd("service uwsgi {}".format(action))
