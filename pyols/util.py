"""Various utility functions."""
from pyols.exceptions import PyolsProgrammerError

from xmlrpclib import Binary
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
        self.instance = ()

    def __call__(self, *args, **kwargs):
        kwargs.update(self.kwargs)
        return self.func(*(self.instance + self.args + args), **kwargs)

    def __repr__(self):
        args = ", ".join([repr(a) for a in self.args])
        kwargs = ", ".join(["%s=%r"%kw for kw in self.kwargs.items()])
        args = ", ".join((args, kwargs))
        return '<curried %s(%s)>' % (self.func.__name__, args)

    def __get__(self, instance, type=None):
        self.instance = (instance, )
        return self

def class_with_args(class_, show_defaults=True):
    """ Return a tuple consiting of (class_, '(' + fields + ')'),
        where 'fields' comes from the fields returned by
        ``class_.list_fields()``.

        Useful with ``create_methods`` when ``class_`` implements
        StorageMethods. """
    required = []
    optional = []
    for field in class_.list_fields():
        if field.name == "namespace": continue
        if field.required or not show_defaults:
            required.append(field.name)
        else:
            optional.append(str(field.name) + "=" + repr(field.default))
    required = ", ".join(required + optional)
    return (class_, "(" + required + ")")

def create_methods(name, classes):
    """ Create methods named 'name%(class.__name__)s' for each class in classes.
        The arguemnt 'classes' can be a list of classes or (class, string)
        tuples.  If string is specified, it will be appended to the docstring,
        along with the function's name.
        >>> class Spam(object):
        ...     def __init__(self, thing): self.thing = thing
        ...     @create_methods('to_%s', (str, (int, "(str) --> int")))
        ...     def _to_something(self, class_):
        ...         "Convert thing to %(class_name)s."
        ...         return class_(self.thing)
        ...
        >>> s = Spam(u'123')
        >>> s.to_str()
        '123'
        >>> s.to_int()
        123
        >>> print s.to_int.__doc__
        Convert thing to int.
        to_int(str) --> int
        >>> """
    # Because of the way decorators which accept arguments work,
    # this function needs to return a function which will be called
    # with the function as an argument.
    return curried(_create_methods, name, classes)

def _create_methods(name, classes, func):
    """ A helper to create_methods. """
    # We need to jump up two levels, because the frame
    # directly above us will be the call to curried.
    class_locals = sys._getframe(2).f_locals

    for class_ in classes:
        doc = ""
        if isinstance(class_, tuple):
            (class_, doc) = class_
        new_func = curried(func, class_)
        new_name = name % (class_.__name__, )
        new_doc = (func.__doc__ or '') %{'class_name': class_.__name__}
        if doc:
            indent = new_doc.splitlines()[-1]
            indent = len(indent) - len(indent.lstrip())
            new_doc += "\n" + " "*indent + new_name + doc
        new_func.__doc__ = new_doc
        class_locals[new_name] = new_func
    return func

class Container:
    """ A simple container for stuff which doesn't quite feel
        "right" to put in a dictionary.
        >>> c = Container()
        >>> c.a = "a"; c.a
        'a'
        >>> c.b = 3; c.b
        3
        >>> c
        <Container a='a' b=3>
        >>> """
    def __init__(self):
        self._set = []

    def __setattr__(self, attr, val):
        if attr != "_set": self._set.append(attr)
        self.__dict__[attr] = val

    def __repr__(self):
        vals = " ".join(["%s=%r" %(a, getattr(self, a)) for a in self._set])
        return "<Container %s>" %(vals)

def to_unicode(s):
    """ Try really hard to convert 's' to a unicode object.
        First decoding as UTF8 is tried, then Latin1 if that fails.
        Note that decoding Latin1 will never fail, just do the wrong thing.
        If 's' is not a string-like object, it will be returned unchanged.
        >>> to_unicode('ohai')
        u'ohai'
        >>> to_unicode(u'123')
        u'123'
        >>> to_unicode(42.5)
        42.5
        >>> to_unicode('\xc3\xb1') == u'\xf1' # A UTF-8 ~n
        True
        >>> to_unicode('\xf1') == u'\xf1' # A latin1 ~n
        True
        >>> """
    if isinstance(s, unicode):
        return s
    if not isinstance(s, str):
        return s
    try:
        return s.decode('utf-8')
    except UnicodeError:
        return s.decode('latin1')

def binary(i):
    """ Flag instance 'i' as containing binary data so the RPC layer will
        give it the appropriate treatment. """
    return Binary(i)

from pyols.tests import run_doctests
run_doctests()
