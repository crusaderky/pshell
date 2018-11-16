import os
import pytest


DATADIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))


class StubError(Exception):
    """Phony exception used to test that the cleanup in context managers always
    happens
    """
    pass


unix_only = pytest.mark.skipif(os.name == 'nt', reason='Unix only')
windows_only = pytest.mark.skipif(os.name != 'nt', reason='Windows only')
