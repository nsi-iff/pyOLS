#!/usr/bin/env python
from pyols.web.rpc_server import server_classes

import sys
from optparse import OptionParser

class RPCFunctions(object):
    """ A little class, used for testing. """
    def add(self, a, b):
        return a + b

    def hello(self, who='World'):
        return 'Hello, %s!' %(who,)


def run():
    parser = OptionParser()
    parser.add_option('-w', '--wrapper', action='store', type='string',
                      help='use the specified wrapper around the RPC server. '
                           'Valid wrappers: %s' \
                                   %(', '.join(server_classes.keys())))
    parser.set_defaults(wrapper='standalone') 
    (options, args) = parser.parse_args()

    ### Handle the wrapper
    if options.wrapper not in server_classes:
        print 'Error: %s is not a valid wrapper.' %(options.wrapper, )
        print 'Valid wrappers: %s' %(', '.join(server_classes.keys()))
        sys.exit(1)
    wrapper = server_classes[options.wrapper]

    w = wrapper(RPCFunctions())
    w.serve()

if __name__ == '__main__':
    run()
