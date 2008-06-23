from pyols.exceptions import PyolsConfigError
from pyols.config.configobj import ConfigObj, flatten_errors
from pyols.config.validate import Validator
from pyols import log

from pkg_resources import resource_filename
from os import path

class ConfigManager(ConfigObj):
    @staticmethod
    def _default_config():
        return resource_filename('pyols', path.join('config', 'default.ini'))

    def load(self, file):
        """ Load config from 'file'.
            An error will be raised on invalid values (as defined by the
            template default.ini.  See also ConfigObj documentation at
            http://www.voidspace.org.uk/python/configobj.html """
        self.filename = file
        self.write_empty_values = True
        self.reload()

        vdt = Validator()
        res = self.validate(vdt, preserve_errors=True)
        for entry in flatten_errors(self, res):
            section_list, key, error = entry
            if key is not None:
               section_list.append(key)
            else:
                section_list.append('[missing section]')
            section_string = '.'.join(section_list)
            if error == False:
                error = 'Missing value or section.'
            raise PyolsConfigError('INI error: %s: %s'%(section_string, error))

    def write_default(self):
        """ Write the default config to the loaded file.
            (assumes that `load` has already been called). """
        vdt = Validator()
        self.validate(vdt, copy=True)
        ConfigObj.write(self)

_spec = ConfigObj(ConfigManager._default_config(), list_values=False)
config = ConfigManager(configspec=_spec)

# The __name__ check here is needed to resolve some circular dependencies
if __name__ == '__main__':
    from pyols.tests import run_doctests
    run_doctests()
