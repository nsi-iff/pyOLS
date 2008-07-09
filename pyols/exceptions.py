class PyolsException(Exception):
    """ A class which all exceptions can inherit from,
        making it easy to tell where they come from. """
    pass

class PyolsValidationError(NameError, PyolsException):
    """ Used for errors caused by invalid input
        (for example, an invalid or duplicate name). """
    pass

class PyolsProgrammerError(AssertionError, PyolsException):
    """ Used for errors which are the _programmers_ fault
        (a user, no matter how unruly, should never be able
         to cause one of these). """
    pass

class PyolsConfigError(PyolsException):
    """ Used when something goes wrong with the config. """
    pass

class PyolsNotFound(PyolsException):
    """ Gets raised when something isn't found :) """
    pass

class PyolsEnvironmentError(PyolsException):
    """ An error which is raised on errors related to the environment. """
    pass
