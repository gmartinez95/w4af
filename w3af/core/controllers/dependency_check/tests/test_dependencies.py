import unittest
import subprocess
import shlex
import sys
import os.path

from nose.plugins.attrib import attr

from w3af import ROOT_PATH

@attr('smoke')
class TestDependenciesInstalled(unittest.TestCase):

    def test_dependencies_installed(self):
        DEPS_CMD = "%s -c 'from w3af.core.controllers.dependency_check."\
                   "dependency_check import dependency_check; dependency_check(skip_external_commands=True)'"
        try:
            subprocess.check_output(shlex.split(DEPS_CMD % sys.executable),
                                    cwd=os.path.join(ROOT_PATH, ".."))
        except subprocess.CalledProcessError as cpe:
            self.assertEqual(False, True, cpe.output)
