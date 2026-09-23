"""Installer unit tests."""

import os
import shutil
import sys
import tempfile
import unittest

from io import StringIO
from pathlib import Path

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import run


class ConfigFileTestCase(unittest.TestCase):
    """Test configuration file generation."""

    def setUp(self):
        """Create temp dir."""
        self.workdir = tempfile.mkdtemp()
        self.cfgfile = os.path.join(self.workdir, "installer.cfg")

    def tearDown(self):
        """Delete temp dir."""
        shutil.rmtree(self.workdir)

    def test_configfile_generation(self):
        """Check simple case."""
        out = StringIO()
        sys.stdout = out
        run.main([
            "--stop-after-configfile-check",
            "--configfile", self.cfgfile,
            "example.test"])
        self.assertTrue(os.path.exists(self.cfgfile))

    def test_razor_follows_amavis(self):
        """Razor is enabled with Amavis, which configures SpamAssassin to use it."""
        with open(os.devnull, "w") as fp:
            sys.stdout = fp
            run.main([
                "--stop-after-configfile-check",
                "--configfile", self.cfgfile,
                "example.test"])
        config = configparser.ConfigParser()
        config.read(self.cfgfile)
        self.assertEqual(config.get("antispam", "type"), "amavis")
        self.assertTrue(config.getboolean("spamassassin", "enabled"))
        self.assertTrue(config.getboolean("razor", "enabled"))

    def test_razor_disabled_with_rspamd(self):
        """Razor stays disabled when Rspamd replaces Amavis/SpamAssassin."""
        from modoboa_installer import config_dict_template, utils
        config = configparser.ConfigParser()
        config.add_section("antispam")
        config.set("antispam", "enabled", "true")
        config.set("antispam", "type", "rspamd")
        razor = next(
            section for section in config_dict_template.ConfigDictTemplate
            if section["name"] == "razor")
        entry = next(
            value for value in razor["values"] if value["option"] == "enabled")
        self.assertEqual(utils.get_entry_value(entry, False, config), "false")

    @patch("modoboa_installer.utils.user_input")
    def test_interactive_mode(self, mock_user_input):
        """Check interactive mode."""
        mock_user_input.side_effect = [
            "0", "0", "", "", "", "", "", ""
        ]
        with open(os.devnull, "w") as fp:
            sys.stdout = fp
            run.main([
                "--stop-after-configfile-check",
                "--configfile", self.cfgfile,
                "--interactive",
                "example.test"])
        self.assertTrue(os.path.exists(self.cfgfile))
        config = configparser.ConfigParser()
        config.read(self.cfgfile)
        self.assertEqual(config.get("certificate", "type"), "self-signed")
        self.assertEqual(config.get("database", "engine"), "postgres")

    @patch("modoboa_installer.utils.user_input")
    def test_updating_configfile(self, mock_user_input):
        """Check configfile update mechanism."""
        cfgfile_temp = os.path.join(self.workdir, "installer_old.cfg")

        out = StringIO()
        sys.stdout = out
        run.main([
            "--stop-after-configfile-check",
            "--configfile", cfgfile_temp,
            "example.test"])
        self.assertTrue(os.path.exists(cfgfile_temp))

        # Adding a dummy section
        with open(cfgfile_temp, "a") as fp:
            fp.write(
"""
[dummy]
    weird_old_option = "hey
""")
        mock_user_input.side_effect = ["y"]
        out = StringIO()
        sys.stdout = out
        run.main([
            "--stop-after-configfile-check",
            "--configfile", cfgfile_temp,
            "example.test"])
        self.assertIn("dummy", out.getvalue())
        self.assertTrue(Path(self.workdir).glob("*.old"))
        self.assertIn("Update complete",
                      out.getvalue()
        )

    @patch("modoboa_installer.utils.user_input")
    def test_interactive_mode_letsencrypt(self, mock_user_input):
        """Check interactive mode."""
        mock_user_input.side_effect = [
            "0", "0", "1", "admin@example.test", "0", "", "", "", ""
        ]
        with open(os.devnull, "w") as fp:
            sys.stdout = fp
            run.main([
                "--stop-after-configfile-check",
                "--configfile", self.cfgfile,
                "--interactive",
                "example.test"])
        self.assertTrue(os.path.exists(self.cfgfile))
        config = configparser.ConfigParser()
        config.read(self.cfgfile)
        self.assertEqual(config.get("certificate", "type"), "letsencrypt")
        self.assertEqual(
            config.get("letsencrypt", "email"), "admin@example.test")

    @patch("modoboa_installer.utils.user_input")
    def test_configfile_loading(self, mock_user_input):
        """Check interactive mode."""
        mock_user_input.side_effect = ["no"]
        out = StringIO()
        sys.stdout = out
        run.main([
            "--configfile", self.cfgfile,
            "example.test"])
        self.assertTrue(os.path.exists(self.cfgfile))
        self.assertIn(
            "fail2ban modoboa amavis clamav dovecot nginx razor "
            "postfix postwhite spamassassin uwsgi radicale opendkim",
            out.getvalue()
        )
        self.assertNotIn(
            "It seems that your config file is outdated.",
            out.getvalue()
        )

    @patch("modoboa_installer.utils.user_input")
    def test_upgrade_mode(self, mock_user_input):
        """Test upgrade mode launch."""
        mock_user_input.side_effect = ["no"]
        # 1. Generate a config file
        with open(os.devnull, "w") as fp:
            sys.stdout = fp
            run.main([
                "--stop-after-configfile-check",
                "--configfile", self.cfgfile,
                "example.test"])
        # 2. Run upgrade
        out = StringIO()
        sys.stdout = out
        run.main([
            "--configfile", self.cfgfile,
            "--upgrade",
            "example.test"])
        self.assertIn(
            "Your mail server is about to be upgraded and the following "
            "components will be impacted:",
            out.getvalue()
        )

    def test_upgrade_no_config_file(self):
        """Check config file existence check."""
        out = StringIO()
        sys.stdout = out
        with self.assertRaises(SystemExit):
            run.main([
                "--configfile", self.cfgfile,
                "--upgrade",
                "example.test"
            ])
        self.assertIn(
            "You cannot upgrade an existing installation without a "
            "configuration file.", out.getvalue()
        )


