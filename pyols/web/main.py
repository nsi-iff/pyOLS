from pyols.db import db
from pyols.log import log
from pyols.api import OntologyTool
from pyols.model import StorageMethods
from pyols.util import to_unicode

import sys
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher, resolve_dotted_attribute
from xmlrpclib import Fault

def rpcify(instance, _seen={}):
    """ Try to convert 'instance' to a format which can be sent over RPC.
        This is acomplished by iterating over itterables and calling the
        __rpc__ method of the instances they contain, if it exists.
        There is no guarentee that the returned value can be marsheled by
        xmlrpclib, but xmlrpclib will handle those errors.
        >>> rpcify(xrange(5))
        [0, 1, 2, 3, 4]
        >>> class Spam:
        ...     def __rpc__(self):
        ...         return "Eggs!"
        ...
        >>> rpcify(Spam())
        'Eggs!'
        >>> rpcify(iter([Spam(), Spam()]))
        ['Eggs!', 'Eggs!']
        >>> rpcify('Ham?')
        'Ham?'
        >>> a = ['a', 'a']
        >>> a.append(a)
        >>> rpcify(a)
        ['a', 'a', ['a', 'a', 'recursion limit']]
        >>> """

    # This controls the amount of recursion we will allow.
    # Two seems like a good default, but it would be nice
    # to eliminate the need for this in the future -- possibly
    # by using a client-side library and sending mutually recursive
    # objects as just the primary keys, which can then be turned
    # into real objects later.
    # For example:
    # class Foo(Entity):
    #    has_field(id, Integer, primary_key=True)
    #    has_many('bar', of_kind='Bar')
    # class Bar(Entity):
    #    has_field(id, Integer, primary_key=True)
    #    has_many('foo', of_kind='Foo')
    # f = Foo(); b = Bar()
    # f.bar[b]; b.foo[f]
    # rpcify(f) ==> {'id': 1,
    #                'bar': [{'id': 2,
    #                         'foo': [{'id': 1}]}]}
    seen = _seen.get(id(instance), 0)
    if seen >= 2:
        return 'recursion limit'
    if isinstance(instance, (list, tuple, dict, StorageMethods)):
        # It is only possible for some kinds of objects to
        # recurse -- so only keep track of those ones.
        _seen[id(instance)] = seen + 1

    # Note that this is implemented here instead of in the xmlrpclib layer
    # because xmlrpclib does not make it easy to add this sort of thing.
    if hasattr(instance, '__iter__'):
        if isinstance(instance, dict):
            return dict([(key, rpcify(val, _seen.copy()))
                         for key, val in instance.items()])
        return [rpcify(item, _seen.copy()) for item in instance]

    f = getattr(instance, '__rpc__', None)
    return f and rpcify(f(), _seen.copy()) or instance


class RequestDispatcher(SimpleXMLRPCDispatcher):
    """ This is the class will be instantiated on each request.
        The first argument will be the path being requested.
        The _dispatch method will then be called with the function name
        and arguments list.
        >>> class TestDispatcher(RequestDispatcher):
        ...     instance_class = ExampleRPCFunctions
        ...
        >>> d = TestDispatcher("/foo/")
        >>> d._dispatch('add', (40, 2))
        42
        >>> d._dispatch('path', [])
        '/foo/'
        >>> """
    instance_class = OntologyTool

    def __init__(self, path):
        path = to_unicode(path)
        SimpleXMLRPCDispatcher.__init__(self, True, 'utf-8')
        self.register_introspection_functions()
        self.register_multicall_functions()
        self.instance = self.instance_class(path)
        self.path = path

    # Ideally, the control loop will look like this:
    # start_database_transaction()
    # for function_call in function_calls:
    #     function_call()
    # finish_database_transaction()
    # Unfortunatly SimpleXMLRPCDispatcher makes that a little tricky.
    # Please forgive the small amount of duplicated coded here.
    def start_request(self, call_list):
        """ Setup the database, then pass the call list on to dispatch_many
            to handle them. """
        db.begin_txn()
        try:
            results = self.dispatch_many(call_list)
        except Fault, fault:
            db.abort_txn()
            log.warning("Fault %d: %s" %(fault.faultCode, fault.faultString))
            raise
        except Exception, e:
            db.abort_txn()
            log.exception(e)
            raise
        db.commit_txn()
        return results

    def dispatch_many(self, call_list):
        """ Dispatch many method calls.
            call_list is in the format:
            ``[{'methodName': 'add', 'params': [2, 2]}, ...]``"""
        results = []
        for call in call_list:
            method_name = call['methodName']
            params = call['params']
            # Note: Any exception here will cause every call to fail.
            #       This is by design: If one thing fails, the DB may be
            #       in an inconsistant state, so everything should fail.
            results.append([self.dispatch_one(method_name, params)])
        return results
    
    def _getFunc(self, method):
        func = self.funcs.get(method)
        if not func:
            try:
                func = resolve_dotted_attribute(
                    self.instance, method, False)
            except AttributeError:
                pass

        if not func:
            raise Fault(2, 'method "%s" is not supported' % method)

        return func

    def dispatch_one(self, method, params):
        """ Dispatches a single method call. """
        params = map(to_unicode, params)
        method = self._getFunc(method)
        result = method(*params)
        # The DB must be flushed after each call so that data from
        # one call is available to the subsequent calls.
        db.flush()
        # rpcify must be called after the flush so that persistant
        # objects which have just been created will get an id
        return rpcify(result)

    def _dispatch(self, method, params):
        """ Override SimpleXMLRPCDispatcher's _dispatch method so it will
            call OUR dispatch method. """
        res = self.start_request([{'methodName': method, 'params': params}])
        if not res:
            raise PyolsProgrammerError("_dispatch got an empty result: %s" %res)
        return res[0][0]

    def register_multicall_functions(self):
        self.funcs.update({'system.multicall' : self.start_request})

    def system_methodHelp(self, method):
        method = self._getFunc(method)
        import pydoc
        return pydoc.getdoc(method)


def get_dispatcher():
    return RequestDispatcher


# Support for the doctests
class ExampleRPCFunctions(object):
    """ A little class, used by the doctests of RequestDispatcher. """
    def __init__(self, path):
        self._path = path

    def add(self, a, b):
        return a + b

    def path(self):
        return self._path

    def hello(self, who='World'):
        return 'Hello, %s!' %(who,)

class TestDispatcher(RequestDispatcher):
    instance_class = ExampleRPCFunctions


from pyols.tests import run_doctests
run_doctests()
