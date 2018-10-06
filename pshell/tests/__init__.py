import os.path


DATADIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))


class StubError(Exception):
    """Phony exception used to test that the cleanup in context managers always
    happens
    """
    pass
