"""
test_gcc_version.py

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
from nose.plugins.attrib import attr
from w3af.plugins.attack.payloads.payloads.tests.apache_payload_test_helper import ApachePayloadTestHelper
from w3af.plugins.attack.payloads.payload_handler import exec_payload
from w3af.plugins.attack.payloads.payloads.gcc_version import gcc_version

from unittest.mock import MagicMock

class test_gcc_version(ApachePayloadTestHelper):

    EXPECTED_RESULT = {'gcc_version': 'gcc-10 (Debian 10.2.1-6) 10.2.1 20210110, GNU ld (GNU Binutils for Debian)'}

    PARSE_TESTS = [
        [
            'Linux version 4.19.0-14-amd64 (debian-kernel@lists.debian.org) (gcc version 8.3.0 (Debian 8.3.0-6)) #1 SMP Debian 4.19.171-2 (2021-01-30)',
            '8.3.0 (Debian 8.3.0-6)'
        ],
        [
            'Linux version 5.10.0-13-amd64 (debian-kernel@lists.debian.org) (gcc-10 (Debian 10.2.1-6) 10.2.1 20210110, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.106-1 (2022-03-17)',
            'gcc-10 (Debian 10.2.1-6) 10.2.1 20210110, GNU ld (GNU Binutils for Debian)'
        ]
    ]

    def test_version_parse(self):
        gcc = gcc_version(MagicMock())
        for example in self.PARSE_TESTS:
            result = gcc.parse_gcc_version(example[0])
            self.assertEqual(result, example[1])

    @attr('ci_fails')
    def test_gcc_version(self):
        result = exec_payload(self.shell, 'gcc_version', use_api=True)
        self.assertEqual(self.EXPECTED_RESULT, result)