class IntrospectionInstanceTestCase(unittest.TestCase):
    """The OAuth2 introspection endpoint gets its own uWSGI instance."""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        cfgfile = os.path.join(self.workdir, "installer.cfg")
        with open(os.devnull, "w") as fp:
            sys.stdout = fp
            run.main([
                "--stop-after-configfile-check",
                "--configfile", cfgfile,
                "example.test"])
        self.config = configparser.ConfigParser()
        self.config.read(cfgfile)
        self.config.set("general", "domain", "example.test")
        self.config.set("uwsgi", "config_dir", self.workdir)
        for name in ["apps-available", "apps-enabled"]:
            os.mkdir(os.path.join(self.workdir, name))
        patcher = patch("modoboa_installer.package.backend")
        patcher.start().FORMAT = "deb"
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_uwsgi_instances(self):
        from modoboa_installer.scripts.uwsgi import Uwsgi

        Uwsgi(self.config, False, None)._setup_modoboa_config()

        for name in ["modoboa_instance", "modoboa_introspect_instance"]:
            self.assertTrue(os.path.islink(os.path.join(
                self.workdir, "apps-enabled", "{}.ini".format(name))))
        with open(os.path.join(
                self.workdir, "apps-available",
                "modoboa_introspect_instance.ini")) as fp:
            content = fp.read()
        self.assertIn("processes = 2\n", content)
        self.assertIn(
            "socket = /run/uwsgi/app/modoboa_introspect_instance/socket\n",
            content)
        with open(os.path.join(
                self.workdir, "apps-available", "modoboa_instance.ini")) as fp:
            content = fp.read()
        self.assertIn("processes = 4\n", content)
        self.assertIn(
            "socket = /run/uwsgi/app/modoboa_instance/socket\n", content)

    def test_nginx_routes_introspection(self):
        from modoboa_installer import utils
        from modoboa_installer.scripts.nginx import Nginx

        nginx = Nginx(self.config, False, None)
        context = nginx.get_template_context()
        context.update({
            "hostname": "mail.example.test",
            "extra_config": "",
            "tls_cert_file": "cert.pem",
            "tls_key_file": "key.pem",
        })
        with open(nginx.get_file_path("modoboa.conf.tpl")) as fp:
            content = utils.ConfigFileTemplate(fp.read()).substitute(context)
        self.assertIn(
            "server unix:/run/uwsgi/app/modoboa_introspect_instance/socket",
            content)
        self.assertIn(
            "location = /api/o/introspect/ {\n"
            "        include uwsgi_params;\n"
            "        uwsgi_param UWSGI_SCRIPT instance.wsgi:application;\n"
            "        uwsgi_pass modoboa_introspect;",
            content)


if __name__ == "__main__":
    unittest.main()
