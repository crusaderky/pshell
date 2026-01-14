import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(params=[str, Path])
def str_or_path(request):
    """Run a test that uses this fixture twice, with and without pathlib

    Usage:

    >>> def test_open(str_or_path):
    ...     sh.open(str_or_path("foo/bar/baz"))
    """
    return request.param


@pytest.fixture(autouse=True)
def clear_names():
    """Clear any environment variables created with get_name()"""
    yield
    for key in list(os.environ.keys()):
        if key.startswith("pshell_tests"):
            del os.environ[key]


if "pytest_run_parallel" not in sys.modules:

    @pytest.fixture
    def thread_index():
        return 0
