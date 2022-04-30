"""
test_os_commanding.py

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
import pytest
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestOSCommanding(PluginTest):
    target_url = get_moth_http('/audit/os_commanding/')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('os_commanding'),),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        }
    }

    @pytest.mark.deprecated
    def test_found_osc(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('os_commanding', 'os_commanding')

        # Verify the specifics about the vulnerabilities
        EXPECTED = [
            ('trivial_osc.py', 'cmd'),
            ('param_osc.py', 'param'),
            ('blind_osc.py', 'cmd')
        ]

        self.assertAllVulnNamesEqual('OS commanding vulnerability', vulns)
        self.assertExpectedVulnsFound(EXPECTED, vulns)
