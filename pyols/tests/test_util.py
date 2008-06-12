from pyols.tests import run_tests
from pyols.util import create_methods, curried, Container

from nose.tools import assert_equal, assert_raises

class Spam(object):
    """ Used for testing create_methods. """
    def __init__(self, thing):
        self.thing = thing

    @create_methods('to_%s', (str, int))
    def _to_something(self, class_):
        """Convert the thing to %(class_name)s."""
        return class_(self.thing)
 
    @create_methods('set_as_%s', (str, int))
    def _set_as_something(self, class_, new_thing):
        # Docstring left intentionally blank
        self.thing = class_(new_thing)
 
def test_create_methods():
    s = Spam(u'123')
    assert_equal(s.to_str(), '123')
    assert_equal(s.to_int(), 123)
    assert_equal(s.to_int.__doc__, "Convert the thing to int.")

    # It should still be possible to call the function directly
    assert_equal(s._to_something(int), 123)

    s.set_as_int("123")
    assert_equal(s.thing, 123)

    # It's an error to specify a method name without a %s formatter
    assert_raises(TypeError,
                  create_methods('no_%%_s_formatter', (str,)),
                  lambda: 42)



def test_curried():
    s = curried(sum, [1, 2, 3])
    assert_equal(s(), 6)

    # keyword arguments should also be handled properly
    s = curried(int, base=8)
    assert_equal(s("31"), 25)

    # This block tests that curried has __get__ set properly.
    # If it doesn't, self won't get set, and life will be sad.
    # Note that the order is important: curried should insert
    # the reference to 'self' as the first argument so everything
    # is nice and consistant.
    class CurriedTester: pass
    CurriedTester.c = curried(lambda self, ft: (self, ft), 42)
    c = CurriedTester()
    assert_equal(c.c(), (c, 42))
    # Test for a bug in handling __get__
    assert_equal(c.c(), (c, 42))

    # Obviously the particular formatting is not important,
    # but it's nice to have the repr really _look_ like a
    # function call.
    c = curried(lambda: 42, 21, a=21, b='eggs')
    assert_equal(repr(c), "<curried <lambda>(21, a=21, b='eggs')>")

def test_container():
    c = Container()
    c.foo = 1
    assert_equal(repr(c), "<Container foo=1>")


run_tests(__name__)
