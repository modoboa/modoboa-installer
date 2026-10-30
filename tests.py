"""Installer unit tests."""

import argparse
import configparser
import os
import shutil
import sys
import tempfile
import unittest

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import run
from modoboa_installer import utils


REAL_EXEC_CMD = utils.exec_cmd


def setUpModule():
    """Tests must reach neither GitHub nor the system they run on."""
    for target, return_value in [
        ("modoboa_installer.checks.handle", None),
        ("modoboa_installer.utils.exec_cmd", (0, b"")),
    ]:
        patcher = patch(target, return_value=return_value)
        patcher.start()
        unittest.addModuleCleanup(patcher.stop)


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
    def test_sharing_disabled_on_existing_installations(self, mock_user_input):
        """Sharing changes the IMAP separator: never enable it on update."""
        with open(os.devnull, "w") as fp:
            sys.stdout = fp
            run.main([
                "--stop-after-configfile-check",
                "--configfile", self.cfgfile,
                "example.test"])
        config = configparser.ConfigParser()
        config.read(self.cfgfile)
        self.assertTrue(config.getboolean("dovecot", "enable_sharing"))

        # Config file generated by an installer without sharing support
        config.remove_option("dovecot", "enable_sharing")
        with open(self.cfgfile, "w") as fp:
            config.write(fp)
        mock_user_input.side_effect = ["y"]
        with open(os.devnull, "w") as fp:
            sys.stdout = fp
            run.main([
                "--stop-after-configfile-check",
                "--configfile", self.cfgfile,
                "example.test"])
        config = configparser.ConfigParser()
        config.read(self.cfgfile)
        self.assertFalse(config.getboolean("dovecot", "enable_sharing"))

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
            "fail2ban redis modoboa amavis clamav dovecot nginx razor "
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


class HostnameConsistencyTestCase(unittest.TestCase):
    """Detect domains passed with a mail prefix (eg. mail.mail.domain)."""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.cfgfile = os.path.join(self.workdir, "installer.cfg")

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_check(self):
        from modoboa_installer import utils

        self.assertEqual(utils.check_hostname_consistency(
            "example.test", "mail.example.test"), [])
        self.assertEqual(utils.check_hostname_consistency(
            "example.co.uk", "mail.example.co.uk"), [])
        warnings = utils.check_hostname_consistency(
            "mail.example.test", "mail.mail.example.test")
        self.assertEqual(len(warnings), 2)
        self.assertIn("duplicated 'mail.' prefix", warnings[0])
        self.assertIn("you probably meant 'example.test'", warnings[1])
        warnings = utils.check_hostname_consistency(
            "MX.example.test", "mx.mx.example.test.")
        self.assertEqual(len(warnings), 2)
        warnings = utils.check_hostname_consistency(
            "mail.example.test", "mail.example.test")
        self.assertEqual(len(warnings), 1)
        self.assertIn("you probably meant 'example.test'", warnings[0])

    @patch("modoboa_installer.utils.user_input")
    def test_install_aborted(self, mock_user_input):
        mock_user_input.side_effect = [""]
        out = StringIO()
        sys.stdout = out
        run.main([
            "--configfile", self.cfgfile,
            "mail.example.test"])
        self.assertIn("duplicated 'mail.' prefix", out.getvalue())
        self.assertNotIn("Your mail server will be installed", out.getvalue())

    @patch("modoboa_installer.utils.user_input")
    def test_install_continued(self, mock_user_input):
        mock_user_input.side_effect = ["y", "no"]
        out = StringIO()
        sys.stdout = out
        run.main([
            "--configfile", self.cfgfile,
            "mail.example.test"])
        self.assertIn("duplicated 'mail.' prefix", out.getvalue())
        self.assertIn("Your mail server will be installed", out.getvalue())


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
        patcher.start()
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


