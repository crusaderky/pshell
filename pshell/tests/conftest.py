from pathlib import Path

import pytest


@pytest.fixture(params=[str, Path])
def str_or_path(request):
    """Run a test that uses this fixture twice, with and without pathlib

    Usage::

        def test_open(str_or_path):
            sh.open(str_or_path("foo/bar/baz"))
    """
    return request.param
