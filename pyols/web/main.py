from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

def RequestDispatcher(SimpleXMLRPCDispatcher):
    """ A wrapper around the SimpleXMLRPCDispatcher, called by the current
        wrapper to handle a function call (or, in the case of multicall, many
        function calls). """

    def __init__(self, instance):
        # instance is the instance to be "published"
        # Init the SimpleXMLRPCDispatcher, disabling None (False) and setting
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
    def dispatch(self, call_list):
        """ Dispatch many method calls.
            Identical to SimpleXMLRPCDispatcher.system_multicall, with the
            exception that self.dispatch_one is called for each request
            instead of self._dispatch. """
        results = []
        for call in call_list:
            method_name = call['methodName']
            params = call['params']

            try:
                # XXX A marshalling error in any response will fail the entire
                # multicall. If someone cares they should fix this.
                results.append([self.dispatch_one(method_name, params)])
            except Fault, fault:
                results.append(
                    {'faultCode' : fault.faultCode,
                     'faultString' : fault.faultString}
                    )
            except:
                results.append(
                    {'faultCode' : 1,
                     'faultString' : "%s:%s" % (sys.exc_type, sys.exc_value)}
                    )
        return results

    def dispatch_one(self, method, params):
        """ Dispatches a single method call.
            This is identical to SimpleXMLRPCDispatcher._dispatch, with the
            exception of removing the check for an _dispatch method. """
        func = None
        try:
            # check to see if a matching function has been registered
            func = self.funcs[method]
        except KeyError:
            if self.instance is not None:
                # call instance method directly
                try:
                    func = resolve_dotted_attribute(
                        self.instance,
                        method,
                        self.allow_dotted_names
                        )
                except AttributeError:
                    pass

        if func is not None:
            return func(*params)
        else:
            raise Exception('method "%s" is not supported' % method)

    def _dispatch(self, method, params):
        """ Override SimpleXMLRPCDispatcher's _dispatch method so it will
            call OUR dispatch method. """
        self.dispatch(self, [{'methodName': method, 'params': params}])

    def register_multicall_functions(self):
        self.funcs.update({'system.multicall' : self.dispatch})
