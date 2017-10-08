"""Installer unit tests."""

import os
import shutil
import tempfile
import unittest

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
        run.main([
            "--stop-after-configfile-check",
            "--configfile", self.cfgfile,
            "example.test"])
        self.assertTrue(os.path.exists(self.cfgfile))


if __name__ == "__main__":
    unittest.main()
