"""
test_proxy.py

Copyright 2012 Andres Riancho

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
import urllib.request, urllib.error, urllib.parse
import unittest

import websocket

from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.controllers.daemons.proxy import Proxy, ProxyHandler


class TestProxy(unittest.TestCase):

    IP_ADDRESS = '127.0.0.1'
    HTTP_URL = 'http://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l'
    HTTPS_URL = 'https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l'

    def setUp(self):
        # Start the proxy server
        create_temp_dir()

        self._proxy = Proxy(self.IP_ADDRESS, 0, ExtendedUrllib(), ProxyHandler)
        self._proxy.start()
        self._proxy.wait_for_start()
        
        port = self._proxy.get_port()

        # Build the proxy opener
        proxy_url = 'http://%s:%s' % (self.IP_ADDRESS, port)
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url,
                                              'https': proxy_url})
        self.proxy_opener = urllib.request.build_opener(proxy_handler,
                                                 urllib.request.HTTPHandler)

    @pytest.mark.deprecated
    def tearDown(self):
        # Shutdown the proxy server
        self._proxy.stop()

    @pytest.mark.deprecated
    def test_do_req_through_proxy(self):
        resp_body = self.proxy_opener.open(self.HTTP_URL).read()

        # Basic check
        self.assertGreater(len(resp_body), 0)

        # Get response using the proxy
        proxy_resp = self.proxy_opener.open(get_moth_http())
        # Get it without any proxy
        direct_resp = urllib.request.urlopen(get_moth_http())

        # Must be equal
        self.assertEqual(direct_resp.read(), proxy_resp.read())

        # Have to remove the Date header because in some cases they differ
        # because one request was sent in second X and the other in X+1, which
        # makes the test fail
        direct_resp_headers = dict(direct_resp.info())
        proxy_resp_headers = dict(proxy_resp.info())

        # Make sure that a change in the seconds returned in date doesn't break
        # the test
        del direct_resp_headers['date']
        del proxy_resp_headers['date']

        del proxy_resp_headers['content-encoding']

        self.assertEqual(direct_resp_headers, proxy_resp_headers)

    @pytest.mark.deprecated
    def test_do_ssl_req_through_proxy(self):
        resp_body = self.proxy_opener.open(self.HTTPS_URL).read()

        # Basic check
        self.assertTrue(len(resp_body) > 0)

        # Get response using the proxy
        proxy_resp = self.proxy_opener.open(get_moth_https())
        # Get it without any proxy
        direct_resp = urllib.request.urlopen(get_moth_https())

        # Must be equal
        self.assertEqual(direct_resp.read(), proxy_resp.read())

        # Have to remove the Date header because in some cases they differ
        # because one request was sent in second X and the other in X+1, which
        # makes the test fail
        direct_resp_headers = dict(direct_resp.info())
        proxy_resp_headers = dict(proxy_resp.info())
        del direct_resp_headers['date']
        del proxy_resp_headers['date']

        del proxy_resp_headers['content-encoding']

        self.assertEqual(direct_resp_headers, proxy_resp_headers)

    @pytest.mark.deprecated
    def test_proxy_req_ok(self):
        """Test if self._proxy.stop() works as expected. Note that the check
        content is the same as the previous check, but it might be that this
        check fails because of some error in start() or stop() which is run
        during setUp and tearDown."""
        # Get response using the proxy
        proxy_resp = self.proxy_opener.open(self.HTTP_URL).read()

        # Get it without the proxy
        resp = urllib.request.urlopen(get_moth_http()).read()

        self.assertEqual(resp, proxy_resp)
    
    def test_stop_no_requests(self):
        """Test what happens if I stop the proxy without sending any requests
        through it"""
        # Note that the test is completed by self._proxy.stop() in tearDown
        pass

    def test_stop_stop(self):
        """Test what happens if I stop the proxy twice."""
        # Note that the test is completed by self._proxy.stop() in tearDown
        self._proxy.stop()

    def test_error_handling(self):
        del self._proxy._master.uri_opener

        try:
            self.proxy_opener.open(self.HTTP_URL).read()
        except urllib.error.HTTPError as hte:
            # By default urllib2 handles 500 errors as exceptions, so we match
            # against this exception object
            self.assertEqual(hte.code, 500)

            body = hte.read()
            self.assertIn('Proxy error', body)
            self.assertIn('HTTP request', body)
        else:
            self.assertTrue(False)

    @pytest.mark.deprecated
    def test_proxy_gzip_encoding(self):
        """
        When we perform a request to a site which returns gzip encoded data, the
        ExtendedUrllib will automatically decode that and set it as the body,
        this test makes sure that we're also changing the header to reflect
        that change.

        Not doing this will make the browser (or any other http client) fail to
        decode the body (it will try to gunzip it and fail).
        """
        resp = self.proxy_opener.open('http://httpbin.org/gzip')

        headers = dict(resp.headers)
        content_encoding = headers.get('content-encoding')

        self.assertIn('"gzipped": true', resp.read())
        self.assertEqual('identity', content_encoding)

    @unittest.skip('Implementation pending')
    def test_websocket_secure_proxy(self):
        raise NotImplementedError

    @unittest.skip('Implementation pending')
    def test_websocket_proxy(self):
        ws = websocket.WebSocket()
        ws.connect('ws://echo.websocket.org',
                   http_proxy_host=self.IP_ADDRESS,
                   http_proxy_port=self._proxy.get_port(),
                   sslopt={'cert_reqs': ssl.CERT_NONE,
                           'check_hostname': False})

        sent_message = 'Hello, World'
        ws.send(sent_message)

        received_message = ws.recv()
        self.assertEqual(received_message, sent_message)
