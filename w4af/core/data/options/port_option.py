"""
port_option.py

Copyright 2008 Andres Riancho

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
from w4af.core.controllers.exceptions import BaseFrameworkException
from w4af.core.data.options.baseoption import BaseOption
from w4af.core.data.options.option_types import PORT


class PortOption(BaseOption):

    _type = PORT

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends 'True' or 'a,b,c'

        Based on the value parameter and the option type, I have to create a nice
        looking object like True or ['a','b','c'].
        """
        self._value = self.validate(value)

    def validate(self, value):
        try:
            port = int(value)
            assert port > 0
            assert port < 65536
        except:
            msg = 'Invalid port specified, it needs to be a number between'\
                  ' 1 and 65535.'
            raise BaseFrameworkException(msg)
        else:
            return port
