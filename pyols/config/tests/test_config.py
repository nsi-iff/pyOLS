from pyols.exceptions import PyolsConfigError
from pyols.config import config, ConfigManager
from pyols.tests import run_tests

from nose.tools import assert_raises
from tempfile import NamedTemporaryFile

f = None
def setup():
    global f
    f = NamedTemporaryFile()

def teardown():
    f.close()

def test_invalid_values():
    f.write("""[web]
               wrapper=invalid\n""")
    f.flush()
    assert_raises(PyolsConfigError, config.load, f.name)

run_tests()
