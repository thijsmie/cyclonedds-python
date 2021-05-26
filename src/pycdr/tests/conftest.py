import pytest

# Allow the import of support modules for tests
import os.path as p
import sys
sys.path.append(p.join(p.abspath(p.dirname(__file__)), "support_modules/"))

def pytest_configure(config):
    plugin = config.pluginmanager.getplugin('mypy')
    plugin.mypy_argv.append('--show-traceback')