class RedisTestCase(unittest.TestCase):
    """Redis is installed by its own script, or provided by another server."""

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
        self.config.set("modoboa", "version", "latest")
        patcher = patch("modoboa_installer.package.backend")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def set_external_redis(self, password=""):
        self.config.set("redis", "enabled", "false")
        self.config.set("redis", "host", "redis.example.test")
        self.config.set("redis", "port", "6380")
        self.config.set("redis", "password", password)

    def get_rspamd(self):
        from modoboa_installer.scripts.rspamd import Rspamd

        installer = Rspamd(self.config, False, None)
        installer.generate_password_condition = False
        return installer

    def get_modoboa(self):
        from modoboa_installer.scripts.modoboa import Modoboa

        return Modoboa(self.config, False, None)

    def render(self, installer, name):
        from modoboa_installer import utils

        with open(installer.get_file_path(name)) as fp:
            return utils.ConfigFileTemplate(fp.read()).substitute(
                installer.get_template_context())

    def test_redis_is_installed_first_by_its_own_script(self):
        from modoboa_installer.scripts.redis import Redis

        self.assertEqual(run.PRIMARY_APPS[0], "redis")
        self.assertTrue(self.config.getboolean("redis", "enabled"))
        redis = Redis(self.config, False, None)
        self.assertEqual(redis.get_packages(), ["redis-server"])
        self.assertEqual(redis.get_daemon_name(), "redis-server")

    def test_other_scripts_do_not_install_redis(self):
        packages = (
            list(self.get_modoboa().get_packages()) +
            list(self.get_rspamd().get_packages())
        )
        self.assertNotIn("redis", packages)
        self.assertNotIn("redis-server", packages)

    def test_local_install_starts_the_service(self):
        from modoboa_installer.scripts.redis import Redis

        with patch("modoboa_installer.system.enable_and_start_service") as svc:
            Redis(self.config, False, None).post_run()
        svc.assert_called_with("redis-server")

    def test_local_install_refuses_a_remote_host(self):
        from modoboa_installer import utils
        from modoboa_installer.scripts.redis import Redis

        self.config.set("redis", "host", "redis.example.test")
        with self.assertRaises(utils.FatalError):
            Redis(self.config, False, None).pre_run()
        self.config.set("redis", "host", "localhost")
        Redis(self.config, False, None).pre_run()

    def test_local_install_refuses_custom_port_or_password(self):
        from modoboa_installer import utils
        from modoboa_installer.scripts.redis import Redis

        self.config.set("redis", "port", "6380")
        with self.assertRaises(utils.FatalError):
            Redis(self.config, False, None).pre_run()
        self.config.set("redis", "port", "6379")
        self.config.set("redis", "password", "secret")
        with self.assertRaises(utils.FatalError):
            Redis(self.config, False, None).pre_run()

    def test_ipv6_host_is_bracketed(self):
        from modoboa_installer.scripts import redis

        self.set_external_redis()
        self.config.set("redis", "host", "2001:db8::1")
        self.assertEqual(
            redis.get_url(self.config), "redis://[2001:db8::1]:6380/0")
        content = self.render(self.get_rspamd(), "local.d/redis.conf.tpl")
        self.assertIn('write_servers = "[2001:db8::1]:6380";\n', content)

    def test_disabled_redis_is_not_installed(self):
        from modoboa_installer import scripts

        self.set_external_redis()
        with patch("modoboa_installer.scripts.redis.Redis.run") as run_redis:
            scripts.install("redis", self.config, False, None)
        run_redis.assert_not_called()

    def test_redis_url(self):
        from modoboa_installer.scripts import redis

        self.assertEqual(redis.get_url(self.config), redis.DEFAULT_URL)
        self.set_external_redis()
        self.assertEqual(
            redis.get_url(self.config), "redis://redis.example.test:6380/0")
        self.config.set("redis", "password", "p@ss:w/'rd")
        self.assertEqual(
            redis.get_url(self.config),
            "redis://:p%40ss%3Aw%2F%27rd@redis.example.test:6380/0")
        self.config.set("redis", "password", "a$b\\c d%%e")
        self.assertEqual(
            redis.get_url(self.config),
            "redis://:a%24b%5Cc%20d%25e@redis.example.test:6380/0")

    def test_config_without_redis_section(self):
        """An outdated installer.cfg that was not updated still works."""
        from modoboa_installer.scripts import redis

        self.config.remove_section("redis")
        self.assertEqual(redis.get_url(self.config), redis.DEFAULT_URL)
        context = self.get_rspamd().get_template_context()
        self.assertEqual(context["redis_host"], "127.0.0.1")
        self.assertEqual(context["redis_port"], "6379")
        self.assertEqual(context["redis_password_line"], "")
        self.get_modoboa().pre_run()

    def test_rspamd_default_configuration(self):
        content = self.render(self.get_rspamd(), "local.d/redis.conf.tpl")
        self.assertIn('write_servers = "127.0.0.1:6379";\n', content)
        self.assertIn('read_servers = "127.0.0.1:6379";\n', content)
        self.assertNotIn("password", content)

    def test_rspamd_configuration(self):
        self.set_external_redis(password='pa"ss')
        rspamd = self.get_rspamd()
        content = self.render(rspamd, "local.d/redis.conf.tpl")
        self.assertIn('write_servers = "redis.example.test:6380";\n', content)
        self.assertIn('read_servers = "redis.example.test:6380";\n', content)
        self.assertIn('password = "pa\\"ss";', content)
        content = self.render(rspamd, "local.d/greylist.conf.tpl")
        self.assertIn('servers = "redis.example.test:6380";\n', content)
        self.assertIn('password = "pa\\"ss";', content)

    def test_modoboa_deploy_uses_redisurl(self):
        modoboa = self.get_modoboa()
        modoboa.user = "modoboa"
        modoboa.home_dir = self.workdir
        modoboa.venv_path = os.path.join(self.workdir, "env")
        with patch("modoboa_installer.utils.exec_cmd") as exec_cmd:
            exec_cmd.return_value = (0, "")
            modoboa._deploy_instance()
            self.assertNotIn("--redisurl", exec_cmd.call_args[0][0])

            self.set_external_redis("secret")
            shutil.rmtree(os.path.join(self.workdir, "instance"), True)
            modoboa._deploy_instance()
            self.assertIn(
                "--redisurl 'redis://:secret@redis.example.test:6380/0'",
                exec_cmd.call_args[0][0])

    def test_redisurl_needs_recent_modoboa(self):
        from modoboa_installer import utils

        self.set_external_redis()
        modoboa = self.get_modoboa()
        for version in ["latest", "2.11.1", "2.12.0"]:
            self.config.set("modoboa", "version", version)
            modoboa._check_redisurl_support()
        self.config.set("modoboa", "version", "2.10.0")
        with self.assertRaises(utils.FatalError):
            modoboa._check_redisurl_support()
        # The installer must stop before installing anything
        with self.assertRaises(utils.FatalError):
            modoboa.pre_run()
        # The default local server works with any version
        self.config.set("redis", "host", "127.0.0.1")
        self.config.set("redis", "port", "6379")
        modoboa.pre_run()


