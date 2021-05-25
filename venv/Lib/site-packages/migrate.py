# -*- coding: utf-8 -*-
"""
    migrate
    ~~~~~~~
    A simple generic database migration tool

    :copyright: (c) 2014 Francis Asante <kofrasa@gmail.com>
    :license: MIT
"""
from __future__ import print_function

__version__ = '0.3.7'
__all__ = ['Migrate', 'MigrateException']

import os
import sys
import argparse
import glob
import string
import subprocess
import tempfile
from datetime import datetime

try:
    from ConfigParser import ConfigParser
except:
    from configparser import ConfigParser

COMMANDS = {
    'postgres': "psql -w --host {host} --port {port} --username {user} -d {database}",
    'mysql': "mysql --host {host} --port {port} --user {user} -D {database}",
    'sqlite3': "sqlite3 {database}"
}
PORTS = dict(postgres=5432, mysql=3306)


class MigrateException(Exception):
    pass


class Migrate(object):
    """A simple generic database migration helper
    """

    def __init__(self, path='./migrations', host=None, port=None, user=None, password=None, database=None,
                 rev=None, command=None, message=None, engine=None, verbose=False, debug=False,
                 skip_errors=False, **kwargs):
        # assign configuration for easy lookup
        self._migration_path = os.path.abspath(path)
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._rev = rev
        self._command = command
        self._message = message
        self._engine = engine
        self._verbose = int(verbose)
        self._debug = debug
        self._skip_errors = skip_errors

        assert os.path.exists(self._migration_path) and os.path.isdir(self._migration_path), \
            "migration folder does not exist: %s" % self._migration_path
        current_dir = os.path.abspath(os.getcwd())
        os.chdir(self._migration_path)
        # cache ordered list of the names of all revision folders
        self._revisions = list(map(str,
                                   sorted(map(int, filter(lambda x: x.isdigit(), glob.glob("*"))))))
        os.chdir(current_dir)

    def _log(self, level, msg):
        """Simple logging for the given verbosity level"""
        if self._verbose >= level:
            print(msg)

    def _cmd_create(self):
        """Create a migration in the current or new revision folder
        """
        assert self._message, "need to supply a message for the \"create\" command"
        if not self._revisions:
            self._revisions.append("1")

        # get the migration folder
        rev_folder = self._revisions[-1]
        full_rev_path = os.path.join(self._migration_path, rev_folder)
        if not os.path.exists(full_rev_path):
            os.mkdir(full_rev_path)
        else:
            count = len(glob.glob(os.path.join(full_rev_path, "*")))
            # create next revision folder if needed
            if count and self._rev and int(self._rev) == 0:
                rev_folder = str(int(rev_folder) + 1)
                full_rev_path = os.path.join(self._migration_path, rev_folder)
                os.mkdir(full_rev_path)
                self._revisions.append(rev_folder)

        # format file name
        filename = '_'.join([s.lower() for s in self._message.split(' ') if s.strip()])
        for p in string.punctuation:
            if p in filename:
                filename = filename.replace(p, '_')
        filename = "%s_%s" % (datetime.utcnow().strftime("%Y%m%d%H%M%S"), filename.replace('__', '_'))

        # create the migration files
        self._log(0, "creating files: ")
        for s in ('up', 'down'):
            file_path = os.path.join(full_rev_path, "%s.%s.sql" % (filename, s))
            with open(file_path, 'a+') as w:
                w.write('\n'.join([
                    '-- *** %s ***' % s.upper(),
                    '-- file: %s' % os.path.join(rev_folder, filename),
                    '-- comment: %s' % self._message]))
                self._log(0, file_path)

    def _cmd_up(self):
        """Upgrade to a revision"""
        revision = self._get_revision()
        if not self._rev:
            self._log(0, "upgrading current revision")
        else:
            self._log(0, "upgrading from revision %s" % revision)
        for rev in self._revisions[int(revision) - 1:]:
            sql_files = glob.glob(os.path.join(self._migration_path, rev, "*.up.sql"))
            sql_files.sort()
            self._exec(sql_files, rev)
        self._log(0, "done: upgraded revision to %s\n" % rev)

    def _cmd_down(self):
        """Downgrade to a revision"""
        revision = self._get_revision()
        if not self._rev:
            self._log(0, "downgrading current revision")
        else:
            self._log(0, "downgrading to revision %s" % revision)
        # execute from latest to oldest revision
        for rev in reversed(self._revisions[int(revision) - 1:]):
            sql_files = glob.glob(os.path.join(self._migration_path, rev, "*.down.sql"))
            sql_files.sort(reverse=True)
            self._exec(sql_files, rev)
        self._log(0, "done: downgraded revision to %s" % rev)

    def _cmd_reset(self):
        """Downgrade and re-run revisions"""
        self._cmd_down()
        self._cmd_up()

    def _get_revision(self):
        """Validate and return the revision to use for current command
        """
        assert self._revisions, "no migration revision exist"
        revision = self._rev or self._revisions[-1]
        # revision count must be less or equal since revisions are ordered
        assert revision in self._revisions, "invalid revision specified"
        return revision

    def _get_command(self, **kwargs):
        return COMMANDS[self._engine].format(
            host=self._host,
            user=self._user,
            database=self._database,
            port=self._port or PORTS.get(self._engine, None))

    def _exec(self, files, rev=0):
        cmd = self._get_command()
        func = globals()["exec_%s" % self._engine]
        assert callable(func), "no exec function found for " + self._engine
        for f in files:
            self._log(1, "applying: %s/%s" % (rev, os.path.basename(f)))
            try:
                func(cmd, f, self._password, self._debug)
            except MigrateException as e:
                if not self._skip_errors:
                    raise e

    def run(self):
        # check for availability of target command line tool
        cmd_name = self._get_command().split()[0]
        cmd_path = subprocess.check_output(["which", cmd_name]).strip()
        assert os.path.exists(cmd_path), "no %s command found on path" % cmd_name
        {
            'create': lambda: self._cmd_create(),
            'up': lambda: self._cmd_up(),
            'down': lambda: self._cmd_down(),
            'reset': lambda: self._cmd_reset()
        }.get(self._command)()


