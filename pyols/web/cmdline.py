#!/usr/bin/env python
from pyols.web.server_wrappers import wrappers
from pyols.web.main import get_dispatcher

import sys
from optparse import OptionParser


def run():
    parser = OptionParser()
    parser.add_option('-w', '--wrapper', action='store', type='string',
                      help='use the specified wrapper around the RPC server. '
                           'Valid wrappers: %s' \
                                   %(', '.join(wrappers.keys())))
    parser.set_defaults(wrapper='standalone') 
    (options, args) = parser.parse_args()

    ### Handle the wrapper
    if options.wrapper not in wrappers:
        print 'Error: %s is not a valid wrapper.' %(options.wrapper, )
        print 'Valid wrappers: %s' %(', '.join(wrappers.keys()))
        sys.exit(1)
    wrapper = wrappers[options.wrapper]

    w = wrapper(get_dispatcher())
    w.serve()

if __name__ == '__main__':
    run()