class AutoconfigTestCase(unittest.TestCase):
    """Mail client auto-configuration is reachable over HTTPS."""

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
        self.config.set("certificate", "type", "letsencrypt")
        if not self.config.has_section("letsencrypt"):
            self.config.add_section("letsencrypt")
        self.config.set("letsencrypt", "email", "admin@example.test")
        patcher = patch("modoboa_installer.package.backend")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def render_autoconfig_vhost(self):
        from modoboa_installer import utils
        from modoboa_installer.scripts.nginx import Nginx

        nginx = Nginx(self.config, False, None)
        context = nginx.get_template_context()
        context["hostname"] = "autoconfig.example.test"
        with open(nginx.get_file_path("autoconfig.conf.tpl")) as fp:
            return utils.ConfigFileTemplate(fp.read()).substitute(context)

    def generate_cert(self, exists):
        from modoboa_installer import ssl

        backend = ssl.get_backend(self.config)
        with patch("modoboa_installer.ssl.os.path.exists",
                   return_value=exists), \
                patch("modoboa_installer.ssl.open"), \
                patch("modoboa_installer.ssl.os.chmod") as self.chmod, \
                patch("modoboa_installer.utils.printcolor"), \
                patch.object(backend, "install_certbot"):
            backend.generate_cert()

    @patch("modoboa_installer.utils.exec_cmd")
    def test_letsencrypt_autoconfig_cert(self, exec_cmd):
        exec_cmd.return_value = (0, "")
        self.generate_cert(exists=True)
        commands = [call[0][0] for call in exec_cmd.call_args_list]
        self.assertIn(
            "--cert-name autoconfig.example.test -d autoconfig.example.test "
            "-d autodiscover.example.test", commands[1])
        self.assertIn("renewal/autoconfig.example.test.conf", commands[3])
        content = self.render_autoconfig_vhost()
        self.assertIn("server_name autoconfig.example.test "
                      "autodiscover.example.test;", content)
        self.assertIn("listen 443 ssl;", content)
        self.assertIn(
            "ssl_certificate /etc/letsencrypt/live/autoconfig.example.test/"
            "fullchain.pem;", content)
        self.assertIn("autodiscover/autodiscover.xml", content)
        self.chmod.assert_called_once_with(
            "/etc/letsencrypt/renewal-hooks/deploy/reload-services.sh", 0o755)

    @patch("modoboa_installer.utils.exec_cmd")
    def test_letsencrypt_main_cert_failure(self, exec_cmd):
        exec_cmd.return_value = (1, b"DNS problem")
        with self.assertRaises(SystemExit):
            self.generate_cert(exists=False)
        self.assertEqual(exec_cmd.call_count, 1)

    @patch("modoboa_installer.utils.exec_cmd")
    def test_letsencrypt_autoconfig_cert_failure(self, exec_cmd):
        # The main certificate succeeds, not the auto-configuration one
        exec_cmd.side_effect = lambda cmd, **kwargs: (
            (1, "") if "--cert-name autoconfig." in cmd else (0, ""))
        self.generate_cert(exists=False)
        commands = [call[0][0] for call in exec_cmd.call_args_list]
        self.assertEqual(len(commands), 3)
        self.assertNotIn("renewal/autoconfig.example.test.conf", commands[2])
        self.assertFalse(
            self.config.has_option("general", "autoconfig_tls_cert_file"))
        self.assertIn(
            "ssl_certificate /etc/letsencrypt/live/mail.example.test/"
            "fullchain.pem;", self.render_autoconfig_vhost())

    def test_allowed_hosts(self):
        from modoboa_installer.scripts.modoboa import Modoboa

        settings_dir = os.path.join(self.workdir, "instance")
        os.mkdir(settings_dir)
        settings_file = os.path.join(settings_dir, "settings.py")
        with open(settings_file, "w") as fp:
            fp.write("ALLOWED_HOSTS = [\n    'mail.example.test',\n]\n")
        Modoboa(self.config, False, None)._allow_autoconfig_hosts(self.workdir)
        with open(settings_file) as fp:
            self.assertEqual(
                fp.read(),
                "ALLOWED_HOSTS = [\n"
                "    'mail.example.test',\n"
                "    'autoconfig.example.test',\n"
                "    'autodiscover.example.test',\n"
                "]\n")


class ValidateBackupPathTestCase(unittest.TestCase):
    """Test backup directory validation."""

    def setUp(self):
        """Create temp dir."""
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        """Delete temp dir."""
        shutil.rmtree(self.workdir)

    @patch("modoboa_installer.utils.mkdir_safe")
    def test_purge_no_mail_backup(self, mkdir_safe):
        """Reusing a --no-mail backup directory must not crash."""
        Path(self.workdir, "installer.cfg").touch()
        os.mkdir(os.path.join(self.workdir, "custom"))
        os.mkdir(os.path.join(self.workdir, "databases"))

        result = utils.validate_backup_path(self.workdir, True)

        self.assertEqual(result, self.workdir)
        self.assertEqual(os.listdir(self.workdir), [])


