#!/usr/bin/env python
"""A simple script which shows how PyOLS can be used.
If the --uri URL argument is supplied, the demonstration
will be run against URI instead of creating a new 
environment.
Example:
    $ ./demo.py
    $ ./demo.py --uri http://localhost/pyols_scgi/test
"""

from pyols import cmdline
from pyols.tests.test_env import tempdir

from sys import argv, exit
import atexit
import os
import signal
import time

def help():
    print __doc__
    exit(1)

if '-h' in argv or '--help' in argv:
    help()

uri = None
if '--uri' in argv:
    index = argv.index('--uri')
    argv.pop(index)
    try: uri = argv.pop(index)
    except IndexError: help()

###
# The following code is used to setup the environment
# and the server -- it can probably be ignored.
###

# Make sure there aren't any arguments
while len(argv) > 1:
    argv.pop(-1)

# Make sure that we're in the correct directory
if os.path.isabs(argv[0]):
    os.chdir(os.path.dirname(argv[0]))

def setup_environment():
    """ Setup a temporary environment, returning the directory name. """
    # A temporary directory which will be destoryed when the script exists
    dir = tempdir()

    # Create the environment
    argv[0] = 'pyols'
    argv.extend(['-c', dir])
    try: cmdline.run()
    except SystemExit: pass
    return dir

def fork_start_server():
    """ Fork and start the server, returning a function which can be
        used to kill off the child. """
    pid = os.fork()
    # If we are the parent, return
    if pid > 0:
        def dead_child(*args):
            print
            print "Failed to start server - "\
                  "is something else running on port 8000?"
            exit(4)
        signal.signal(signal.SIGCHLD, dead_child)
        # Give the server some time to start up
        time.sleep(2)

        def kill_child():
            os.kill(pid, signal.SIGTERM)
            os.wait()
        atexit.register(kill_child)
        return
    
    # The autoreloader causes strange problems when forking,
    # so we won't use it here.
    argv[1] = '-R'
    cmdline.run() # Start the server


if not uri:
    # We need to create the temp environment
    print "Creating temporary environment..."
    env = setup_environment()
    print "Done.  Sleeping to give the server time time to wake up..."
    cleanup = fork_start_server()
    print "Server set up!"
    uri = "http://127.1:8000/example_namespace/"

###
# If you are reading this code to learn how to use PyOLS,
# this is where you should start.
###
print
print "Client connecting to %s..." %(uri)
from xmlrpclib import ServerProxy
s = ServerProxy(uri)

print "Connected.  Importing 'doc/beer.owl'..."
s.importOWL(file('doc/beer.owl').read())

print
print "Some keywords in the ontology:"
for (id, kwd) in enumerate(s.queryKeywords()):
    if id > 10: break
    print kwd['name'] + ':'

    if not kwd['left_relations']:
        print '    ' + '<no outbound relationships>'

    for rel in kwd['left_relations']:
        print '    ' + rel['relation']['name'], rel['right']['name']

print 
print "Graphing the ontology...",
png = s.getOntologyGraph()
filename = '/tmp/pyols_demo_graph.png'
f = open(filename, 'w').write(png.data)
print "A graph of the ontology has been saved to", filename