def print_debug(msg):
    print("[debug] %s" % msg)


def exec_mysql(cmd, filename, password=None, debug=False):
    if password:
        cmd = cmd + ' -p' + password
    if debug:
        print_debug("%s < %s" % (cmd, filename))
    with open(filename) as f:
        try:
            return subprocess.check_call(cmd.split(), stdin=f)
        except subprocess.CalledProcessError as e:
            raise MigrateException(str(e))

# reuse :)
exec_sqlite3 = lambda a, b, c, d: exec_mysql(a, b, None, d)


def exec_postgres(cmd, filename, password=None, debug=False):
    if debug:
        if password:
            print_debug("PGPASSWORD=%s %s -f %s" % (password, cmd, filename))
        else:
            print_debug("%s -f %s" % (cmd, filename))
        return 0
    env_password = None
    if password:
        if 'PGPASSWORD' in os.environ:
            env_password = os.environ['PGPASSWORD']
        os.environ['PGPASSWORD'] = password
    # for Postgres exit status for bad file input is 0, so we use temporary file to detect errors
    err_filename = tempfile.mktemp()
    try:
        subprocess.check_call(cmd.split() + ['-f', filename], stdout=open(os.devnull), stderr=open(err_filename, 'w'))
    finally:
        if env_password:
            os.environ['PGPASSWORD'] = env_password
        elif password:
            del os.environ['PGPASSWORD']
        with open(err_filename, 'r') as fd:
            stat = os.fstat(fd.fileno())
            if stat.st_size:
                raise MigrateException(''.join(fd.readlines()))
        os.remove(err_filename)


def main(*args):
    # allow flexibility for testing
    args = args or sys.argv[1:]

    login_name = os.getlogin()
    migration_path = os.path.join(os.getcwd(), "migrations")
    program = os.path.splitext(os.path.split(__file__)[1])[0]

    parser = argparse.ArgumentParser(
        prog=program,
        formatter_class=argparse.RawTextHelpFormatter,
        version=__version__,
        usage="""\
%(prog)s [options] <command>

A simple generic database migration tool using SQL scripts

commands:
  up        Upgrade from a revision to the latest
  down      Downgrade from the latest to a lower revision
  reset     Rollback and re-run to the current revision
  create    Create a migration. Specify "-r 0" to add a new revision
""")

    parser.add_argument(dest='command', choices=('create', 'up', 'down', 'reset'))
    parser.add_argument("-e", dest="engine", default='sqlite3', choices=('postgres', 'mysql', 'sqlite3'),
                        help="database engine (default: \"sqlite3\")")
    parser.add_argument("-r", dest="rev",
                        help="revision to use. specify \"0\" for the next revision if using the "
                             "\"create\" command. (default: last revision)")
    parser.add_argument("-m", dest="message",
                        help="message description for migrations created with the \"create\" command")
    parser.add_argument("-u", dest="user", default=login_name,
                        help="database user name (default: \"%s\")" % login_name)
    parser.add_argument("-p", dest="password", default='', help="database password.")
    parser.add_argument("--host", default="localhost", help='database server host (default: "localhost")')
    parser.add_argument("--port", help='server port (default: postgres=5432, mysql=3306)')
    parser.add_argument("-d", dest="database", default=login_name,
                        help="database name to use. specify a /path/to/file if using sqlite3. "
                             "(default: login name)")
    parser.add_argument("--path", default=migration_path,
                        help="path to the migration folder either absolute or relative to the "
                             "current directory. (default: \"./migrations\")")
    parser.add_argument("-f", dest='file', metavar='CONFIG', default=".migrate",
                        help="configuration file in \".ini\" format. "
                             "sections represent different configuration environments.\n"
                             "keys include: migration_path, user, password, host, port, "
                             "database, and engine. (default: \".migrate\")")
    parser.add_argument("--env", default='dev',
                        help="configuration environment. applies only to config file option "
                             "(default: \"dev\")")
    parser.add_argument("--debug", action='store_true', default=False,
                        help="print the commands but does not execute.")
    parser.add_argument("--skip-errors", default=False, action='store_true',
                        help="continue migration even when some scripts in a revision fail")
    parser.add_argument("--verbose", dest="verbose", action='store_true', default=False, help="show verbose output.")

    config = {}
    args = parser.parse_args(args=args)
    for name in ('engine', 'command', 'rev', 'password', 'user', 'path', 'env', 'skip_errors',
                 'host', 'port', 'database', 'file', 'message', 'verbose', 'debug'):
        config[name] = getattr(args, name)

    try:
        if 'file' in config:
            if os.path.isfile(config['file']):
                cfg = ConfigParser()
                cfg.read(config['file'])
                env = config.get('env', 'dev')
                for name in ('engine', 'user', 'password', 'migration_path',
                             'host', 'port', 'database', 'verbose'):
                    if cfg.has_option(env, name):
                        value = cfg.get(env, name)
                        if name == 'migration_path':
                            config['path'] = value
                        if value is not None:
                            config[name] = value
            elif config['file'] != '.migrate':
                raise Exception("Couldn't find configuration file: %s" % config['file'])
        Migrate(**config).run()
    except MigrateException as e:
        print(str(e), file=sys.stderr)
    except Exception as e:
        print(str(e), file=sys.stderr)
        parser.print_usage(sys.stderr)


if __name__ == '__main__':
    main()