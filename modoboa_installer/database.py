"""Database related tools."""

import os
import pwd
import stat
from typing import Optional

from . import package
from . import system
from . import utils


class Database:
    """Common database backend."""

    default_port: Optional[int] = None
    packages: Optional[list[str]] = None
    service: Optional[str] = None

    def __init__(self, config):
        """Read settings."""
        self.config = config
        engine = self.config.get("database", "engine")
        self.dbhost = self.config.get("database", "host")
        self.dbport = self.config.getint(
            "database", "port", fallback=self.default_port)
        self.dbuser = config.get(engine, "user")
        self.dbpassword = config.get(engine, "password")

    def install_package(self):
        """Install database package if required."""
        package.backend.install_many(self.packages)
        system.enable_and_start_service(self.service)


class PostgreSQL(Database):
    """Postgres."""

    default_port = 5432
    packages = ["postgresql", "postgresql-server-dev-all"]
    service = "postgresql"

    def __init__(self, config):
        super().__init__(config)
        self._pgpass_done = False

    def _exec_query(self, query, dbname=None, dbuser=None, dbpassword=None):
        """Exec a postgresql query."""
        cmd = "psql"
        if dbname:
            cmd += " -d {}".format(dbname)
            if dbuser:
                self._setup_pgpass(dbname, dbuser, dbpassword)
                cmd += " -h {} -p {} -U {} -w".format(
                    self.dbhost, self.dbport, dbuser)
        utils.exec_cmd(cmd, sudo_user=self.dbuser, stdin_data=query + ";\n")

    def create_user(self, name, password):
        """Create a user."""
        query = "SELECT 1 FROM pg_roles WHERE rolname='{}'".format(name)
        code, output = utils.exec_cmd(
            """psql -tAc "{}" | grep -q 1""".format(query),
            sudo_user=self.dbuser)
        if not code:
            return
        query = "CREATE USER {} PASSWORD '{}'".format(name, password)
        self._exec_query(query)

    def create_database(self, name, owner):
        """Create a database."""
        code, output = utils.exec_cmd(
            "psql -lqt | cut -d \\| -f 1 | grep -qw {}"
            .format(name), sudo_user=self.dbuser)
        if not code:
            return
        utils.exec_or_fail(
            "createdb {} -O {}".format(name, owner),
            "Failed to create database {}".format(name),
            sudo_user=self.dbuser)

    def grant_access(self, dbname, user):
        """Grant access to dbname."""
        query = "GRANT ALL ON DATABASE {} TO {}".format(dbname, user)
        self._exec_query(query)

    def grant_right_on_table(self, dbname, table, user, right):
        """Grant specific right to user on table."""
        query = "GRANT {} ON {} TO {}".format(
            right.upper(), table, user)
        self._exec_query(query, dbname=dbname)

    def _setup_pgpass(self, dbname, dbuser, dbpasswd):
        """Setup .pgpass file."""
        if self._pgpass_done:
            return
        if self.dbhost not in ["localhost", "127.0.0.1"]:
            self._pgpass_done = True
            return
        pw = pwd.getpwnam(self.dbuser)
        target = os.path.join(pw[5], ".pgpass")
        with open(target, "w") as fp:
            fp.write("{}:*:{}:{}:{}\n".format(
                self.dbhost, dbname, dbuser, dbpasswd))
        mode = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(target, mode)
        os.chown(target, pw[2], pw[3])
        self._pgpass_done = True

    def load_sql_file(self, dbname, dbuser, dbpassword, path):
        """Load SQL file."""
        self._setup_pgpass(dbname, dbuser, dbpassword)
        cmd = "psql -h {} -p {} -d {} -U {} -w < {}".format(
            self.dbhost, self.dbport, dbname, dbuser, path)
        return utils.exec_cmd(cmd, sudo_user=self.dbuser)

    def dump_database(self, dbname, dbuser, dbpassword, path):
        """Dump DB to SQL file."""
        # Reset pgpass since we backup multiple db (different secret set)
        self._pgpass_done = False
        self._setup_pgpass(dbname, dbuser, dbpassword)
        cmd = "pg_dump -h {} -p {} -d {} -U {} -O  -w > {}".format(
            self.dbhost, self.dbport, dbname, dbuser, path)
        utils.exec_or_fail(
            cmd, "Failed to dump database {}".format(dbname),
            sudo_user=self.dbuser)


