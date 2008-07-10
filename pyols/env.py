"""PyOLS environment directory functions."""
from pyols.exceptions import PyolsNotFound, PyolsValidationError,\
                             PyolsEnvironmentError
from pyols.db import db
from pyols.config import config
from pyols.log import log

from os import path, mkdir
from popen2 import popen4

def find_graphviz(tool='dot'):
    (pout, pin) = popen4("which %s" %(tool))
    pin.close()
    dot = pout.read()
    pout.close()
    if not path.isabs(dot): return None
    return path.dirname(dot)

class EnvironmentManager:
    # Increase this version each time something that will break backwards
    # compatibility changes to cause a warning at startup.
    version = 0

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

    def assert_env_version(self):
        """ Assert that the environment is the correct version. """
        ver = file(self.path('version')).read().split()[-1]
        ver = int(ver)
        if ver > self.version:
            raise PyolsEnvironmentError("The environment was created with a "
                                        "newer version of PyOLS.")
        elif ver < self.version:
            # XXX: Right now there is no code to actually upgrade an
            #      environment which is out of date.  Please write it :)
            raise PyolsEnvironmentError("The environment needs upgrading.")
    
    def load(self, p, c):
        """ Load the environment from path 'p' with config options 'c'.
            An exception will be raised if there is something wrong with it
            (version is too old, it doesn't exist, etc). """
        if not path.exists(p):
            raise PyolsNotFound("The environment path '%s' does not exist. "
                                "Create it with '-c'?" %(p))
        self._path = p

        self.assert_env_version()
        
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
        except OSError, e:
            raise PyolsValidationError("Cannot create a new environment:\n"\
                                       + str(e))
        mkfile('version', 'PyOLS environment version: %s' %self.version)
        mkfile('README', 'A PyOLS environment.\n'
                         'See http://nsi.cefetcampos.br/softwares/pyols/')
        mkfile('config.ini', config.default_config())

        gv_path = find_graphviz()
        if gv_path:
            config['graphviz_path'] = gv_path
        else:
            log.warning("Could not find graphviz binaries. Before PyOLS will "
                        "be able to generate graphs, the 'graphviz_path' "
                        "in pyols.ini will need to be set.")

        self.load(path, c)

        config.write()
        db.create_tables()

        log.info("Environment created at %r" %(path))

env = EnvironmentManager()

from pyols.tests import run_doctests
run_doctests()
