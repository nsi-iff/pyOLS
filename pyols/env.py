from pyols.exceptions import PyolsNotFound, PyolsValidationError
from pyols.db import db
from pyols.config import config
from pyols.log import log

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
    
    def load(self, p, c):
        """ Load the environment from path 'p' with config options 'c'.
            An exception will be raised if there is something wrong with it
            (version is too old, it doesn't exist, etc). """
        if not path.exists(p):
            raise PyolsNotFound("The environment path '%r' does not exist. "
                                "Create it with '-c'?")
        self._path = p
        
        config.load(self.path('config.ini'))
        config.update(c)

        log.reconfigure(config, self.path('pyols.log'))

        # Note: The DB path is hard-coded here for two reasons:
        #       0) I cannot think of any good reason to change it
        #       1) It would involve more code to get the environment
        #          path into the config parser.
        db.connect('sqlite:///'+self.path('pyOLS.sqlite3'),
                   debug=config['log_level'] == 'debug')
    
    def create(self, path, c):
        """ Create an environment at 'path' with config options 'c'.
            The 'path' will be created, and an error will be raised
            if it already exists.
            `load(path)` is implied by calling `create(path)`. """
        self._path = path

        def mkfile(path, data):
            f = open(self.path(path), "w")
            f.write(data)
            f.close()

        try:
            mkdir(self.path())
        except OSError:
            raise PyolsValidationError("Cannot create a new environment: path "
                                       "'%s' already exists." %(self.path()))
        mkfile('version', self.version)
        mkfile('README', 'A PyOLS environment.\n'
                         'See http://nsi.cefetcampos.br!')
        mkfile('config.ini', config.default_config())

        self.load(path, c)

        config.write()
        db.create_tables()

        log.info("Environment created at %r" %(path))

env = EnvironmentManager()

from pyols.tests import run_doctests
run_doctests()
