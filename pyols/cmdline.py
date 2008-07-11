#!/usr/bin/env python
from pyols.web.server_wrappers import wrappers
from pyols.web.main import get_dispatcher
from pyols.env import env
from pyols.config import config

import sys
from optparse import OptionParser, Option
from os import path

class OptionsMemory(Option):
    """ An option which remembers if it has been set
        or the default was used. """
    changed = []

    def process(self, *args):
        # uuhh... See optparse.py if this doesn't make sense
        ini_option = self.get_opt_string().replace('--','').replace('-', '_')
        if ini_option != 'create':
            OptionsMemory.changed.append(ini_option)
        Option.process(self, *args)

def run():
    # Note that these options mirror options in default.ini
    parser = OptionParser("Usage: %prog [options] environment",
                          option_class=OptionsMemory)
    parser.add_option('-w', '--web-wrapper', action='store', type='string',
                      default='standalone', help='use the specified wrapper '
                      'around the RPC server. Valid wrappers: %s' \
                      %(', '.join(wrappers.keys())))
    parser.add_option('-R', '--no-reload', action='store_true', default=False,
                      help='Do not auto-reload the standalone server.')
    parser.add_option('-c', '--create', action='store_true', default=False,
                      help='create a new pyOLS environment')
    (options, args) = parser.parse_args()

    ### Handle the environment
    if len(args) != 1:
        parser.error("incorrect number of arguments. "
                     "Did you specify an environment directory?")
    env_path = args.pop()

    changed_options = dict([(option, getattr(options, option))
                            for option in OptionsMemory.changed])

    ### Create a new environment?
    if options.create:
        env.create(env_path, changed_options)
        print "The pyOLS server can now be started with `%s %s`"\
              %(sys.argv[0], env_path)
        sys.exit(0)

    env.load(env_path, changed_options)

    ### Handle the wrapper
    if config['web_wrapper'] not in wrappers:
        print 'Error: %s is not a valid wrapper.' %(config['web_wrapper'])
        print 'Valid wrappers: %s' %(', '.join(wrappers.keys()))
        sys.exit(1)
    wrapper = wrappers[config['web_wrapper']]

    w = wrapper(get_dispatcher())
    w.serve()

if __name__ == '__main__':
    run()
