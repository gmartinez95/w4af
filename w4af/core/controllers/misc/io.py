"""
io.py

Copyright 2011 Andres Riancho

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
from io import StringIO, BytesIO, IOBase

from w4af.core.data.dc.utils.token import DataToken

class NamedStringIO(StringIO):
    """
    A unicode file-like string.
    """
    def __new__(cls, *args, **kwargs):
        return super(NamedStringIO, cls).__new__(cls, args[0])

    def __init__(self, the_str, name):
        super(NamedStringIO, self).__init__(the_str)
        self._name = name

    def __bytes__(self):
        return self.getvalue().encode('utf-8')

    # pylint: disable=E0202
    @property
    def name(self):
        return self._name

    def __getnewargs__(self):
        return (self.getvalue(), self.name)

class NamedBytesIO(BytesIO):
    """
    A binary file-like string.
    """
    def __new__(cls, *args, **kwargs):
        return super(NamedBytesIO, cls).__new__(cls, args[0])

    def __init__(self, the_bytes, name):
        super(NamedBytesIO, self).__init__(the_bytes)
        self._name = name

    def __deepcopy__(self, memo):
        return NamedBytesIO(self.getvalue(), self._name)

    # pylint: disable=E0202
    @property
    def name(self):
        return self._name

    def __getnewargs__(self):
        return (self.getvalue(), self.name)

def is_file_like(f):
    return isinstance(f, IOBase) or (isinstance(f, DataToken) and isinstance(f.get_value(), IOBase))
