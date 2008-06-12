# This module is taken from DrProject, licenced under the GPL.
# Copyright (C) 2008 University of Toronto

import os
import sys
import time
import thread

SLEEP_TIME = 1

def reloader_thread(modification_callback):
    """ When this function is run from the main thread, it will force other
        threads to exit when any modules currently loaded change.

        @param modification_callback: Function taking a single argument, the
        modified file, and is called after a modification is detected."""
    mtimes = {}
    while True:
        for filename in filter(None, [getattr(module, "__file__", None)
                                      for module in sys.modules.values()]):
            while not os.path.isfile(filename): # Probably in an egg or zip file
                filename = os.path.dirname(filename)
                if not filename:
                    break
            if not filename: # Couldn't map to physical file, so just ignore
                continue

            if filename.endswith(".pyc"):
                filename = filename[:-1]

            mtime = os.stat(filename).st_mtime
            if filename not in mtimes:
                mtimes[filename] = mtime
                continue
            if mtime > mtimes[filename]:
                modification_callback(filename)
                sys.exit(3)
        time.sleep(SLEEP_TIME)

def restart_with_reloader():
    while True:
        args = [sys.executable] + sys.argv
        if sys.platform == "win32":
            args = ['"%s"' % arg for arg in args]
        new_environ = os.environ.copy()
        new_environ["RUN_MAIN"] = 'true'

        # This call reinvokes ourself and goes into the other branch of main as
        # a new process.
        exit_code = os.spawnve(os.P_WAIT, sys.executable,
                               args, new_environ)
        if exit_code != 3:
            return exit_code

def main(main_func, modification_callback):
    """ Run mail_func and restart any time modules are changed.
    
        @param main_func: Function taking no arguments which is relaunched
        when any modules are changed """

    if os.environ.get("RUN_MAIN"):
        # Lanch the actual program as a child thread
        thread.start_new_thread(main_func, ())

        try:
            # Now wait for a file modification and quit
            reloader_thread(modification_callback)
        except KeyboardInterrupt:
            pass

    else:
        # Initial invocation just waits around restarting this executable
        try:
            sys.exit(restart_with_reloader())
        except KeyboardInterrupt:
            pass
