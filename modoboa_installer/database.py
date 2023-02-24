"""Database related tools."""

import os
import pwd
import stat

from . import package
from . import system
from . import utils


class Database(object):

    """Common database backend."""

    default_port = None
    packages = None
    service = None

    def __init__(self, config):
        """Install if necessary."""
        self.config = config
        engine = self.config.get("database", "engine")
        self.dbhost = self.config.get("database", "host")
        self.dbport = self.config.getint(
            "database", "port", fallback=self.default_port)
        self.dbuser = config.get(engine, "user")
        self.dbpassword = config.get(engine, "password")
        if self.config.getboolean("database", "install"):
            self.install_package()

    def install_package(self):
        """Install database package if required."""
        package.backend.install_many(self.packages[package.backend.FORMAT])
        system.enable_and_start_service(self.service)


class PostgreSQL(Database):

    """Postgres."""

    default_port = 5432
    packages = {
        "deb": ["postgresql", "postgresql-server-dev-all"],
        "rpm": ["postgresql-server", "postgresql-devel"]
    }
    service = "postgresql"

    def __init__(self, config):
        super().__init__(config)
        self._pgpass_done = False

    def install_package(self):
        """Install database if required."""
        name, version = utils.dist_info()
        if "CentOS" in name:
            if version.startswith("7"):
                # Install newer version of postgres in this case
                package.backend.install(
                    "https://download.postgresql.org/pub/repos/yum/"
                    "reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm"
                )
                self.packages["rpm"] = [
                    "postgresql10-server", "postgresql10-devel"]
                self.service = "postgresql-10"
                initdb_cmd = "/usr/pgsql-10/bin/postgresql-10-setup initdb"
                cfgfile = "/var/lib/pgsql/10/data/pg_hba.conf"
            else:
                initdb_cmd = "postgresql-setup initdb"
                cfgfile = "/var/lib/pgsql/data/pg_hba.conf"
            package.backend.install_many(self.packages[package.backend.FORMAT])
            utils.exec_cmd(initdb_cmd)
            pattern = "s/^host(.+)ident$/host$1md5/"
            utils.exec_cmd("perl -pi -e '{}' {}".format(pattern, cfgfile))
        else:
            package.backend.install_many(self.packages[package.backend.FORMAT])
        system.enable_and_start_service(self.service)

    def _exec_query(self, query, dbname=None, dbuser=None, dbpassword=None):
        """Exec a postgresql query."""
        cmd = "psql"
        if dbname:
            cmd += " -d {}".format(dbname)
            if dbuser:
                self._setup_pgpass(dbname, dbuser, dbpassword)
                cmd += " -h {} -p {} -U {} -w".format(
                    self.dbhost, self.dbport, dbuser)
        query = query.replace("'", "'\"'\"'")
        cmd = "{} -c '{}' ".format(cmd, query)
        utils.exec_cmd(cmd, sudo_user=self.dbuser)

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
            "psql -lqt | cut -d \| -f 1 | grep -w {} | wc -l"
            .format(name), sudo_user=self.dbuser)
        if code:
            return
        utils.exec_cmd(
            "createdb {} -O {}".format(name, owner),
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
            fp.write("127.0.0.1:*:{}:{}:{}\n".format(
                dbname, dbname, dbpasswd))
        mode = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(target, mode)
        os.chown(target, pw[2], pw[3])
        self._pgpass_done = True

    def load_sql_file(self, dbname, dbuser, dbpassword, path):
        """Load SQL file."""
        self._setup_pgpass(dbname, dbuser, dbpassword)
        cmd = "psql -h {} -p {} -d {} -U {} -w < {}".format(
            self.dbhost, self.dbport, dbname, dbuser, path)
        utils.exec_cmd(cmd, sudo_user=self.dbuser)

    def dump_database(self, dbname, dbuser, dbpassword, path):
        """Dump DB to SQL file."""
        # Reset pgpass since we backup multiple db (different secret set)
        self._pgpass_done = False
        self._setup_pgpass(dbname, dbuser, dbpassword)
        cmd = "pg_dump -h {} -d {} -U {} -O  -w > {}".format(
            self.dbhost, dbname, dbuser, path)
        utils.exec_cmd(cmd, sudo_user=self.dbuser)


class MySQL(Database):

    """MySQL backend."""

    default_port = 3306
    packages = {
        "deb": ["mariadb-server"],
        "rpm": ["mariadb", "mariadb-devel", "mariadb-server"],
    }
    service = "mariadb"

    def _escape(self, query):
        """Replace special characters."""
        return query.replace("'", "'\"'\"'")

    def install_package(self):
        """Preseed package installation."""
        name, version = utils.dist_info()
        name = name.lower()
        if name.startswith("debian"):
            if version.startswith("8"):
                self.packages["deb"].append("libmysqlclient-dev")
            elif version.startswith("11"):
                self.packages["deb"].append("libmariadb-dev")
            else:
                self.packages["deb"].append("libmariadbclient-dev")
        elif name == "ubuntu":
            self.packages["deb"].append("libmysqlclient-dev")
        super(MySQL, self).install_package()
        queries = []
        if name.startswith("debian"):
            if version.startswith("8"):
                package.backend.preconfigure(
                    "mariadb-server", "root_password", "password",
                    self.dbpassword)
                package.backend.preconfigure(
                    "mariadb-server", "root_password_again", "password",
                    self.dbpassword)
                return
            if version.startswith("11"):
                queries = [
                    "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('{}')"
                    .format(self.dbpassword),
                    "flush privileges"
                ]
        if not queries:
            queries = [
                "UPDATE user SET plugin='' WHERE user='root'",
                "UPDATE user SET password=PASSWORD('{}') WHERE USER='root'"
                .format(self.dbpassword),
                "flush privileges"
            ]
        for query in queries:
            utils.exec_cmd(
                "mysql -D mysql -e '{}'".format(self._escape(query)))

    def _exec_query(self, query, dbname=None, dbuser=None, dbpassword=None):
        """Exec a mysql query."""
        if dbuser is None and dbpassword is None:
            dbuser = self.dbuser
            dbpassword = self.dbpassword
        cmd = "mysql -h {} -P {} -u {}".format(
            self.dbhost, self.dbport, dbuser)
        if dbpassword:
            cmd += " -p{}".format(dbpassword)
        if dbname:
            cmd += " -D {}".format(dbname)
        utils.exec_cmd(cmd + """ -e '{}' """.format(self._escape(query)))

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
        self._exec_query(
            "CREATE DATABASE IF NOT EXISTS {} "
            "DEFAULT CHARACTER SET {} "
            "DEFAULT COLLATE {}".format(
                name, self.config.get("mysql", "charset"),
                self.config.get("mysql", "collation"))
        )
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
        query = "GRANT {} ON {}.{} TO '{}'@'%'".format(
            right.upper(), dbname, table, user)
        self._exec_query(query)

    def load_sql_file(self, dbname, dbuser, dbpassword, path):
        """Load SQL file."""
        utils.exec_cmd(
            "mysql -h {} -P {} -u {} -p{} {} < {}".format(
                self.dbhost, self.dbport, dbuser, dbpassword, dbname, path)
        )

    def dump_database(self, dbname, dbuser, dbpassword, path):
        """Dump DB to SQL file."""
        cmd = "mysqldump -h {} -u {} -p{} {} > {}".format(
            self.dbhost, dbuser, dbpassword, dbname, path)
        utils.exec_cmd(cmd, sudo_user=self.dbuser)


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


def create(config, name, password):
    """Create a database and a user."""
    backend = get_backend(config)
    backend.create_user(name, password)
    backend.create_database(name)


def grant_database_access(config, name, user):
    """Grant access to a database."""
    get_backend(config).grant_access(name, user)
