#!/usr/bin/env python
from pyols.web.server_wrappers import wrappers
from pyols.web.main import get_dispatcher
from pyols.env import env

import sys
from optparse import OptionParser


def run():
    parser = OptionParser("Usage: %prog [options] environment")
    parser.add_option('-w', '--wrapper', action='store', type='string',
                      default='standalone', help='use the specified wrapper '
                      'around the RPC server. Valid wrappers: %s' \
                      %(', '.join(wrappers.keys())))
    parser.add_option('-c', '--create', action='store_true', default=False,
                      help='create a new pyOLS environment')
    (options, args) = parser.parse_args()

    ### Handle the environment
    if len(args) != 1:
        parser.error("incorrect number of arguments. "
                     "Did you specify an environment directory?")

    env_path = args.pop()
    if options.create:
        env.create(env_path)
    else:
        env.load(env_path)

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