class DataSafetyTestCase(unittest.TestCase):
    """Backup, restore and upgrade must neither lose data nor hide failures."""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.cfgfile = os.path.join(self.workdir, "installer.cfg")
        sys.stdout = StringIO()
        run.main([
            "--skip-checks",
            "--stop-after-configfile-check",
            "--configfile", self.cfgfile,
            "example.test"])
        self.config = configparser.ConfigParser()
        self.config.read(self.cfgfile)
        self.config.set("general", "domain", "example.test")
        self.config.set("dovecot", "domain", "example.test")
        self.config.set("modoboa", "version", "latest")
        patcher = patch("modoboa_installer.package.backend")
        self.package_backend = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def mkdir(self, *paths):
        path = os.path.join(self.workdir, *paths)
        os.makedirs(path, exist_ok=True)
        return path

    def write(self, path, content="content"):
        with open(path, "w") as fp:
            fp.write(content)

    def get_modoboa(self, upgrade=False, archive_path=None):
        from modoboa_installer.scripts.modoboa import Modoboa

        modoboa = Modoboa(self.config, upgrade, archive_path)
        modoboa.user = "modoboa"
        modoboa.home_dir = self.workdir
        return modoboa

    def test_antispam_apps_are_backed_up(self):
        args = run.parser_setup([
            "--silent-backup",
            "--backup-path", self.mkdir("backup"),
            "--configfile", self.cfgfile,
            "example.test"])
        with patch("modoboa_installer.scripts.backup") as backup, \
                patch("os.chown"):
            run.backup_system(self.config, args, ["amavis", "opendkim"])
        apps = [call[0][0] for call in backup.call_args_list]
        self.assertEqual(apps, run.PRIMARY_APPS + ["amavis", "opendkim"])

    def test_no_mail_backup_still_skips_dovecot_only(self):
        args = run.parser_setup([
            "--silent-backup", "--no-mail",
            "--backup-path", self.mkdir("backup"),
            "--configfile", self.cfgfile,
            "example.test"])
        with patch("modoboa_installer.scripts.backup") as backup, \
                patch("os.chown"):
            run.backup_system(self.config, args, ["rspamd"])
        apps = [call[0][0] for call in backup.call_args_list]
        self.assertNotIn("dovecot", apps)
        self.assertIn("rspamd", apps)

    def test_rspamd_backup_and_restore(self):
        from modoboa_installer.scripts.rspamd import Rspamd

        source = self.mkdir("source")
        self.write(os.path.join(self.mkdir("source", "local.d"), "custom.conf"))
        self.write(os.path.join(self.mkdir("source", "dkim"), "example.pem"))
        self.mkdir("source", "dkim", "subdir")
        self.config.set("rspamd", "dkim_keys_storage_dir",
                        os.path.join(source, "dkim"))
        archive = self.mkdir("archive")
        with patch.object(Rspamd, "config_dir", source):
            Rspamd(self.config, False, None).custom_backup(
                os.path.join(archive, "custom"))

        target = self.mkdir("target")
        self.mkdir("target", "local.d")
        dkim_dir = self.mkdir("target", "dkim")
        self.config.set("rspamd", "dkim_keys_storage_dir", dkim_dir)
        with patch.object(Rspamd, "config_dir", target), \
                patch("modoboa_installer.utils.exec_cmd") as exec_cmd:
            Rspamd(self.config, False, archive).restore()
        self.assertTrue(os.path.isfile(
            os.path.join(target, "local.d", "custom.conf")))
        self.assertTrue(os.path.isfile(os.path.join(dkim_dir, "example.pem")))
        self.assertTrue(os.path.isdir(os.path.join(dkim_dir, "subdir")))
        self.assertIn("chown -R _rspamd:_rspamd", exec_cmd.call_args[0][0])

    def test_rspamd_restore_without_custom_files(self):
        """A backup made by a previous version has none of these files."""
        from modoboa_installer.scripts.rspamd import Rspamd

        Rspamd(self.config, False, self.mkdir("archive")).restore()

    def test_restore_keeps_settings(self):
        modoboa = self.get_modoboa(archive_path="/backup")
        with patch("modoboa_installer.scripts.modoboa.pwd.getpwnam"), \
                patch("modoboa_installer.utils.mkdir_safe") as mkdir_safe, \
                patch.object(modoboa.backend, "_exec_query") as exec_query:
            modoboa.apply_settings()
            exec_query.assert_not_called()
            self.assertEqual(mkdir_safe.call_count, 3)
            modoboa.archive_path = None
            modoboa.apply_settings()
            exec_query.assert_called_once()

    def test_failed_database_dump(self):
        from modoboa_installer import database, utils

        backend = database.get_backend(self.config)
        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(1, b"connection refused")), \
                patch.object(backend, "_setup_pgpass"):
            with self.assertRaises(utils.FatalError) as ctx:
                backend.dump_database("modoboa", "modoboa", "pwd", "/dump.sql")
        self.assertIn("connection refused", str(ctx.exception))

    def test_failed_pip_install(self):
        from modoboa_installer import python, utils

        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(1, b"no network")):
            with self.assertRaises(utils.FatalError):
                python.install_packages(["modoboa"], "/venv")

    def test_postgres_create_database(self):
        from modoboa_installer import database, utils

        backend = database.get_backend(self.config)
        # grep finds the database: nothing to do
        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(0, b"")) as exec_cmd:
            backend.create_database("modoboa", "modoboa")
        self.assertEqual(exec_cmd.call_count, 1)
        # Not found, then created
        with patch("modoboa_installer.utils.exec_cmd",
                   side_effect=[(1, b""), (0, b"")]) as exec_cmd:
            backend.create_database("modoboa", "modoboa")
        self.assertIn("createdb modoboa", exec_cmd.call_args[0][0])
        # Not found, and creation fails
        with patch("modoboa_installer.utils.exec_cmd",
                   side_effect=[(1, b""), (1, b"no space left")]):
            with self.assertRaises(utils.FatalError):
                backend.create_database("modoboa", "modoboa")

    def test_failed_schema_is_fatal_on_restore_only(self):
        from modoboa_installer import utils

        modoboa = self.get_modoboa(archive_path="/backup")
        modoboa.backend = MagicMock()
        modoboa.backend.load_sql_file.return_value = (1, b"syntax error")
        with patch.object(modoboa, "get_sql_schema_from_backup",
                          return_value="/backup/modoboa.sql"):
            with self.assertRaises(utils.FatalError):
                modoboa.setup_database()

        modoboa.archive_path = None
        with patch.object(modoboa, "get_sql_schema_path",
                          return_value="/schema.sql"):
            modoboa.setup_database()
        self.assertIn("syntax error", sys.stdout.getvalue())

    def test_database_installed_once(self):
        from modoboa_installer.scripts.redis import Redis

        with patch("modoboa_installer.database.PostgreSQL.install_package") \
                as install_package:
            Redis(self.config, False, None)
        install_package.assert_not_called()

    @patch("modoboa_installer.system.restart_service")
    @patch("modoboa_installer.ssl.get_backend")
    @patch("modoboa_installer.database.get_backend")
    @patch("modoboa_installer.scripts.install", side_effect=SystemExit(1))
    def test_system_restored_after_failure(self, install, get_backend, *args):
        with self.assertRaises(SystemExit):
            run.main([
                "--skip-checks", "--force",
                "--configfile", self.cfgfile,
                "example.test"])
        get_backend.return_value.install_package.assert_called_once()
        self.package_backend.prepare_system.assert_called_once()
        self.package_backend.restore_system.assert_called_once()

    @patch("modoboa_installer.utils.user_input",
           side_effect=AssertionError("Unexpected question"))
    @patch("modoboa_installer.checks.handle")
    @patch.object(run, "backup_system")
    def test_silent_backup_asks_nothing(self, backup_system, handle, _input):
        self.config.remove_option("dovecot", "enable_sharing")
        with open(self.cfgfile, "w") as fp:
            self.config.write(fp)
        run.main([
            "--silent-backup",
            "--configfile", self.cfgfile,
            "example.test"])
        handle.assert_not_called()
        backup_system.assert_called_once()

    @patch.object(run, "backup_system")
    def test_silent_backup_without_config_file(self, backup_system):
        with self.assertRaises(SystemExit) as ctx:
            run.main([
                "--silent-backup",
                "--configfile", os.path.join(self.workdir, "missing.cfg"),
                "example.test"])
        self.assertEqual(ctx.exception.code, 1)
        backup_system.assert_not_called()

    def test_version_check_without_network(self):
        from urllib.error import URLError
        from modoboa_installer import checks

        with patch("modoboa_installer.checks.urlopen",
                   side_effect=URLError("unreachable")):
            checks.check_version()
        self.assertIn("Could not check", sys.stdout.getvalue())

    def test_failed_upgrade_keeps_instance(self):
        from modoboa_installer import utils

        self.config.set("opendkim", "enabled", "false")
        settings = os.path.join(self.mkdir("instance"), "settings.py")
        self.write(settings)
        modoboa = self.get_modoboa(upgrade=True)
        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(1, b"migration failed")):
            with self.assertRaises(utils.FatalError):
                modoboa._deploy_instance()
        self.assertTrue(os.path.isfile(settings))
        self.assertFalse(os.path.exists(
            os.path.join(self.workdir, "instance.old")))

    def test_successful_upgrade_keeps_previous_instance(self):
        self.config.set("opendkim", "enabled", "false")
        self.write(os.path.join(self.mkdir("instance"), "settings.py"))
        self.mkdir("instance.old")
        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(0, b"")):
            self.get_modoboa(upgrade=True)._deploy_instance()
        self.assertTrue(os.path.isfile(
            os.path.join(self.workdir, "instance.old", "settings.py")))

    def test_mailboxes_keep_symbolic_links(self):
        from modoboa_installer.scripts.dovecot import Dovecot

        home_dir = self.mkdir("vmail")
        mailbox = self.mkdir("vmail", "example.test", "user")
        self.write(os.path.join(self.mkdir("vmail", "example.test", "user",
                                           "sieve"), "active.sieve"))
        os.symlink("sieve/active.sieve",
                   os.path.join(mailbox, ".dovecot.sieve"))
        os.symlink("sieve/deleted.sieve", os.path.join(mailbox, ".broken"))
        self.config.set("dovecot", "home_dir", home_dir)
        archive = self.mkdir("archive")
        Dovecot(self.config, False, None).backup(archive)
        shutil.rmtree(home_dir)

        dovecot = Dovecot(self.config, False, archive)
        dovecot.mailboxes_owner = "vmail"
        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(0, b"")) as exec_cmd:
            dovecot.restore()
        self.assertTrue(os.path.islink(
            os.path.join(mailbox, ".dovecot.sieve")))
        self.assertTrue(os.path.islink(os.path.join(mailbox, ".broken")))
        self.assertIn("chown -hR vmail:vmail", exec_cmd.call_args[0][0])

    def test_restore_without_mails(self):
        """A --no-mail backup leaves existing mailboxes untouched."""
        from modoboa_installer.scripts.dovecot import Dovecot

        home_dir = self.mkdir("vmail")
        self.write(os.path.join(home_dir, "message"))
        self.config.set("dovecot", "home_dir", home_dir)
        archive = self.mkdir("archive")
        for _ in ["no mails/ directory", "empty mails/ directory"]:
            Dovecot(self.config, False, archive).restore()
            self.assertTrue(os.path.isfile(os.path.join(home_dir, "message")))
            self.assertIn("emails were not backed up", sys.stdout.getvalue())
            self.mkdir("archive", "mails")

    def test_no_mail_backup_then_restore(self):
        """Full cycle: back up without mails twice, then restore."""
        from modoboa_installer.scripts.dovecot import Dovecot

        backup_path = self.mkdir("backup")
        for _ in range(2):
            args = run.parser_setup([
                "--silent-backup", "--no-mail",
                "--backup-path", backup_path,
                "--configfile", self.cfgfile,
                "example.test"])
            with patch("modoboa_installer.scripts.backup"), patch("os.chown"):
                run.backup_system(self.config, args, [])
        self.assertFalse(os.path.exists(os.path.join(backup_path, "mails")))
        Dovecot(self.config, False, backup_path).restore()

    def test_radicale_collections_owner(self):
        from modoboa_installer.scripts.radicale import Radicale

        self.write(os.path.join(
            self.mkdir("archive", "custom", "radicale"), "calendar.ics"))
        radicale = Radicale(
            self.config, False, os.path.join(self.workdir, "archive"))
        radicale.user = "radicale"
        radicale.home_dir = self.mkdir("radicale")
        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(0, b"")) as exec_cmd:
            radicale.restore()
        self.assertIn("chown -R radicale:radicale", exec_cmd.call_args[0][0])

    def test_disabled_antispam(self):
        cfgfile = os.path.join(self.workdir, "noantispam.cfg")
        with patch("modoboa_installer.utils.user_input",
                   side_effect=["1", "0"] + [""] * 10):
            run.main([
                "--skip-checks",
                "--stop-after-configfile-check",
                "--interactive",
                "--configfile", cfgfile,
                "example.test"])
        config = configparser.ConfigParser()
        config.read(cfgfile)
        for section in ["amavis", "spamassassin", "razor", "postwhite",
                        "opendkim", "rspamd", "clamav"]:
            self.assertFalse(config.getboolean(section, "enabled"), section)

    def test_protect_file(self):
        from modoboa_installer.scripts.redis import Redis

        path = os.path.join(self.workdir, "secret.conf")
        self.write(path)
        os.chmod(path, 0o644)
        redis = Redis(self.config, False, None)
        with patch("modoboa_installer.scripts.base.shutil.chown") as chown:
            redis.protect_file(path, "amavis")
            redis.protect_file(path + ".missing", "amavis")
        chown.assert_called_once_with(path, "root", "amavis")
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o640)

    def test_dovecot_secrets(self):
        """Non-secret files included by Dovecot must stay readable."""
        from modoboa_installer.scripts.dovecot import Dovecot

        dovecot = Dovecot(self.config, False, None)
        dovecot.mailboxes_owner = "vmail"
        dovecot._version = "2.3"
        with patch.object(dovecot, "protect_file") as protect_file:
            dovecot._protect_secrets()
        self.assertEqual(
            {call[0][1] for call in protect_file.call_args_list}, {"dovecot"})
        files = [call[0][0] for call in protect_file.call_args_list]
        self.assertNotIn("/etc/dovecot/conf.d/auth-sql.conf.ext", files)
        dovecot._version = "2.4"
        with patch.object(dovecot, "protect_file") as protect_file:
            dovecot._protect_secrets()
        protect_file.assert_any_call(
            "/etc/dovecot/conf.d/auth-sql.conf.ext", "vmail")

    def test_old_files_are_private(self):
        from modoboa_installer import utils

        path = os.path.join(self.workdir, "main.cf")
        self.write(path)
        os.chmod(path, 0o644)
        utils.backup_file(path)
        old_file = next(Path(self.workdir).glob("main.cf.old.*"))
        self.assertEqual(old_file.stat().st_mode & 0o777, 0o600)


