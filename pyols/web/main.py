from pyols.db import db
from pyols.log import log

import sys
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher, resolve_dotted_attribute
from xmlrpclib import Fault

def rpcify(instance):
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
        >>> """

    # Note that this is implemented here instead of in the xmlrpclib layer
    # because xmlrpclib does not make it easy to add this sort of thing.
    if hasattr(instance, '__iter__'):
        if isinstance(instance, dict):
            return dict([(key, rpcify(val))
                         for key, val in instance.items()])
        return [rpcify(item) for item in instance]

    f = getattr(instance, '__rpc__', None)
    return f and rpcify(f()) or instance


class RequestDispatcher(SimpleXMLRPCDispatcher):
    """ A wrapper around the SimpleXMLRPCDispatcher, called by the current
        wrapper to handle a function call (or, in the case of multicall, many
        function calls). """

    def __init__(self, instance):
        # instance is the instance to be "published"
        # Init the SimpleXMLRPCDispatcher, disallowing None (False) and setting
        # the encoding to UTF-8
        SimpleXMLRPCDispatcher.__init__(self, False, 'utf-8')
        self.register_introspection_functions()
        self.register_multicall_functions()
        self.register_instance(instance)

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
                [{'methodName': 'add', 'params': [2, 2]}, ...] """
        results = []
        for call in call_list:
            method_name = call['methodName']
            params = call['params']
            # Note: Any exception here will cause every call to fail.
            #       This is by design: If one thing fails, the DB may be
            #       in an inconsistant state, so everything should fail.
            results.append([self.dispatch_one(method_name, params)])
            # The DB must be flushed after each call so that data from
            # one call is available to the subsequent calls.
            db.flush()
        return results

    def dispatch_one(self, method, params):
        """ Dispatches a single method call. """
        func = self.funcs.get(method, None)
        if not func:
            try:
                func = resolve_dotted_attribute(
                    self.instance, method,
                    self.allow_dotted_names)
            except AttributeError:
                pass

        if func is None:
            raise Fault(2, 'method "%s" is not supported' % method)

        return rpcify(func(*params))

    def _dispatch(self, method, params):
        """ Override SimpleXMLRPCDispatcher's _dispatch method so it will
            call OUR dispatch method. """
        res = self.start_request([{'methodName': method, 'params': params}])
        if not res:
            raise PyolsProgrammerError("_dispatch got an empty result: %s" %res)
        return res[0][0]

    def register_multicall_functions(self):
        self.funcs.update({'system.multicall' : self.start_request})


class RPCFunctions(object):
    """ A little class, used for testing. """
    def add(self, a, b):
        return a + b

    def hello(self, who='World'):
        return 'Hello, %s!' %(who,)

def get_dispatcher():
    return RequestDispatcher(RPCFunctions())

from pyols.tests import run_doctests
run_doctests()
