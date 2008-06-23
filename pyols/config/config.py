from pyols.exceptions import PyolsConfigError
from pyols.config.configobj import ConfigObj

from pkg_resources import resource_filename
from os import path

class ConfigManager(ConfigObj):
    @staticmethod
    def default_config():
        """ Return a string containing the default configuration. """
        location = resource_filename('pyols', path.join('config', 'default.ini'))
        f = open(location)
        data = f.read()
        f.close()
        return data

    def load(self, file):
        """ Load config from 'file'. """
        self.filename = file
        self.write_empty_values = True
        self.file_error = True
        self.reload()

config = ConfigManager()

# The __name__ check here is needed to resolve some circular dependencies
if __name__ == '__main__':
    from pyols.tests import run_doctests
    run_doctests()
