from pyols.tests import run_tests, db
from pyols.web.main import RequestDispatcher

import elixir
from nose.tools import raises, assert_equal
from xmlrpclib import Fault

class RPCFunctions:
    def __init__(self, path):
        self.called = 0
        self._path = path

    def add(self, a, b):
        self.called += 1
        return a+b

    def echo(self, what='world'):
        self.called += 1
        return what

    def path(self):
        return self._path
    
    def exception(self):
        assert True == False, "Darn, True != False"

    def get_self(self):
        return self

    def __rpc__(self):
        return iter(['one', [{'two': iter([3])}, 'four']])

class TestDispatcher(RequestDispatcher):
    instance_class = RPCFunctions

class TestRequestDispatcher:
    def setup(self):
        # d => dispatcher
        self.d = TestDispatcher("/test")

    def teardown(self):
        db.reset()

    def call(self, *calls):
        """ Make a call to the dispatch_many function, called when a
            a multicall comes in or by the _dispatch function.
            >>> self.call(('add', 3, 4), ('add', 1, 2))
            [7, 3]
            >>> """
        call_list = [{'methodName':c[0], 'params':c[1:]} for c in calls]
        return self.d.dispatch_many(call_list)

    def call_one(self, func, *args):
        """ Make a call to the _dispatch function, the default function
            called when an RPC request comes in. """
        return self.d._dispatch(func, args)

    def testSimpleRequest(self):
        r = self.call_one('add', 1, 2) 
        assert_equal(r, 3)

        r = self.call(('add', 1, 2), ('echo', 'NSI'), ('echo', )) 
        assert_equal(r, [[3], ['NSI'], ['world']])

    def testExceptionHandling(self):
        # If an exception is raised, an error should be returned and
        # no subsequent functions should be called.
        # Additionally, the DB should be rolled back.

        try: r = self.call(('add', 1, 2), ('exception', ), ('echo', ))
        except AssertionError: pass # This is expected
        else: raise Exception("An exception was expected but none was raised.")

        assert_equal(self.d.instance.called, 1)
                     

    def testPath(self):
        r = self.call_one('path')
        assert_equal(r, '/test')

    def testRPCification(self):
        # Ensure that returned instances are rpcified
        r = self.call_one('get_self')
        assert_equal(r, ['one', [{'two': [3]}, 'four']])

    @raises(Fault)
    def testUnsupportedMethod(self):
        self.call_one('unsupported')

    def testUnicodeArguments(self):
        # Arguments should be converted to unicode
        for test in ([1,2], 12.34):
            assert_equal(test, self.call_one('echo', test))

        r = self.call_one('echo', 'non-unicode')
        assert isinstance(r, unicode)


run_tests()
