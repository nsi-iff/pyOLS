from pyols.web.tests import reset_db
from pyols.web.main import RequestDispatcher

import elixir

class RPCFunctions:
    def __init__(self):
        self.called = 0

    def add(self, a, b):
        self.called += 1
        return a + b

    def hello(self, who='World'):
        self.called += 1
        return 'Hello, %s!' %(who,)

class TestRequestDispatcher:
    def setup(self):
        # f => functions
        self.f = RPCFunctions()
        # d => dispatcher
        self.d = RequestDispatcher(self.f)

    def teardown(self):
        # XXX THIS DOESN'T WORK XXX
        # Keyword().flush()
        # will result in an object in the DB, but new and dirty will be empty
        if elixir.objectstore.dirty or elixir.objectstore.new:
            reset_db()

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
