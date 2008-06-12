import sys

class curried(object):
    """ curried(func[, args[, kwargs]]) -> function

    A curried function will store the arguments passed to it and use them
    in later calls.  Additional arguments can be passed to the curried
    function on subsequent calls, and they will be appended to the
    internal list when the function is called (but will not be stored).
    >>> s = curried(sum, [1, 2, 3])
    >>> s()
    6
    >>> """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        kwargs.update(self.kwargs)
        return self.func(*(self.args + args), **kwargs)

    def __repr__(self):
        return '<curried %s() with %s %s>' % (self.func.__name__, `self.args`,
                                              `self.kwargs`)

    def __get__(self, instance, cls):
        self.args = ((instance, ) + self.args)
        return self

def create_methods(name, classes):
    """ Create methods named 'name%(class.__name__)s' for each class in classes.
        >>> class Spam(object):
        ...     def __init__(self, thing): self.thing = thing
        ...     @create_methods('to_%s', (str, int))
        ...     def _to_something(self, class_):
        ...         "Convert thing to %(class_name)s."
        ...         return class_(self.thing)
        ...
        >>> s = Spam(u'123')
        >>> s.to_str()
        '123'
        >>> s.to_int()
        123
        >>> s.to_int.__doc__
        'Convert thing to int.'
        >>> """
    # Because of the way decorators which accept arguments work,
    # this function needs to return a function which will be called
    # with the function as an argument.
    return curried(_create_methods, name, classes)

def _create_methods(name, classes, function):
    """ A helper to create_methods. """
    def _link_to_new(cls, *args, **kwargs):
        for (name, func, class_) in cls.__link_map:
            new_func = curried(func, class_)
            new_func.__doc__ = func.__doc__ %({'class_name': class_.__name__})
            setattr(cls, name, new_func)
        # Call the __new__ method of this object's super class.
        # See the suggestion at http://docs.python.org/ref/customization.html
        return super(cls.__class__, cls).__new__(cls, *args, **kwargs)

    # We need to jump up two levels, because the frame
    # directly above us will be the call to curried.
    class_locals = sys._getframe(2).f_locals

    if class_locals.get('__new__', _link_to_new) != _link_to_new:
        raise PyolsProgrammerError("create_methods cannot be used "
                                   "in a class which already has an "
                                   "__new__ method defined.")

    class_locals['__new__'] = _link_to_new
    # The link map links names to functions to actual functions,
    # which _link_to_new will wire up when it is called.
    lm = class_locals.setdefault('__link_map', [])
    for class_ in classes:
        lm.append((name %(class_.__name__, ), function, class_))
