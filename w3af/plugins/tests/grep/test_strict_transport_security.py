"""
test_strict_transport_security.py

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
import pytest
import unittest

import w3af.core.data.kb.knowledge_base as kb
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.grep.strict_transport_security import strict_transport_security


class TestSTSSecurity(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        self.plugin = strict_transport_security()

    def tearDown(self):
        self.plugin.end()
        kb.kb.cleanup()

    @pytest.mark.deprecated
    def test_http_no_vuln(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)
        self.assertEqual(len(kb.kb.get('strict_transport_security',
                                        'strict_transport_security')), 0)

    @pytest.mark.deprecated
    def test_https_with_sts(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('strict-transport-security',
                            'max-age=31536000; includeSubDomains; preload')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)
        self.assertEqual(len(kb.kb.get('strict_transport_security',
                                        'strict_transport_security')), 0)

    @pytest.mark.deprecated
    def test_https_without_sts(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)

        findings = kb.kb.get('strict_transport_security',
                             'strict_transport_security')
        self.assertEqual(len(findings), 1, findings)

        info_set = findings[0]
        expected_desc = 'The remote web server sent 1 HTTPS responses which' \
                        ' do not contain the Strict-Transport-Security' \
                        ' header. The first ten URLs which did not send the' \
                        ' header are:\n - https://www.w3af.com/\n'

        self.assertEqual(info_set.get_id(), [1])
        self.assertEqual(info_set.get_desc(), expected_desc)
        self.assertEqual(info_set.get_name(),
                         'Missing Strict Transport Security header')

    @pytest.mark.deprecated
    def test_https_without_sts_group_by_domain(self):
        body = ''
        url = URL('https://www.w3af.com/1')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)

        body = ''
        url = URL('https://www.w3af.com/2')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=2)

        self.plugin.grep(request, resp)

        findings = kb.kb.get('strict_transport_security',
                             'strict_transport_security')
        self.assertEqual(len(findings), 1, findings)

        info_set = findings[0]
        expected_desc = 'The remote web server sent 2 HTTPS responses which' \
                        ' do not contain the Strict-Transport-Security' \
                        ' header. The first ten URLs which did not send the' \
                        ' header are:\n - https://www.w3af.com/1\n' \
                        ' - https://www.w3af.com/2\n'

        self.assertEqual(info_set.get_id(), [1, 2])
        self.assertEqual(info_set.get_desc(), expected_desc)
        self.assertEqual(info_set.get_name(),
                         'Missing Strict Transport Security header')
