from pyols.exceptions import PyolsConfigError, PyolsProgrammerError

import logging
import sys
import threading
import traceback

class LogObject(object):
    levels = ('info', 'warning', 'error', 'exception')

    def __init__(self):
        self.logger = logging.getLogger('pyOLS')

        # We need to fake the config here so that the logger
        # can be setup before the environment is setup
        self.reconfigure({'log_type': 'stdout'})

        def mkFunc(f):
            logfunc = getattr(self.logger, f)
            def _func(msg, *a, **kw):
                thread_name = threading.currentThread().getName()
                if thread_name != 'MainThread':
                    thread_name = "<%s> " %(thread_name, )
                else:
                    thread_name = ""
                msg = '%s%s' %(thread_name, msg)
                logfunc(msg, *a, **kw)
            return _func
        for l in self.levels:
            if l == 'exception': continue
            setattr(self, l, mkFunc(l))

    def reconfigure(self, config, file_path=None):
        """ Reconfigure the logger. """
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                          '%Y/%m/%d %H:%M:%S')
        # Re-set the list of formatters
        self.logger.handlers = []
        

        ### Setup the type
        type = config.get('log_type', 'stdout')
        # The .get is nessicary here as the logger may be called before
        # the environment is loaded.
        if type in ('stderr', 'stdout'):
            handler = logging.StreamHandler(getattr(sys, type))
        elif type == 'file':
            if not file_path:
                raise PyolsProgrammerError("The logger was reconfigured and "
                                           "asked to log to a file, but no "
                                           "file_path was given!")
            handler = logging.FileHandler(file_path)
        else:
            raise PyolsConfigError('Invalid log type: %r.  Must be one of '
                                   'stdout, stderr, file.' %(type, ))
        handler.setFormatter(formatter)
        self.logger.addHandler(handler) 

        ### Setup the level
        level = config.get('log_level', 'info')
        # Debug logging is _only_ for SQL
        if level == 'debug': level = 'info'
        if level not in self.levels:
            raise PyolsConfigError('Invalid log level: %r.  Must be one of: '
                                   '%s' %(level, ", ".join(self.levels)))
        self.logger.setLevel(getattr(logging, level.upper()))

    def exception(self, e, tb=None):
        if tb is None: tb = sys.exc_info()[2]
        msg = "Exception:\n"
        msg += e.__class__.__name__ + ': ' + unicode(e) + '\n'
        msg += ''.join(traceback.format_tb(tb))
        self.error(msg)

log = LogObject()

if __name__=='__main__':
    log.info('NSI NSI NSI')
    log.warning('gfgfdgfgdg')
    log.error('dfdfdfdf')
    try:
        1/0
    except Exception, e:
        log.exception(e)
