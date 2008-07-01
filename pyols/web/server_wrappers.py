#!/usr/bin/env python

from pyols.web import autoreload
from pyols.log import log

from SimpleXMLRPCServer import SimpleXMLRPCServer, CGIXMLRPCRequestHandler, \
                               SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler
import BaseHTTPServer
from os import environ
import sys

class ServerInterface(object):
    def __init__(self, dispatcher, *args, **kwargs):
        """ Initialize the server with a dispatcher class which
            will be instanciated on each request and the _dispatch
            method will be called.  See doctest on RequestDispatcher. """

    def serve(self):
        """ Start serving.
            In the case of SCGI and Standalone, listen for connections.
            In the case of CGI, handle the current request. """

class _StandaloneHandler(SimpleXMLRPCRequestHandler):
    # This class is nessicary because I can't find any other way
    # of getting the path functions are being called against
    dispatcher = None
    def _dispatch(self, method, params):
        dispatcher = self.dispatcher(self.path)
        return dispatcher._dispatch(method, params)

    def is_rpc_path_valid(self):
        # For us, all paths are valid.
        return True

class _StandaloneServer(SimpleXMLRPCServer):
    """ This is the "real" standalone server. """
    def __init__(self, port=8000):
        SimpleXMLRPCServer.__init__(self, ("0.0.0.0", port), allow_none=True,
                                    requestHandler=_StandaloneHandler)

    def serve(self):
        self.serve_forever()

class StandaloneServer(object):
    """ A "fake" standalone server, posing as a wrapper around the
        real one to make life with autoreload easier.
        All of the methods here that are prefixed with _ will be called
        by autoreload. """
    def __init__(self, dispatcher, port=8000):
        _StandaloneHandler.dispatcher = dispatcher
        self._port = port

    def serve(self):
        """ A "fake" serve function, for the benefit of autoreload. """
        # Note that, becuse of the way the autorestarter works, all the code
        # which executes up to here is run twice (except, that is, for the
        # code in this block)
        if "RUN_MAIN" in environ:
            log.info("Starting standalone server on port %s" %(self._port, ))
        autoreload.main(self._serve, self._modification_callback)

    def _serve(self):
        """ The "actual" serve function. """
        _StandaloneServer(self._port).serve()

    def _modification_callback(self, file):
        log.info("%s was modified.  Restarting." %(file, ))


class CGIServer(CGIXMLRPCRequestHandler):
    def __init__(self, dispatcher):
        CGIXMLRPCRequestHandler.__init__(self)
        self.register_instance(dispatcher("/tmp/"))
        raise Exception("This needs to be written!")

    def serve(self):
        self.handle_request() 


try:
    from scgi.scgi_server import SCGIHandler as _SCGIHandler
except ImportError:
    class _SCGIHandler:
        def __init__(*args):
            print "Error: The SCGI module, which is needed to run "
            print "       the SCGI server, was not found."
            print "Try installing it with `easy_install scgi` or "
            print "grab the source from http://quixote.python.ca/releases/"
            sys.exit(1)

class SCGIHandler(_SCGIHandler, SimpleXMLRPCDispatcher):
    # XXX: This rpc_obj isn't great, may change after testing
    rpc_dispatcher = None

    def __init__(self, parent_fd, allow_none=True, encoding=None):
        raise Exception("This needs to be tested!")
        self.env = self._input = self._output = None

        _SCGIHandler.__init__(self, parent_fd)

        SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)

    def write(self, text, nl='\r\n'):
        """ Write text + nl to the output stream. """
        self._output.write(text)
        if nl: self._output.write(nl)

    ###
    # SCGIServer methods
    ###
    def handle_connection(self, conn):
        self._output = conn.makefile("w")

        input = conn.makefile("r")
        self.env = self.read_env(input)
        # CONTENT_LENGTH is set by the SCGI server.
        # See RFC 3875, section 4.1.2
        body_size = int(self.env.get('CONTENT_LENGTH', 0))
        request_text = input.read(body_size)

        self.handle_request(request_text)

        try:
            self._output.close()
            input.close()
            conn.close()
        except IOError, err:
            # XXX: Log this properly
            print "IOError while closing connection ignored: %s" % err

    ###
    # SimpleXMLRPCDispatcher methods
    # This code is coppied from CGIXMLRPCRequestHandler, the only change
    # being `print` statements changed to `self.write`. 
    ###
    def handle_xmlrpc(self, request_text):
        """Handle a single XML-RPC request"""

        response = self._marshaled_dispatch(request_text)

        self.write('Content-Type: text/xml')
        self.write('Content-Length: %d' % len(response))
        self.write('')
        self.write(response, None)

    def handle_get(self):
        """Handle a single HTTP GET request.

        Default implementation indicates an error because
        XML-RPC uses the POST method.
        """

        code = 400
        message, explain = \
                 BaseHTTPServer.BaseHTTPRequestHandler.responses[code]

        response = BaseHTTPServer.DEFAULT_ERROR_MESSAGE % \
            {
             'code' : code,
             'message' : message,
             'explain' : explain
            }
        self.write('Status: %d %s' % (code, message))
        self.write('Content-Type: text/html')
        self.write('Content-Length: %d' % len(response))
        self.write('')
        self.write(response, None)

    def handle_request(self, request_text = None):
        """Handle a single XML-RPC request passed through a CGI post method.

        If no XML data is given then it is read from stdin. The resulting
        XML-RPC response is printed to stdout along with the correct HTTP
        headers.
        """

        if request_text is None and \
            self.env.get('REQUEST_METHOD', None) == 'GET':
            self.handle_get()
        else:
            # POST data is normally available through stdin
            if request_text is None:
                request_text = ''

            self.handle_xmlrpc(request_text)

class SCGIServer(object):
    def __init__(self, obj, port=4000):
        SCGIHandler.rpc_obj = obj
        self._server = scgi_server.SCGIServer(SCGIHandler, host="localhost",
                                              port=port, max_children=5)

    def serve(self):
        self._server.serve()

wrappers = {'scgi': SCGIServer, 'standalone': StandaloneServer, 'cgi': CGIServer}