class BackupRestoreCycleTestCase(unittest.TestCase):
    """What a backup writes must be what a restore finds."""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.cfgfile = os.path.join(self.workdir, "installer.cfg")
        sys.stdout = StringIO()
        run.main([
            "--skip-checks",
            "--stop-after-configfile-check",
            "--configfile", self.cfgfile,
            "example.test"])
        self.config = configparser.ConfigParser()
        self.config.read(self.cfgfile)
        self.config.set("general", "domain", "example.test")
        self.config.set("dovecot", "domain", "example.test")
        self.config.set("dovecot", "home_dir", self.mkdir("vmail"))
        self.write(self.path("vmail", "message"))
        self.config.set("radicale", "home_dir", self.mkdir("radicale"))
        self.write(os.path.join(
            self.mkdir("radicale", "collections"), "calendar.ics"))
        self.mkdir("dkim")
        self.write(self.path("dkim", "example.pem"))
        self.config.set("opendkim", "keys_storage_dir", self.path("dkim"))
        self.config.set("rspamd", "dkim_keys_storage_dir", self.path("dkim"))
        patcher = patch("modoboa_installer.package.backend")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def path(self, *paths):
        return os.path.join(self.workdir, *paths)

    def mkdir(self, *paths):
        os.makedirs(self.path(*paths), exist_ok=True)
        return self.path(*paths)

    def write(self, path):
        with open(path, "w") as fp:
            fp.write("content")

    def use_rspamd(self):
        self.config.set("rspamd", "enabled", "true")
        for section in ["amavis", "spamassassin", "opendkim", "postwhite"]:
            self.config.set(section, "enabled", "false")

    def fake_exec_cmd(self, cmd, **kwargs):
        """Dumps are done by the shell: create their target file."""
        if cmd.startswith(("pg_dump", "mysqldump")):
            self.write(cmd.rsplit(" > ", 1)[1])
        return 0, b""

    def backup(self, antispam_apps, *options):
        path = self.mkdir("backup")
        args = run.parser_setup([
            "--silent-backup", *options,
            "--backup-path", path,
            "--configfile", self.cfgfile,
            "example.test"])
        with patch("modoboa_installer.utils.exec_cmd",
                   side_effect=self.fake_exec_cmd), \
                patch("modoboa_installer.database.PostgreSQL._setup_pgpass"), \
                patch("os.chown"):
            run.backup_system(self.config, args, antispam_apps)
        return path

    def assertBackedUp(self, *paths):
        for path in paths:
            self.assertTrue(
                os.path.isfile(self.path("backup", path)), path)

    def test_amavis(self):
        from modoboa_installer import scripts
        from modoboa_installer.scripts.amavis import Amavis
        from modoboa_installer.scripts.opendkim import Opendkim
        from modoboa_installer.scripts.spamassassin import Spamassassin

        path = self.backup(["amavis", "opendkim"])
        self.assertBackedUp(
            "installer.cfg",
            "databases/modoboa.sql",
            "databases/amavis.sql",
            "databases/spamassassin.sql",
            "custom/dkim/example.pem",
            "custom/radicale/calendar.ics",
            "mails/message",
        )
        scripts.restore_prep(path)
        for app in [Amavis, Spamassassin]:
            self.assertIsNotNone(
                app(self.config, False, path).get_sql_schema_from_backup())
        self.config.set("opendkim", "keys_storage_dir", self.mkdir("newdkim"))
        Opendkim(self.config, False, path).restore()
        self.assertTrue(os.path.isfile(self.path("newdkim", "example.pem")))

    def test_rspamd(self):
        from modoboa_installer.scripts.rspamd import Rspamd

        self.use_rspamd()
        self.write(os.path.join(self.mkdir("rspamd", "local.d"), "custom.conf"))
        with patch.object(Rspamd, "config_dir", self.path("rspamd")):
            path = self.backup(["rspamd"])
        self.assertBackedUp(
            "custom/rspamd/custom.conf", "custom/dkim/example.pem")

        self.mkdir("newrspamd", "local.d")
        self.config.set(
            "rspamd", "dkim_keys_storage_dir", self.mkdir("newdkim"))
        with patch.object(Rspamd, "config_dir", self.path("newrspamd")):
            Rspamd(self.config, False, path).restore()
        self.assertTrue(os.path.isfile(
            self.path("newrspamd", "local.d", "custom.conf")))
        self.assertTrue(os.path.isfile(self.path("newdkim", "example.pem")))

    def test_no_mail(self):
        from modoboa_installer.scripts.dovecot import Dovecot

        path = self.backup(["amavis", "opendkim"], "--no-mail")
        self.assertFalse(os.path.exists(self.path("backup", "mails")))
        Dovecot(self.config, False, path).restore()
        self.assertTrue(os.path.isfile(self.path("vmail", "message")))


