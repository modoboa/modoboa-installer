"""Installer unit tests."""

import os
import shutil
import sys
import tempfile
import unittest

from six import StringIO
from six.moves import configparser
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

    @patch("modoboa_installer.utils.user_input")
    def test_interactive_mode(self, mock_user_input):
        """Check interactive mode."""
        mock_user_input.side_effect = [
            "0", "0", "", "", "", "", ""
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
    def test_interactive_mode_letsencrypt(self, mock_user_input):
        """Check interactive mode."""
        mock_user_input.side_effect = [
            "1", "admin@example.test", "0", "", "", "", "", ""
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
            "modoboa automx amavis clamav dovecot nginx razor postfix"
            " postwhite spamassassin uwsgi",
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


if __name__ == "__main__":
    unittest.main()
