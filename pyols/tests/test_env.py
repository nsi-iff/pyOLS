from pyols.env import EnvironmentManager
from pyols.tests import run_tests

import atexit
import os
import random
import shutil
import tempfile
from nose.tools import assert_equal

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

def setup():
    global env
    env = EnvironmentManager()
    env.create(tempdir())


def testCreateEnv():
    1/0

def testLoadEnv():
    1/0

run_tests()
