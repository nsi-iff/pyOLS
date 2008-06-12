from pyols.db import get_db
from pyols import log

import sys
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher, resolve_dotted_attribute
from xmlrpclib import Fault

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
        db = get_db()
        db.begin_txn()
        try:
            results = self.dispatch_many(call_list)
            db.commit_txn()
        except Fault, fault:
            db.abort_txn()
            log.warning("Fault %d: %s" %(fault.faultCode, fault.faultString))
            raise
        except Exception, e:
            db.abort_txn()
            log.exception(e)
            raise
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

        if func is not None:
            return func(*params)
        else:
            raise Fault(2, 'method "%s" is not supported' % method)

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
