# -*- encoding: utf-8 -*-
"""
test_multire.py

Copyright 2012 Andres Riancho

This file is part of w4af, https://w4af.net/ .

w4af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w4af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w4af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import re
import unittest

from w4af.core.data.quick_match.multi_re import MultiRE, MultiREUnicode
from w4af.core.data.quick_match.tests.test_multi_in import to_list


class MultiReTest(unittest.TestCase):

    def test_simplest(self):
        re_list = [b'1234', b'4567', b'7890']
        mre = MultiRE(re_list)

        result = to_list(mre.query(b'4567'))
        self.assertEqual(1, len(result))
        self.assertEqual(b'4567', result[0][1])

        result = to_list(mre.query(b'7890'))
        self.assertEqual(1, len(result))
        self.assertEqual(b'7890', result[0][1])

    def test_dup(self):
        re_list = [b'1234', b'4567']
        mre = MultiRE(re_list)

        result = to_list(mre.query(b'4567 4567'))
        print(result)
        self.assertEqual(1, len(result))

    def test_short(self):
        re_list = [rb'12.?34']
        mre = MultiRE(re_list)

        result = to_list(mre.query(b'12X34'))
        self.assertEqual(1, len(result))

    def test_re(self):
        re_list = [rb'1234.*56', rb'ab.*cdef']
        mre = MultiRE(re_list)
        result = to_list(mre.query(b'456'))
        self.assertEqual(0, len(result))
        self.assertEqual([], result)

        result = to_list(mre.query(b'1234a56'))
        self.assertEqual(1, len(result))
        self.assertEqual(rb'1234.*56', result[0][1])

        result = to_list(mre.query(b'abAAAcdef'))
        self.assertEqual(1, len(result))
        self.assertEqual(rb'ab.*cdef', result[0][1])

    def test_re_with_obj(self):
        re_list = [(rb'1234.*56', None), (rb'ab.*cdef', 1)]
        mre = MultiRE(re_list)

        result = to_list(mre.query(b'1234A56'))
        self.assertEqual(1, len(result))
        self.assertEqual(rb'1234.*56', result[0][1])
        self.assertEqual(None, result[0][3])

        result = to_list(mre.query(b'abAAAcdef'))
        self.assertEqual(1, len(result))
        self.assertEqual(rb'ab.*cdef', result[0][1])
        self.assertEqual(1, result[0][3])

    def test_re_flags(self):
        re_list = [rb'12.*3456', rb'ab.*cdef']
        mre = MultiRE(re_list, re.IGNORECASE)

        result = to_list(mre.query(b'AB3Cdef'))
        self.assertEqual(1, len(result))
        self.assertEqual(rb'ab.*cdef', result[0][1])

    def test_unicode_re(self):
        re_list = [r'ñandú', r'ýandex']
        mre = MultiREUnicode(re_list)

        result = to_list(mre.query('abcn'))
        self.assertEqual(0, len(result))
        self.assertEqual([], result)

        result = to_list(mre.query('123 ñandú 345'))
        print(result)
        self.assertEqual(1, len(result))
        self.assertEqual('ñandú', result[0][1])

    def test_unicode_query(self):
        re_list = ['abc321', 'def123']
        mre = MultiREUnicode(re_list)

        result = to_list(mre.query('abc321ñ'))
        print(result)
        self.assertEqual(1, len(result))
        self.assertEqual('abc321', result[0][1])

        result = to_list(mre.query('abc321\x00def123'))
        self.assertEqual(2, len(result))
        match_res = set(i[1] for i in result)
        self.assertEqual(set(re_list), match_res)

    def test_special_char(self):
        re_list = [b'\x01\x02\x03']
        mre = MultiRE(re_list)

        result = to_list(mre.query(b'abc\x00\x01\x02\x03def'))
        self.assertEqual(1, len(result))
        self.assertEqual(b'\x01\x02\x03', result[0][1])

