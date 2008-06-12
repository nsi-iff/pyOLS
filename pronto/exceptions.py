class ProntoValueError(ValueError):
    """ A wrapper around ValueError. """
    pass

class ProntoProgrammerError(AssertionError):
    """ An error which has occured due to a programming error.
        (a user, no matter how unruly, should never be able
         to cause one of these). """
    pass
