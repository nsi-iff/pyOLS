#!/usr/bin/env python
from SimpleXMLRPCServer import SimpleXMLRPCServer, CGIXMLRPCRequestHandler, \
                               SimpleXMLRPCDispatcher
from scgi import scgi_server
import BaseHTTPServer

import autoreload

class RPCFunctions(object):
    def add(self, a, b):
        return a + b

    def hello(self, who='World'):
        return 'Hello, %s!' %(who,)


class ServerInterface(object):
    def __init__(self, obj, *args, **kwargs):
        """ Initialize the server with obj being an instance of an object
            who's methods will be available over RPC. """
        pass

    def serve(self):
        """ Start serving.
            In the case of SCGI and Standalone, listen for connections.
            In the case of CGI, handle the current request. """


class StandaloneServer(SimpleXMLRPCServer):
    def __init__(self, obj, port=8000):
        SimpleXMLRPCServer.__init__(self, ("localhost", port))
        self.register_instance(obj)

    def serve(self):
        self.serve_forever()


class CGIServer(CGIXMLRPCRequestHandler):
    def __init__(self, obj):
        CGIXMLRPCRequestHandler.__init__(self)
        self.register_instance(obj)

    def serve(self):
        self.handle_request() 


class SCGIHandler(scgi_server.SCGIHandler, SimpleXMLRPCDispatcher):
    # XXX: This rpc_obj isn't great, may change after testing
    rpc_obj = None

    def __init__(self, parent_fd, allow_none=False, encoding=None):
        self.env = self._input = self._output = None

        scgi_server.SCGIHandler.__init__(self, parent_fd)

        SimpleXMLRPCDispatcher.__init__(self, False, None)
        self.register_instance(self.rpc_obj)

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


def mod_callback(file):
    print "%s was modified.  Restarting." %(file, )

def run():
    s = StandaloneServer(RPCFunctions())
    s.serve()

autoreload.main(run, mod_callback)