class DatabaseTestCase(unittest.TestCase):
    """Secrets stay out of the process list and settings are honoured."""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        cfgfile = os.path.join(self.workdir, "installer.cfg")
        sys.stdout = StringIO()
        run.main([
            "--skip-checks",
            "--stop-after-configfile-check",
            "--configfile", cfgfile,
            "example.test"])
        self.config = configparser.ConfigParser()
        self.config.read(cfgfile)
        self.config.set("database", "port", "6543")
        self.config.set("dovecot", "domain", "example.test")
        if not self.config.has_section("mysql"):
            self.config.add_section("mysql")
        self.config.set("mysql", "user", "root")
        self.config.set("mysql", "password", "rootsecret")
        patcher = patch("modoboa_installer.package.backend")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def get_backend(self, engine):
        from modoboa_installer import database

        self.config.set("database", "engine", engine)
        return database.get_backend(self.config)

    def commands(self, exec_cmd):
        return [call[0][0] for call in exec_cmd.call_args_list]

    def stdin(self, exec_cmd):
        return [
            call[1].get("stdin_data") for call in exec_cmd.call_args_list]

    @patch("modoboa_installer.utils.exec_cmd", return_value=(1, b""))
    def test_postgres_user_password(self, exec_cmd):
        self.get_backend("postgres").create_user("modoboa", "it's secret")
        self.assertNotIn("secret", " ".join(self.commands(exec_cmd)))
        self.assertEqual(
            self.stdin(exec_cmd)[-1],
            "CREATE USER modoboa PASSWORD 'it's secret';\n")

    @patch("modoboa_installer.utils.exec_cmd", return_value=(0, b""))
    def test_mysql_passwords(self, exec_cmd):
        backend = self.get_backend("mysql")
        backend.create_user("modoboa", "usersecret")
        backend.load_sql_file("modoboa", "modoboa", "dbsecret", "/f.sql")
        backend.dump_database("modoboa", "modoboa", "dbsecret", "/d.sql")
        self.assertNotIn("secret", " ".join(self.commands(exec_cmd)))
        self.assertIn("usersecret", self.stdin(exec_cmd)[0])
        self.assertEqual(
            exec_cmd.call_args_list[0][1]["env"]["MYSQL_PWD"], "rootsecret")
        self.assertEqual(
            exec_cmd.call_args[1]["env"]["MYSQL_PWD"], "dbsecret")
        self.assertIn("-P 6543", self.commands(exec_cmd)[-1])
        # sudo would drop the environment holding the password
        self.assertNotIn("sudo_user", exec_cmd.call_args[1])

    @patch("modoboa_installer.utils.exec_cmd", return_value=(0, b""))
    def test_mysql_root_password(self, exec_cmd):
        with patch("modoboa_installer.utils.dist_info",
                   return_value=("Debian GNU/Linux", "13")), \
                patch("modoboa_installer.system.enable_and_start_service"):
            self.get_backend("mysql").install_package()
        self.assertNotIn("rootsecret", " ".join(self.commands(exec_cmd)))
        self.assertIn("rootsecret", self.stdin(exec_cmd)[0])

    @patch("modoboa_installer.utils.exec_cmd", return_value=(0, b""))
    def test_mysql_table_right(self, exec_cmd):
        self.get_backend("mysql").grant_right_on_table(
            "modoboa", "dkim", "opendkim", "select")
        queries = " ".join(self.stdin(exec_cmd))
        self.assertIn("TO 'opendkim'@'%'", queries)
        self.assertIn("TO 'opendkim'@'localhost'", queries)

    @patch("modoboa_installer.utils.exec_cmd", return_value=(0, b""))
    def test_postgres_dump(self, exec_cmd):
        backend = self.get_backend("postgres")
        with patch.object(backend, "_setup_pgpass"):
            backend.dump_database("modoboa", "modoboa", "secret", "/d.sql")
        self.assertIn("-p 6543", self.commands(exec_cmd)[0])

    def test_pgpass(self):
        backend = self.get_backend("postgres")
        backend.dbhost = "localhost"
        with patch("modoboa_installer.database.pwd.getpwnam",
                   return_value=(0, 0, 1000, 1000, 0, self.workdir, "")), \
                patch("os.chown"):
            backend._setup_pgpass("modoboa", "dbuser", "secret")
        with open(os.path.join(self.workdir, ".pgpass")) as fp:
            self.assertEqual(fp.read(), "localhost:*:modoboa:dbuser:secret\n")

    def test_exec_cmd_stdin(self):
        """Run the real command: the module-level patch hides it."""
        code, output = REAL_EXEC_CMD("cat", stdin_data="hello\n")
        self.assertEqual((code, output), (0, b"hello\n"))
        code, output = REAL_EXEC_CMD("exit 3", stdin_data="x" * 200000)
        self.assertEqual(code, 3)

    def test_dkim_view_dropped_from_modoboa_database(self):
        from modoboa_installer.scripts.modoboa import Modoboa

        self.config.set("modoboa", "version", "latest")
        self.config.set("general", "domain", "example.test")
        modoboa = Modoboa(self.config, True, None)
        modoboa.user = "modoboa"
        modoboa.home_dir = self.workdir
        with patch.object(modoboa.backend, "_exec_query") as exec_query, \
                patch.object(modoboa.backend, "load_sql_file"), \
                patch.object(modoboa.backend, "grant_right_on_table"):
            modoboa._deploy_instance()
        exec_query.assert_called_once_with(
            "DROP VIEW IF EXISTS dkim", "modoboa")

    def test_upgrade_keeps_media(self):
        from modoboa_installer.scripts.modoboa import Modoboa

        self.config.set("modoboa", "version", "latest")
        self.config.set("general", "domain", "example.test")
        self.config.set("opendkim", "enabled", "false")
        media_dir = os.path.join(self.workdir, "instance", "media", "logos")
        os.makedirs(media_dir)
        Path(media_dir, "logo.png").touch()

        def deploy(cmd, **kwargs):
            if "deploy instance" in cmd:
                os.makedirs(os.path.join(self.workdir, "instance", "media"))
            return 0, b""

        modoboa = Modoboa(self.config, True, None)
        modoboa.user = "modoboa"
        modoboa.home_dir = self.workdir
        with patch("modoboa_installer.utils.exec_cmd",
                   side_effect=deploy) as exec_cmd:
            modoboa._deploy_instance()
        self.assertTrue(os.path.isfile(os.path.join(media_dir, "logo.png")))
        self.assertIn("chown -R modoboa:modoboa", " ".join(
            call[0][0] for call in exec_cmd.call_args_list))

    def test_invalid_silent_backup_path(self):
        path = os.path.join(self.workdir, "afile")
        Path(path).touch()
        args = run.parser_setup([
            "--silent-backup", "--backup-path", path, "example.test"])
        with self.assertRaises(SystemExit) as ctx:
            run.backup_system(self.config, args, [])
        self.assertEqual(ctx.exception.code, 1)

    def test_custom_repository_written_once(self):
        from modoboa_installer import package

        backend = package.DEBPackage()
        with patch("builtins.open", mock_open()) as opener:
            for _ in range(2):
                backend.add_custom_repository(
                    "rspamd", "http://rspamd.test/", "http://rspamd.test/key",
                    "trixie")
        opener.assert_called_with("/etc/apt/sources.list.d/rspamd.list", "w")
        self.assertEqual(opener().write.call_count, 4)

    def test_dovecot_templates_are_not_copied(self):
        from modoboa_installer.scripts.dovecot import Dovecot

        dovecot = Dovecot(self.config, False, None)
        dovecot._version = "2.4"
        dovecot._sharing_enabled = False
        dovecot.mailboxes_owner = "vmail"
        with patch("modoboa_installer.utils.copy_file") as copy_file, \
                patch("modoboa_installer.system.add_user_to_group"), \
                patch.object(dovecot, "protect_file"):
            dovecot.post_run()
        copied = [call[0][0] for call in copy_file.call_args_list]
        self.assertTrue(copied)
        self.assertEqual([f for f in copied if f.endswith(".tpl")], [])


