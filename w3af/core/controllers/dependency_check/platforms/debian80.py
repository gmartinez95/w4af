"""
debian80.py

Copyright 2013 Andres Riancho

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
import distro

from .ubuntu1204 import Ubuntu1204


class Debian80(Ubuntu1204):
    SYSTEM_NAME = 'Debian 8.0'

    def is_current_platform(self):
        dist_name, dist_version, _ = distro.linux_distribution()
        return 'debian' == dist_name and '8.0' == dist_version
