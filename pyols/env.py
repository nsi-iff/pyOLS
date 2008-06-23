from pyols.db import db
from pyols.config import config
from pyols import log

from os import path, mkdir

class EnvironmentManager:
    version = '0'

    def path(self, *p):
        """ Return a path reletive to the environment path.
            >>> e = EnvironmentManager()
            >>> e._path = "/tmp"
            >>> e.path()
            '/tmp'
            >>> e.path('version')
            '/tmp/version'
            >>> """
        return path.join(self._path, *p)
    
    def load(self, path):
        """ Load the environment in 'path'.
            An exception will be raised if there is something wrong with it
            (version is too old, it doesn't exist, etc). """
        self._path = path

        config.load(self.path('config.ini'))
        # Note: The DB path is hard-coded here for two reasons:
        #       0) I cannot think of any good reason to change it
        #       1) It would involve more code to get the environment
        #          path into the config parser.
        db.connect('sqlite:///'+self.path('pyOLS.sqlite3'))
    
    def create(self, path):
        """ Create an environment at 'path'.
            The 'path' will be created, and an error will be raised
            if it already exists.
            `load(path)` is implied by calling `create(path)`. """
        self._path = path

        def mkfile(path, data):
            f = open(self.path(path), "w")
            f.write(data)
            f.close()

        mkdir(self.path())
        mkfile('version', self.version)
        mkfile('README', 'A PyOLS environment.\n'
                         'See http://nsi.cefetcampos.br!')
        mkfile('config.ini', config.default_config())

        self.load(path)
        db.create_tables()
        log.info("Environment created at %s" %(path))

env = EnvironmentManager()

from pyols.tests import run_doctests
run_doctests()
