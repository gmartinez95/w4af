"""
ssl_daemon.py

Copyright 2015 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import socketserver
import threading
import socket
import time
import ssl
import os

from .upper_daemon import UpperDaemon, UpperTCPHandler

HTTP_RESPONSE = b"HTTP/1.1 200 Ok\r\n"\
                b"Connection: close\r\n"\
                b"Content-Type: text/html\r\n"\
                b"Content-Length: 3\r\n\r\nabc"


class RawSSLDaemon(UpperDaemon):
    """
    Echo the data sent by the client, but upper case it first. SSL version of
    UpperDaemon.
    """
    def __init__(self, handler=UpperTCPHandler, ssl_version=ssl.PROTOCOL_TLS):
        super(RawSSLDaemon, self).__init__(handler=handler)
        self.ssl_version = ssl_version

    def run(self):
        self.server = socketserver.TCPServer(self.server_address, self.handler,
                                             bind_and_activate=False)

        key_file = os.path.join(os.path.dirname(__file__), 'unittest.key')
        cert_file = os.path.join(os.path.dirname(__file__), 'unittest.crt')

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)

        with context.wrap_socket(self.server.socket, server_side=True) as ssl_sock:
            self.server.socket = ssl_sock

            self.server.server_bind()
            self.server.server_activate()
            self.server.serve_forever()


class SSLServer(threading.Thread):

    def __init__(self, listen, port, certfile, proto=ssl.PROTOCOL_TLSv1_2,
                 http_response=HTTP_RESPONSE):
        threading.Thread.__init__(self)
        self.daemon = True
        self.name = 'SSLServer'
        
        self.listen = listen
        self.port = port
        self.cert = certfile
        self.proto = proto
        self.http_response = http_response

        self.sock = socket.socket()
        self.sock.bind((listen, port))
        self.sock.listen(5)

        self.errors = []

        self.should_stop = False

    def accept(self):
        self.sock = ssl.wrap_socket(self.sock,
                                    server_side=True,
                                    certfile=self.cert,
                                    cert_reqs=ssl.CERT_NONE,
                                    ssl_version=self.proto,
                                    do_handshake_on_connect=False,
                                    suppress_ragged_eofs=True)

        newsocket, fromaddr = self.sock.accept()

        try:
            # pylint: disable=E1101
            newsocket.do_handshake()
            # pylint: enable=E1101
        except:
            # The ssl certificate might request a connection with
            # SSL protocol v2 and that will "break" the handshake
            newsocket.close()
            # print 'SSL do_handshake() failed: "%s"' % e

        # print 'Connection from %s port %s, sending HTTP response' % fromaddr
        try:
            newsocket.send(self.http_response)
        except Exception as e:
            self.errors.append(e)
            # print 'Failed to send HTTP response to client: "%s"' % e
        finally:
            # If we don't sleep here the HTTP client might raise some exceptions
            # while reading from the socket. This second gives the HTTP client
            # time to read the HTTP response, process it, and if he wants call
            # close()
            time.sleep(1)

            # Close the connection
            # print 'Closed connection from %s port %s' % fromaddr
            newsocket.close()

    def run(self):
        self.should_stop = False
        while not self.should_stop:
            self.accept()

    def stop(self):
        self.should_stop = True
        try:
            self.sock.close()

            # Connection to force stop,
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.listen, self.port))
            s.close()
        except:
            pass

    def wait_for_start(self):
        while self.get_port() is None:
            time.sleep(0.5)

    def get_port(self):
        try:
            return self.sock.getsockname()[1]
        except:
            return None