class DistributionTestCase(unittest.TestCase):
    """The supported distributions are detected from /etc/os-release."""

    @patch("modoboa_installer.utils.platform.freedesktop_os_release")
    def test_rolling_release_has_no_version(self, os_release):
        os_release.return_value = {"NAME": "Debian GNU/Linux"}
        self.assertEqual(utils.dist_info(), ("Debian GNU/Linux", ""))
        self.assertEqual(utils.dist_codename(), "")

    @patch("modoboa_installer.utils.platform.freedesktop_os_release",
           return_value={"NAME": "Debian GNU/Linux",
                         "VERSION_CODENAME": "Trixie"})
    def test_codename(self, os_release):
        self.assertEqual(utils.dist_codename(), "trixie")

    @patch("modoboa_installer.utils.platform.freedesktop_os_release",
           side_effect=OSError)
    def test_unknown_system(self, os_release):
        sys.stdout = StringIO()
        with self.assertRaises(SystemExit):
            utils.dist_info()

    @patch("modoboa_installer.utils.dist_name", return_value="fedora linux")
    def test_unsupported_distribution(self, dist_name):
        from modoboa_installer import package

        with self.assertRaises(NotImplementedError):
            package.get_backend()

    @patch("modoboa_installer.utils.dist_name",
           return_value="debian gnu/linux")
    def test_debian(self, dist_name):
        from modoboa_installer import package

        self.assertIsInstance(package.get_backend(), package.DEBPackage)


