"""
handler.py

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
import threading
import traceback

from nocasedict import NocaseDict
from libmproxy.controller import Master
from libmproxy.protocol.http import HTTPResponse as LibMITMProxyHTTPResponse
from mitmproxy.controller import Master, handler
from mitmproxy.models import HTTPResponse as MITMProxyHTTPResponse
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.misc.encoding import smart_str, smart_unicode
from w3af.core.controllers.daemons.proxy.templates.utils import render
from w3af.core.controllers.daemons.proxy.empty_handler import EmptyHandler

class ProxyHandler(Master, EmptyHandler):
    """
    All HTTP traffic goes through the `request` method.

    More hooks are available and can be used to intercept/modify HTTP traffic,
    see mitmproxy docs and EmptyHandler for more information.

    http://mitmproxy.org/doc/
    """

    def __init__(self, options, server, uri_opener, parent_process):
        EmptyHandler.__init__(self)
        Master.__init__(self, options, server)

        self.uri_opener = uri_opener
        self.parent_process = parent_process

    @handler
    def request(self, flow):
        """
        This method handles EVERY request that was send by the browser, since
        this is just a base/example implementation we just:

            * Load the request form the flow
            * Translate the request into a w3af HTTPRequest
            * Send it to the wire using our uri_opener
            * Set the response

        :param flow: A mitmproxy flow containing the request
        """
        #
        # I'm not sure about all this... but... here it goes!
        #
        # mitmproxy will "call" this method in protocol/http.py#L204 [0].
        #
        # After calling this method, mitmproxy checks if the flow has a
        # response attribute set to something different than None, if there
        # is no response then mitmproxy will send an HTTP request to the
        # server.
        #
        # When there are multiple threads running or the network is slow,
        # and without the LazyHTTPResponse, the thread running handle_request_in_thread_wrapper
        # might take a few seconds to set flow.response. During that time
        # the mitmproxy main thread will check flow.response and since it
        # is not None another HTTP request will be sent.
        #
        # Sending two HTTP requests was bad, but the worse thing was that
        # mitmproxy left TCP connections in CLOSE_WAIT state. These connections
        # piled up and ended up breaking other things in the scanner.
        #
        # Quickly setting the response attribute in the `flow` guarantees (to
        # a certain degree) that mitmproxy will not send those HTTP requests.
        # It might still be possible to see (in some rate situations) HTTP
        # requests being sent by mitmproxy.
        #
        # Tried to fix this in a better way but the mitmproxy tool doesn't seem
        # to be prepared to handle the case.
        #
        # [0] https://github.com/mitmproxy/mitmproxy/blob/v0.18.2/mitmproxy/protocol/http.py#L204
        # [1] https://github.com/mitmproxy/mitmproxy/blob/v0.18.2/mitmproxy/protocol/http.py#L212
        #
        flow.response = LazyHTTPResponse()

        # This signals mitmproxy that the request will be handled by us
        flow.reply.take()
        flow.reply.ack()
        flow.reply.commit()

        self.parent_process.total_handled_requests += 1

        t = threading.Thread(target=self.handle_request_in_thread_wrapper,
                             args=(flow,),
                             name='ThreadProxyRequestHandler')
        t.daemon = True
        t.start()

    def handle_request_in_thread_wrapper(self, flow):
        """
        Handles one HTTP request in a thread

        :param flow: A mitmproxy flow containing the request
        :return: None. The HTTP response is set to the flow
        """
        http_request = self._to_w3af_request(flow.request)

        http_response = self.handle_request_in_thread(http_request)

        # Send the response (success|error) to the browser
        http_response = self._to_mitmproxy_response(http_response)
        flow.response.set(http_response)

    def handle_request_in_thread(self, http_request):
        """
        Receives an HTTP request, sends it to the wire, and returns an HTTP
        response.

        :param http_request: An HTTPRequest (w3af) object
        :return: An HTTPResponse (w3af) object
        """
        try:
            # Send the request to the remote web server
            http_response = self._send_http_request(http_request)
        except Exception, e:
            trace = str(traceback.format_exc())
            http_response = self._create_error_response(http_request,
                                                        None,
                                                        e,
                                                        trace=trace)

        return http_response

    def _to_w3af_request(self, mitmproxy_request):
        """
        Convert mitmproxy HTTPRequest to w3af HTTPRequest
        """
        url = '%s://%s:%s%s' % (mitmproxy_request.scheme,
                                mitmproxy_request.host,
                                mitmproxy_request.port,
                                mitmproxy_request.path)

        return HTTPRequest(URL(url),
                           data=request.content,
                           headers=list(request.headers.items()),
                           method=request.method)

    def _to_mitmproxy_response(self, w3af_response):
        """
        Convert w3af HTTPResponse to mitmproxy HTTPResponse
        """
        header_items = []
        charset = w3af_response.charset
        content_encoding = 'content-encoding'

        body = smart_str(w3af_response.body, charset, errors='ignore')

        header_items = []
        for header_name, header_value in list(response.headers.items()):
            header_name = smart_str(header_name, charset, errors='ignore')
            header_value = smart_str(header_value, charset, errors='ignore')
            header_items.append((header_name, header_value))

        headers = NocaseDict(header_items)

        # This is an important step! The ExtendedUrllib will gunzip the body
        # for us, which is great, but we need to change the content-encoding
        # for the response in order to match the decoded body and avoid the
        # HTTP client using the proxy from failing
        header_items.append((content_encoding, 'identity'))

        return MITMProxyHTTPResponse.make(
            status_code=w3af_response.get_code(),
            content=body,
            headers=header_items
        )

    def _send_http_request(self,
                           http_request,
                           grep=True,
                           cache=False,
                           debugging_id=None):
        """
        Send a w3af HTTP request to the web server using w3af's HTTP lib

        No error handling is performed, someone else should do that.

        :param http_request: The request to send
        :return: The response
        """
        http_method = getattr(self.uri_opener, http_request.get_method())
        return http_method(http_request.get_uri(),
                           data=http_request.get_data(),
                           headers=http_request.get_headers(),
                           grep=grep,
                           cache=cache,

                           debugging_id=debugging_id,

                           #
                           # This is an important one, which needs to be
                           # properly documented.
                           #
                           # What happens here is that mitmproxy receives a
                           # request from xurllib configured to send requests
                           # via a proxy, and then another xurllib with the same
                           # proxy config tries to forward the request.
                           #
                           # Since it has a proxy config it will enter a "proxy
                           # request routing loop" if use_proxy is not set to False
                           #
                           use_proxy=False)

    def _create_error_response(self, request, response, exception, trace=None):
        """

        :param request: The HTTP request which triggered the exception
        :param response: The response (if any) we were processing and triggered
                         the exception
        :param exception: The exception instance
        :return: A mitmproxy response object ready to send to the flow
        """
        context = {'exception_message': exception,
                   'http_request': request.dump(),
                   'traceback': trace.replace('\n', '<br/>\n') if trace else ''}

        for key, value in context.iteritems():
            context[key] = smart_unicode(value, errors='ignore')

        content = render('error.html', context)

        headers = Headers((
            ('Connection', 'close'),
            ('Content-type', 'text/html'),
        ))

        http_response = HTTPResponse(500,
                                     content.encode('utf-8'),
                                     headers,
                                     request.get_uri(),
                                     request.get_uri(),
                                     msg='Server error')
        return http_response


class LazyHTTPResponse(object):
    """
    An HTTP response holder that will block all calls to the object attributes
    until the real HTTP response is set. After the HTTP response is set, all
    attribute methods are forwarded to it.
    """
    def __init__(self):
        self._http_response = None
        self._set_event = threading.Event()

    def set(self, http_response):
        self._http_response = http_response
        self._set_event.set()

    def __str__(self):
        return '<LazyHTTPResponse %s>' % id(self)

    def __getattr__(self, item):
        if self._set_event is not None:
            self._set_event.wait()

        :param flow: A libmproxy flow containing the request
        """
        http_request = self._to_w3af_request(flow.request)

        try:
            # Send the request to the remote webserver
            http_response = self._send_http_request(http_request)
        except Exception as e:
            trace = str(traceback.format_exc())
            http_response = self._create_error_response(http_request, None, e,
                                                        trace=trace)

        # Send the response (success|error) to the browser
        http_response = self._to_libmproxy_response(flow.request, http_response)
        flow.reply(http_response)
