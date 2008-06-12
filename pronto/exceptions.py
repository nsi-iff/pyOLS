class ProntoException(Exception):
    """ A class which all exceptions can inherit from,
        making it easy to tell where they come from. """
    pass

class ProntoValidationError(NameError, ProntoException):
    """ Used for errors caused by invalid input
        (for example, an invalid or duplicate name). """
    pass

class ProntoProgrammerError(AssertionError, ProntoException):
    """ Used for errors which are the _programmers_ fault
        (a user, no matter how unruly, should never be able
         to cause one of these). """
    pass
