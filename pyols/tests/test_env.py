from pyols.config import config
from pyols.env import EnvironmentManager
from pyols.exceptions import PyolsEnvironmentError
from pyols.log import log
from pyols.tests import run_tests, db

import atexit
import os
import random
import shutil
import tempfile
from nose.tools import assert_equal, assert_raises

tempdirs = []

@atexit.register
def _destory_temp_dirs():
    for tempdir in tempdirs:
        try: shutil.rmtree(tempdir, ignore_errors=True)
        except OSError, e: print "Error removing temp dirs:", e

def tempdir():
    # I need to write my own tempdir function because
    # the EnvironmentManager expectes that the directory
    # won't exist, while mkdtemp creates the directory.
    r = random.randint(100000, 999999)
    dir = os.path.join(tempfile.gettempdir(), 'pyols-test-%d'%(r))
    if os.path.exists(dir): dir = tempdir()
    tempdirs.append(dir)
    return dir

def teardown():
    if db.connected:
        db.reset()

class EnvWithBigVersion(EnvironmentManager):
    version = EnvironmentManager.version + 1

class EnvWithSmallVersion(EnvironmentManager):
    version = EnvironmentManager.version - 1

def test_create_env():
    dir = tempdir()

    env0 = EnvironmentManager()
    env0.create(dir, {'web_wrapper': 'cgi', 'log_type': 'file'})

    ### Test that the correct values are loaded
    env1 = EnvironmentManager()
    env1.load(dir, {})
    assert_equal(config['web_wrapper'], 'cgi')
    
    ### Test that things get logged to files properly
    log.info('testing log')
    log_data = open(env1.path('pyols.log')).read()
    assert 'testing log' in log_data

    ### Test that an error is raised on loading a bad version
    for env_class in (EnvWithSmallVersion, EnvWithBigVersion):
        env = env_class()
        assert_raises(PyolsEnvironmentError, env.load, dir, {})

run_tests()
