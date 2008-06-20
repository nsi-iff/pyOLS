from pyols.tests import run_tests, db
from pyols.web.main import RequestDispatcher

import elixir
from nose.tools import raises
from xmlrpclib import Fault

class RPCFunctions:
    def __init__(self):
        self.called = 0

    def add(self, a, b):
        self.called += 1
        return a + b

    def hello(self, who='World'):
        self.called += 1
        return 'Hello, %s!' %(who,)
    
    def exception(self):
        assert True == False, "Darn, True != False"

    def get_self(self):
        return self

    def __rpc__(self):
        return iter(['one', [{'two': iter([3])}, 'four']])


class TestRequestDispatcher:
    def setup(self):
        # f => functions
        self.f = RPCFunctions()
        # d => dispatcher
        self.d = RequestDispatcher(self.f)

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
        assert r == 3

        r = self.call(('add', 1, 2), ('hello', 'NSI'), ('hello', )) 
        assert r == [[3], ['Hello, NSI!'], ['Hello, World!']]

    def testExceptionHandling(self):
        # If an exception is raised, an error should be returned and
        # no subsequent functions should be called.
        # Additionally, the DB should be rolled back.

        try: r = self.call(('add', 1, 2), ('exception', ), ('hello', ))
        except AssertionError: pass # This is expected
        else: raise Exception("An exception was expected but none was raised.")

        assert self.f.called == 1, "Only one RPC function should have been "\
                                   "called before the exception was raised."

    def testRPCification(self):
        # Ensure that returned instances are rpcified
        r = self.call_one('get_self')
        assert r == ['one', [{'two': [3]}, 'four']]

    @raises(Fault)
    def testUnsupportedMethod(self):
        self.call_one('unsupported')


run_tests()