class SettingsTestCase(unittest.TestCase):
    """Options of the configuration file are honoured."""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        cfgfile = os.path.join(self.workdir, "installer.cfg")
        sys.stdout = StringIO()
        run.main([
            "--skip-checks",
            "--stop-after-configfile-check",
            "--configfile", cfgfile,
            "example.test"])
        self.config = configparser.ConfigParser()
        self.config.read(cfgfile)
        self.config.set("general", "domain", "example.test")
        self.config.set("dovecot", "domain", "example.test")
        self.config.set("modoboa", "version", "latest")
        patcher = patch("modoboa_installer.package.backend")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def get_dovecot_files(self):
        from modoboa_installer.scripts.dovecot import Dovecot

        dovecot = Dovecot(self.config, False, None)
        dovecot._version = "2.4"
        dovecot._sharing_enabled = False
        return " ".join(dovecot.get_config_files())

    def test_move_spam_to_junk(self):
        self.assertIn("spam-to-junk.sieve", self.get_dovecot_files())
        self.config.set("dovecot", "move_spam_to_junk", "false")
        files = self.get_dovecot_files()
        self.assertNotIn("spam-to-junk.sieve", files)
        # It also configures users' Sieve scripts
        self.assertIn("90-sieve.conf", files)

    def get_nginx_extra_config(self):
        from modoboa_installer.scripts.nginx import Nginx

        nginx = Nginx(self.config, False, None)
        with patch.object(nginx, "_setup_config") as setup_config:
            nginx.post_run()
        return setup_config.call_args[1]["extra_config"]

    def test_radicale_proxy(self):
        self.assertIn("/radicale/", self.get_nginx_extra_config())
        self.config.set("radicale", "enabled", "false")
        self.assertEqual(self.get_nginx_extra_config(), "")

    def test_opendkim_port(self):
        from modoboa_installer.scripts.opendkim import Opendkim

        self.config.set("opendkim", "port", "12346")
        opendkim = Opendkim(self.config, False, None)
        with patch("builtins.open", mock_open()) as opener, \
                patch("modoboa_installer.utils.mkdir"):
            opendkim.post_run()
        written = "".join(
            call[0][0] for call in opener().write.call_args_list)
        self.assertIn('SOCKET="inet:12346@localhost"', written)

    def test_version_argument(self):
        for version in ["latest", "2.11", "2.11.1"]:
            self.assertEqual(
                run.modoboa_version(version), version)
        for version in ["", "2", "2.11.1; reboot", "2.11.1rc1"]:
            with self.assertRaises(argparse.ArgumentTypeError):
                run.modoboa_version(version)

    def get_installed_packages(self, version):
        from modoboa_installer.scripts.modoboa import Modoboa

        self.config.set("modoboa", "version", version)
        self.config.set("modoboa", "install_beta", "False")
        self.config.set(
            "modoboa", "extensions", "modoboa-webmail modoboa-custom")
        modoboa = Modoboa(self.config, True, None)
        modoboa.user = "modoboa"
        with patch("modoboa_installer.python.setup_virtualenv"), \
                patch("modoboa_installer.python.install_packages") as install:
            modoboa._setup_venv()
        return install.call_args[0][0], modoboa.extensions

    def test_removed_extensions_are_not_installed(self):
        packages, extensions = self.get_installed_packages("latest")
        self.assertEqual(
            packages, ["modoboa[postgresql]", "modoboa-custom"])
        self.assertEqual(extensions, ["modoboa-custom"])
        packages, extensions = self.get_installed_packages("2.2.0")
        self.assertEqual(
            packages,
            ["modoboa[postgresql]==2.2.0", "modoboa-webmail", "modoboa-custom"])
        packages, extensions = self.get_installed_packages("2.4.0")
        self.assertEqual(
            packages, ["modoboa[postgresql]==2.4.0", "modoboa-custom"])

    def test_third_party_sources_are_pinned(self):
        from modoboa_installer.scripts import postwhite
        from modoboa_installer.scripts.postfix import Postfix

        def download(cmd, **kwargs):
            if cmd.startswith("wget"):
                Path(self.workdir, "abc123.zip").touch()
            return 0, b""

        installer = postwhite.Postwhite(self.config, False, None)
        with patch("modoboa_installer.utils.exec_cmd",
                   side_effect=download) as exec_cmd:
            installer.install_from_archive(
                "https://example.test/repo", "abc123", self.workdir)
        commands = [call[0][0] for call in exec_cmd.call_args_list]
        self.assertEqual(commands, [
            "wget https://example.test/repo/archive/abc123.zip",
            "unzip abc123.zip",
            "mv repo-abc123 repo",
        ])
        postfix = Postfix(self.config, False, None)
        with patch("modoboa_installer.utils.exec_cmd",
                   return_value=(0, b"")) as exec_cmd, \
                patch("modoboa_installer.scripts.postfix.os.path.exists",
                      return_value=False):
            postfix.check_dhe_group_file()
        self.assertNotIn("/main/", exec_cmd.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