class MySQL(Database):
    """MySQL backend."""

    default_port = 3306
    packages = ["mariadb-server", "libmariadb-dev"]
    service = "mariadb"

    def _get_env(self, password):
        """Return the environment giving a password to mysql commands."""
        return {**os.environ, "MYSQL_PWD": password}

    def install_package(self):
        """Preseed package installation."""
        name, version = utils.dist_info()
        super().install_package()
        queries = [
            "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('{}')"
            .format(self.dbpassword),
            "flush privileges"
        ]
        if name.lower().startswith("ubuntu") and int(version[:2]) < 22:
            queries = [
                "UPDATE user SET plugin='' WHERE user='root'",
                "UPDATE user SET password=PASSWORD('{}') WHERE USER='root'"
                .format(self.dbpassword),
                "flush privileges"
            ]
        for query in queries:
            utils.exec_cmd("mysql -D mysql", stdin_data=query + ";\n")

    def _exec_query(self, query, dbname=None, dbuser=None, dbpassword=None):
        """Exec a mysql query."""
        if dbuser is None and dbpassword is None:
            dbuser = self.dbuser
            dbpassword = self.dbpassword
        cmd = "mysql -h {} -P {} -u {}".format(
            self.dbhost, self.dbport, dbuser)
        if dbname:
            cmd += " -D {}".format(dbname)
        return utils.exec_cmd(
            cmd, env=self._get_env(dbpassword), stdin_data=query + ";\n")

    def create_user(self, name, password):
        """Create a user."""
        self._exec_query(
            "CREATE USER '{}'@'%' IDENTIFIED BY '{}'".format(
                name, password))
        self._exec_query(
            "CREATE USER '{}'@'localhost' IDENTIFIED BY '{}'".format(
                name, password))

    def create_database(self, name, owner):
        """Create a database."""
        code, output = self._exec_query(
            "CREATE DATABASE IF NOT EXISTS {} "
            "DEFAULT CHARACTER SET {} "
            "DEFAULT COLLATE {}".format(
                name, self.config.get("mysql", "charset"),
                self.config.get("mysql", "collation"))
        )
        if code:
            raise utils.FatalError(
                "Failed to create database {}: {}".format(
                    name, output.decode()))
        self.grant_access(name, owner)

    def grant_access(self, dbname, user):
        """Grant access to dbname."""
        self._exec_query(
            "GRANT ALL PRIVILEGES ON {}.* to '{}'@'%'"
            .format(dbname, user))
        self._exec_query(
            "GRANT ALL PRIVILEGES ON {}.* to '{}'@'localhost'"
            .format(dbname, user))

    def grant_right_on_table(self, dbname, table, user, right):
        """Grant specific right to user on table."""
        for host in ["%", "localhost"]:
            self._exec_query("GRANT {} ON {}.{} TO '{}'@'{}'".format(
                right.upper(), dbname, table, user, host))

    def load_sql_file(self, dbname, dbuser, dbpassword, path):
        """Load SQL file."""
        return utils.exec_cmd(
            "mysql -h {} -P {} -u {} {} < {}".format(
                self.dbhost, self.dbport, dbuser, dbname, path),
            env=self._get_env(dbpassword)
        )

    def dump_database(self, dbname, dbuser, dbpassword, path):
        """Dump DB to SQL file."""
        cmd = "mysqldump -h {} -P {} -u {} {} > {}".format(
            self.dbhost, self.dbport, dbuser, dbname, path)
        utils.exec_or_fail(
            cmd, "Failed to dump database {}".format(dbname),
            env=self._get_env(dbpassword))


def get_backend(config):
    """Return appropriate backend."""
    engine = config.get("database", "engine")
    if engine == "postgres":
        backend = PostgreSQL
    elif engine == "mysql":
        backend = MySQL
    else:
        raise utils.FatalError("database engine not supported")
    return backend(config)
