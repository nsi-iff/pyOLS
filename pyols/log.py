import logging
import sys
import threading
import traceback

class LogObject(object):

    levels = ('info', 'warning', 'error', 'critical', 'exception')

    def __init__(self):
        self.logger = logging.getLogger('pyOLS')
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                          '%Y/%m/%d %H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler) 
        self.logger.setLevel(logging.DEBUG)

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

    def exception(self, e, tb=None):
        if tb is None: tb = sys.exc_info()[2]
        msg = "Exception:\n"
        msg += e.__class__.__name__ + ': ' + unicode(e) + '\n'
        msg += ''.join(traceback.format_tb(tb))
        self.error(msg)

log = LogObject()

g = globals()
for level in log.levels:
    g[level] = getattr(log, level)

if __name__=='__main__':
    info('NSI NSI NSI')
    warning('gfgfdgfgdg')
    error('dfdfdfdf')
    try:
        1/0
    except Exception, e:
        exception(e)
