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
        patcher.start().FORMAT = "deb"
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
        with patch("modoboa_installer.package.backend") as backend:
            backend.FORMAT = "rpm"
            self.assertEqual(redis.get_packages(), ["redis"])
            self.assertEqual(redis.get_daemon_name(), "redis")

    def test_other_scripts_do_not_install_redis(self):
        for fmt in ["deb", "rpm"]:
            with patch("modoboa_installer.package.backend") as backend:
                backend.FORMAT = fmt
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
        patcher.start().FORMAT = "deb"
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


if __name__ == "__main__":
    unittest.main()
